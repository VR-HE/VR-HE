// VR-HE interactive browser demo: provisional local record store.
//
// PROVISIONAL PROTOTYPE CODE. This is not the VR-HE backend, the two-way spreadsheet adapter or
// a sync engine. It keeps user-edited descriptions for the synthetic demo site in one versioned
// JSON document in browser storage, so a tester can save, reload, relaunch and export.
//
// Storage contract (key StorageKeyFor(siteId), document schema "vrhe.demo.local-records" v1):
//   { "schema": "...", "schemaVersion": 1, "siteId": "...", "notice": "...", "updatedAt": "...",
//     "entries": [ { "recordId": "rec-...", "description": "...", "revision": 3,
//                    "updatedAt": "2026-11-10T14:03:12Z" } ] }
// Only edited records are stored. Seed text from the site file is revision 0; each save that
// changes the text adds 1. Entries are matched by recordId only, never by display name, anchor
// or splat index, so renaming a rack or moving its anchor keeps its saved description.
//
// Rules that protect saved data:
//   * Every open and save re-reads storage first, so a second tab's save is seen.
//   * A save names the revision it started from; if storage moved on, the save is refused
//     (Conflict) and nothing is written. This is optimistic concurrency, not a lock: two tabs
//     saving in the same instant can still race. Acceptable for a single-user local demo.
//   * Entries for records this build does not know are kept untouched.
//   * A document from a newer schema version is never rewritten (read-only mode).
//   * A document that cannot be parsed is copied to a backup key before the first write;
//     if that copy fails, the store stays read-only rather than overwrite it.
// Extension point: a production adapter needs server identity, field-level history, the
// draft-then-designated-editor-approval policy for AI-generated live writes, and spreadsheet
// mapping. None of that is implemented here.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;
using UnityEngine;

namespace VRHE.InteractiveDemo.Records
{
    public enum SaveStatus
    {
        Saved,
        NoChange,
        Conflict,
        ReadOnly,
        UnknownRecord,
        Invalid,
        StorageError
    }

    [Serializable]
    public sealed class StoredRecordEntry
    {
        public string recordId;
        public string description;
        public int revision;
        public string updatedAt;

        public StoredRecordEntry Clone() => new()
            { recordId = recordId, description = description, revision = revision, updatedAt = updatedAt };
    }

    [Serializable]
    public sealed class LocalRecordsDocument
    {
        public string schema;
        public int schemaVersion;
        public string siteId;
        public string notice;
        public string updatedAt;
        public List<StoredRecordEntry> entries = new();
    }

    /// <summary>What the user sees for one record: seed fields plus the saved description.</summary>
    [Serializable]
    public sealed class DemoRecordView
    {
        public string recordId;
        public string kind;
        public string name;
        public string location;
        public string[] anchorIds;
        public string description;
        public int revision;      // 0 = original demo text
        public string updatedAt;  // empty for original demo text
        public string source;     // "seed" or "local edit"
    }

    public sealed class SaveResult
    {
        public SaveStatus Status;
        public string Message;
        public DemoRecordView Record;  // current view after the attempt (null for unknown records)
    }

    [Serializable]
    public sealed class DemoRecordsExport
    {
        public string schema = "vrhe.demo.records-export";
        public int schemaVersion = 1;
        public string notice;
        public string exportedAt;
        public string siteId;
        public string siteName;
        public string storageKey;
        public string storageDescription;
        public string origin;
        public string build;
        public bool readOnly;
        public string storeStatus;
        public List<DemoRecordView> records = new();
        public List<StoredRecordEntry> unmatchedStoredEntries = new();
    }

    public sealed class DemoRecordStore
    {
        public const string DocumentSchema = "vrhe.demo.local-records";
        public const int DocumentSchemaVersion = 1;
        public const int MaxDescriptionLength = 4000;
        public const string SourceSeed = "seed";
        public const string SourceLocalEdit = "local edit";

        public const string Notice =
            "LOCAL DEMO DATA: synthetic records saved only in this browser profile on this computer. " +
            "Not a backend, spreadsheet or production record.";

        readonly DemoSiteDefinition m_site;
        readonly IKeyValueStorage m_storage;
        readonly Func<DateTime> m_utcNow;
        readonly Dictionary<string, DemoRecordSeed> m_seeds = new();
        readonly Dictionary<string, List<string>> m_anchorsByRecord = new();
        readonly List<string> m_recordOrder = new();

        LocalRecordsDocument m_document;  // last successfully read document (never null)
        string m_unreadableRaw;           // raw text when storage held something we cannot parse

        public DemoRecordStore(DemoSiteDefinition site, IKeyValueStorage storage, Func<DateTime> utcNow = null)
        {
            m_site = site ?? throw new ArgumentNullException(nameof(site));
            m_storage = storage ?? throw new ArgumentNullException(nameof(storage));
            m_utcNow = utcNow ?? (() => DateTime.UtcNow);
            foreach (var seed in site.records ?? Array.Empty<DemoRecordSeed>())
            {
                if (seed?.recordId == null || m_seeds.ContainsKey(seed.recordId))
                    continue;
                m_seeds.Add(seed.recordId, seed);
                m_recordOrder.Add(seed.recordId);
                m_anchorsByRecord[seed.recordId] = new List<string>();
            }
            foreach (var anchor in site.anchors ?? Array.Empty<DemoAnchorDefinition>())
                if (anchor?.recordId != null && m_anchorsByRecord.TryGetValue(anchor.recordId, out var list))
                    list.Add(anchor.anchorId);
            StorageKey = StorageKeyFor(site.siteId);
            m_document = NewDocument();
            Reload();
        }

        public static string StorageKeyFor(string siteId) => "vrhe.demo.records.v1." + siteId;

        public string StorageKey { get; }
        public string StorageDescription => m_storage.Description;
        public bool IsReadOnly { get; private set; }

        /// <summary>Plain-language state of the stored data after the last read.</summary>
        public string StatusMessage { get; private set; }

        public IReadOnlyList<string> RecordIds => m_recordOrder;

        /// <summary>Re-reads storage. Returns false when storage could not be read.</summary>
        public bool Reload()
        {
            if (!m_storage.TryRead(StorageKey, out var raw, out var error))
            {
                // Keep showing what was last read; refuse writes until a read works again.
                IsReadOnly = true;
                StatusMessage = $"Browser storage could not be read ({error}). Saving is disabled.";
                return false;
            }
            IsReadOnly = false;
            m_unreadableRaw = null;
            if (raw == null)
            {
                m_document = NewDocument();
                StatusMessage = "No saved edits yet in this browser profile; showing the original demo text.";
                return true;
            }

            LocalRecordsDocument parsed = null;
            try
            {
                parsed = JsonUtility.FromJson<LocalRecordsDocument>(raw);
            }
            catch (Exception)
            {
                // malformed JSON (JsonUtility throws ArgumentException): handled below as unreadable
            }

            if (parsed == null || parsed.schema != DocumentSchema || parsed.schemaVersion < 1 ||
                (parsed.siteId != null && parsed.siteId != m_site.siteId))
            {
                m_unreadableRaw = raw;
                m_document = NewDocument();
                StatusMessage = "Saved data in this browser could not be read; showing the original demo text. " +
                                "The first save keeps a backup copy of the unreadable data.";
                return true;
            }
            if (parsed.schemaVersion > DocumentSchemaVersion)
            {
                IsReadOnly = true;
                m_document = NewDocument();
                StatusMessage = $"Saved data was written by a newer demo version (schema {parsed.schemaVersion}). " +
                                "This page shows the original demo text and will not change that data.";
                return true;
            }

            parsed.entries ??= new List<StoredRecordEntry>();
            parsed.entries.RemoveAll(e => e == null || string.IsNullOrEmpty(e.recordId));
            m_document = parsed;
            var edited = 0;
            foreach (var entry in parsed.entries)
                if (m_seeds.ContainsKey(entry.recordId))
                    edited++;
            StatusMessage = edited == 0
                ? "No saved edits yet in this browser profile; showing the original demo text."
                : $"{edited} edited record(s) loaded from this browser profile.";
            return true;
        }

        public DemoRecordView Get(string recordId)
        {
            if (recordId == null || !m_seeds.TryGetValue(recordId, out var seed))
                return null;
            var entry = FindEntry(m_document, recordId);
            return new DemoRecordView
            {
                recordId = seed.recordId,
                kind = seed.kind ?? "",
                name = seed.name ?? "",
                location = seed.location ?? "",
                anchorIds = m_anchorsByRecord[recordId].ToArray(),
                description = entry != null ? entry.description ?? "" : seed.description ?? "",
                revision = entry?.revision ?? 0,
                updatedAt = entry?.updatedAt ?? "",
                source = entry != null ? SourceLocalEdit : SourceSeed
            };
        }

        public List<DemoRecordView> All()
        {
            var list = new List<DemoRecordView>(m_recordOrder.Count);
            foreach (var id in m_recordOrder)
                list.Add(Get(id));
            return list;
        }

        /// <summary>
        /// Saves a new description for one record. baseRevision is the revision the editor
        /// opened; a mismatch with storage is a Conflict and writes nothing.
        /// </summary>
        public SaveResult Save(string recordId, string description, int baseRevision)
        {
            if (recordId == null || !m_seeds.ContainsKey(recordId))
                return new SaveResult { Status = SaveStatus.UnknownRecord, Message = "That record is not part of this demo site." };

            var clean = Sanitize(description, out var tooLong);
            if (tooLong)
                return Result(SaveStatus.Invalid, recordId,
                    $"The description is longer than {MaxDescriptionLength} characters; nothing was saved.");

            Reload();  // see edits made in another tab since this one opened the record
            if (IsReadOnly)
                return Result(SaveStatus.ReadOnly, recordId, StatusMessage);

            var current = Get(recordId);
            if (current.revision != baseRevision)
                return Result(SaveStatus.Conflict, recordId,
                    $"This record changed after you opened it (now revision {current.revision}, you opened revision " +
                    $"{baseRevision}). Nothing was saved. Copy your text, reopen the record and save again.");
            if (current.description == clean)
                return Result(SaveStatus.NoChange, recordId, "No changes to save.");

            if (m_unreadableRaw != null)
            {
                var backupKey = StorageKey + ".unreadable-" + m_utcNow().ToString("yyyyMMdd'T'HHmmss'Z'", CultureInfo.InvariantCulture);
                if (!m_storage.TryWrite(backupKey, m_unreadableRaw, out var backupError))
                {
                    IsReadOnly = true;
                    StatusMessage = $"Could not back up unreadable saved data ({backupError}); saving is disabled so it is not overwritten.";
                    return Result(SaveStatus.StorageError, recordId, StatusMessage);
                }
            }

            var now = Timestamp(m_utcNow());
            var next = Copy(m_document);
            var entry = FindEntry(next, recordId);
            if (entry == null)
            {
                entry = new StoredRecordEntry { recordId = recordId };
                next.entries.Add(entry);
            }
            entry.description = clean;
            entry.revision = current.revision + 1;
            entry.updatedAt = now;
            next.updatedAt = now;
            next.notice = Notice;
            next.schema = DocumentSchema;
            next.schemaVersion = DocumentSchemaVersion;
            next.siteId = m_site.siteId;

            if (!m_storage.TryWrite(StorageKey, JsonUtility.ToJson(next), out var error))
                return Result(SaveStatus.StorageError, recordId,
                    $"The browser refused to save ({error}). Nothing was saved; your text is still in the editor.");

            m_document = next;
            m_unreadableRaw = null;
            StatusMessage = "Saved in this browser profile.";
            return Result(SaveStatus.Saved, recordId, $"Saved in this browser profile (revision {entry.revision}).");
        }

        /// <summary>Removes this site's saved edits only. Backups and other keys are kept.</summary>
        public bool Clear(out string error)
        {
            if (!m_storage.TryRemove(StorageKey, out error))
                return false;
            m_document = NewDocument();
            m_unreadableRaw = null;
            IsReadOnly = false;
            StatusMessage = "Saved demo edits were removed from this browser profile; showing the original demo text.";
            return true;
        }

        public DemoRecordsExport BuildExport(string origin, string build)
        {
            var export = new DemoRecordsExport
            {
                notice = Notice,
                exportedAt = Timestamp(m_utcNow()),
                siteId = m_site.siteId,
                siteName = m_site.siteName,
                storageKey = StorageKey,
                storageDescription = StorageDescription,
                origin = origin ?? "",
                build = build ?? "",
                readOnly = IsReadOnly,
                storeStatus = StatusMessage,
                records = All()
            };
            foreach (var entry in m_document.entries)
                if (!m_seeds.ContainsKey(entry.recordId))
                    export.unmatchedStoredEntries.Add(entry.Clone());
            return export;
        }

        public string ExportJson(string origin, string build) => JsonUtility.ToJson(BuildExport(origin, build), true);

        /// <summary>
        /// Normalizes line endings to \n, removes control characters other than tab and newline,
        /// and replaces unpaired surrogates. tooLong reports text over MaxDescriptionLength.
        /// </summary>
        public static string Sanitize(string text, out bool tooLong)
        {
            text ??= "";
            var sb = new StringBuilder(text.Length);
            for (var i = 0; i < text.Length; i++)
            {
                var c = text[i];
                if (c == '\r')
                {
                    sb.Append('\n');
                    if (i + 1 < text.Length && text[i + 1] == '\n')
                        i++;
                }
                else if (c == '\n' || c == '\t')
                    sb.Append(c);
                else if (char.IsControl(c))
                {
                    // dropped
                }
                else if (char.IsHighSurrogate(c))
                {
                    if (i + 1 < text.Length && char.IsLowSurrogate(text[i + 1]))
                    {
                        sb.Append(c).Append(text[i + 1]);
                        i++;
                    }
                    else
                        sb.Append('�');
                }
                else if (char.IsLowSurrogate(c))
                    sb.Append('�');
                else
                    sb.Append(c);
            }
            tooLong = sb.Length > MaxDescriptionLength;
            return sb.ToString();
        }

        public static string Timestamp(DateTime utc) =>
            utc.ToUniversalTime().ToString("yyyy-MM-dd'T'HH:mm:ss'Z'", CultureInfo.InvariantCulture);

        SaveResult Result(SaveStatus status, string recordId, string message) =>
            new() { Status = status, Message = message, Record = Get(recordId) };

        LocalRecordsDocument NewDocument() => new()
        {
            schema = DocumentSchema,
            schemaVersion = DocumentSchemaVersion,
            siteId = m_site.siteId,
            notice = Notice,
            updatedAt = "",
            entries = new List<StoredRecordEntry>()
        };

        static LocalRecordsDocument Copy(LocalRecordsDocument source)
        {
            var copy = new LocalRecordsDocument
            {
                schema = source.schema,
                schemaVersion = source.schemaVersion,
                siteId = source.siteId,
                notice = source.notice,
                updatedAt = source.updatedAt,
                entries = new List<StoredRecordEntry>(source.entries.Count)
            };
            foreach (var entry in source.entries)
                copy.entries.Add(entry.Clone());
            return copy;
        }

        static StoredRecordEntry FindEntry(LocalRecordsDocument document, string recordId)
        {
            foreach (var entry in document.entries)
                if (entry.recordId == recordId)
                    return entry;
            return null;
        }
    }
}
