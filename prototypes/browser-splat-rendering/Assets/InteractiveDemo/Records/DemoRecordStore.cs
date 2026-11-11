// VR-HE interactive browser demo: provisional local record store, format version 2.
//
// PROVISIONAL PROTOTYPE CODE. This is not the VR-HE backend, the two-way spreadsheet adapter or
// a sync engine. It keeps the demo's rack notes, equipment records, their descriptions and the
// shared list of description names in one versioned JSON document in browser storage, so a
// tester can author, reload, relaunch and export. Data shapes: DemoRecordModel.cs.
//
// Storage contract
//   Key StorageKeyFor(siteId) = "vrhe.demo.records.v2.<siteId>", schema "vrhe.demo.local-records" v2:
//     { schema, schemaVersion: 2, siteId, notice, updatedAt, migration{...},
//       rackNotes:[{recordId, description, revision, updatedAt}],
//       labels:[{labelId, name, revision, createdAt, updatedAt, retired, retiredAt, replacedByLabelId,
//                previousNames[], reassignedDescriptionIds[]}],
//       equipment:[{equipmentId, rackRecordId, name, ruStart, ruEnd, revision, createdAt, updatedAt,
//                   descriptions:[{descriptionId, labelId, text, createdAt, updatedAt}]}] }
//   Rack notes keep the version 1 meaning: only edited notes are stored, seed text is revision 0.
//   Equipment and names are stored in full once the document exists; until then the starter
//   names come from the site file and there is no equipment. Opening never writes.
//
// Migration from the delivered first demo (version 1, key "vrhe.demo.records.v1.<siteId>")
//   The version 1 key is only ever read. When no version 2 document exists, its rack notes are
//   shown as rack notes (same record IDs, text, revisions and dates, unknown records included)
//   and written into the new document at the first save. The version 1 document stays
//   unchanged as a recovery copy, so the earlier build still finds its data. Rack notes are
//   never turned into equipment descriptions. Unreadable earlier data is left alone and
//   included raw in exports, as are backups under the same key prefix.
//
// Rules that protect saved data
//   * Every command re-reads storage first, so another tab's save is seen.
//   * Changes name the revision they started from (rack note, equipment item or name); if
//     storage moved on, the change is refused (Conflict) and nothing is written. Optimistic
//     concurrency, not a lock: acceptable for a single-user local demo.
//   * Each command builds the complete next document in memory, checks it, then writes it with
//     ONE storage write. If the browser refuses that write, nothing changes; there is no
//     half-applied state to recover from. In-memory state is replaced only after the write.
//   * Unknown records, unknown equipment and unknown name references are kept, not dropped.
//   * A document from a newer schema version is never rewritten (read-only mode).
//   * An unreadable version 2 document is copied to a backup key before the first write.
//
// Description names (D039, D041)
//   A description refers to a name by labelId, so a Rename (spelling fix) reaches every
//   description without touching any text. A name can only leave the list through Replace,
//   which needs a valid replacement (an existing name or a new one); there is no command that
//   removes a name without one. Replace moves every description that used the old name to the
//   replacement in the same single write, keeps every description's ID, text and equipment,
//   records the moved IDs on the retired name, and checks those invariants before writing.
//   When an item already has a description with the replacement name, both are kept
//   (authoring.labelCollision "keep-both", the default) or the replacement is refused
//   ("block"). Removing an empty description is allowed; removing text is not offered.
//
// Extension point: a production adapter needs server identity, field-level history, the
// draft-then-designated-editor-approval policy for AI-generated live writes, designated-editor
// roles, and an explicit spreadsheet mapping keyed by these IDs. None of that is implemented.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;
using UnityEngine;

namespace VRHE.InteractiveDemo.Records
{
    public sealed class DemoRecordStore
    {
        public const string DocumentSchema = "vrhe.demo.local-records";
        public const int DocumentSchemaVersion = 2;
        public const int LegacySchemaVersion = 1;
        public const int MaxDescriptionLength = 4000;
        public const int MaxStoredCopyCharacters = 1_000_000;
        public const string SourceSeed = "seed";
        public const string SourceLocalEdit = "local edit";
        public const string KeyPrefix = "vrhe.demo.records.";

        public const string MigrationNone = "no earlier data";
        public const string MigrationCarried = "carried over";
        public const string MigrationLegacyUnreadable = "earlier data unreadable, kept unchanged";
        public const string MigrationLegacyUnsupported = "earlier data in an unexpected version, kept unchanged";
        public const string MigrationReset = "reset";

        public const string Notice =
            "LOCAL DEMO DATA: synthetic records saved only in this browser profile on this computer. " +
            "Not a backend, spreadsheet or production record.";

        public const string MappingNotice =
            "No spreadsheet or Google Drive mapping exists in this demo. Renaming or replacing a description " +
            "name changes only this local list and its references; it never renames, clears or deletes a " +
            "spreadsheet column or value.";

        readonly DemoSiteDefinition m_site;
        readonly DemoAuthoringSettings m_rules;
        readonly IKeyValueStorage m_storage;
        readonly Func<DateTime> m_utcNow;
        readonly Func<string> m_newGuid;
        readonly Dictionary<string, DemoRecordSeed> m_seeds = new();
        readonly Dictionary<string, List<string>> m_anchorsByRecord = new();
        readonly List<string> m_recordOrder = new();

        LocalRecordsDocument m_document;   // effective state; never null
        bool m_persisted;                  // the version 2 key holds m_document
        string m_unreadableRaw;            // version 2 text we could not read (backed up before the first write)
        LegacyRecordsDocumentV1 m_legacy;  // the readable version 1 document, if any (never written)
        bool m_legacyPresent;              // the version 1 key exists (readable or not)

        public DemoRecordStore(DemoSiteDefinition site, IKeyValueStorage storage, Func<DateTime> utcNow = null,
            Func<string> newGuid = null)
        {
            m_site = site ?? throw new ArgumentNullException(nameof(site));
            m_storage = storage ?? throw new ArgumentNullException(nameof(storage));
            m_rules = site.Authoring;
            m_utcNow = utcNow ?? (() => DateTime.UtcNow);
            m_newGuid = newGuid ?? (() => Guid.NewGuid().ToString("D"));
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
            LegacyStorageKey = LegacyStorageKeyFor(site.siteId);
            m_document = SeedDocument(MigrationNone);
            Reload();
        }

        public static string StorageKeyFor(string siteId) => KeyPrefix + "v2." + siteId;
        public static string LegacyStorageKeyFor(string siteId) => KeyPrefix + "v1." + siteId;

        public string StorageKey { get; }
        public string LegacyStorageKey { get; }
        public string StorageDescription => m_storage.Description;
        public DemoAuthoringSettings Rules => m_rules;
        public bool IsReadOnly { get; private set; }

        /// <summary>Plain-language state of the stored data after the last read or write.</summary>
        public string StatusMessage { get; private set; }

        /// <summary>True once the version 2 document exists in storage.</summary>
        public bool IsPersisted => m_persisted;

        public StoredMigration Migration => Clone(m_document.migration);
        public IReadOnlyList<string> RecordIds => m_recordOrder;

        // ============================================================== loading and migration

        /// <summary>Re-reads storage. Returns false when storage could not be read.</summary>
        public bool Reload()
        {
            if (!m_storage.TryRead(StorageKey, out var raw, out var error) ||
                !m_storage.TryRead(LegacyStorageKey, out var legacyRaw, out error))
            {
                // Keep showing what was last read; refuse writes until a read works again.
                IsReadOnly = true;
                StatusMessage = $"Browser storage could not be read ({error}). Saving is disabled.";
                return false;
            }
            IsReadOnly = false;
            m_unreadableRaw = null;
            m_legacyPresent = legacyRaw != null;
            m_legacy = ParseLegacy(legacyRaw, out var legacyState);

            if (raw == null)
            {
                m_persisted = false;
                m_document = FromLegacy(legacyState, legacyRaw != null);
                StatusMessage = DescribeUnwritten(legacyState);
                return true;
            }

            var header = ParseHeader(raw);
            if (header != null && header.schemaVersion > DocumentSchemaVersion)
            {
                IsReadOnly = true;
                m_persisted = true;
                m_document = SeedDocument(MigrationNone);
                StatusMessage = $"Saved data was written by a newer demo version (schema {header.schemaVersion}). " +
                                "This page shows the original demo content and will not change that data.";
                return true;
            }
            var parsed = header != null && header.schemaVersion == DocumentSchemaVersion ? ParseDocument(raw) : null;
            if (parsed == null)
            {
                m_unreadableRaw = raw;
                m_persisted = false;
                m_document = FromLegacy(legacyState, legacyRaw != null);
                StatusMessage = "Saved data in this browser could not be read; showing the original demo content. " +
                                "The first save keeps a backup copy of the unreadable data.";
                return true;
            }
            m_document = parsed;
            m_persisted = true;
            StatusMessage = DescribeLoaded(legacyRaw != null);
            return true;
        }

        DocumentHeader ParseHeader(string raw)
        {
            try
            {
                var header = JsonUtility.FromJson<DocumentHeader>(raw);
                if (header == null || header.schema != DocumentSchema || (header.siteId != null && header.siteId != m_site.siteId))
                    return null;
                return header;
            }
            catch (Exception)
            {
                return null;  // malformed JSON (JsonUtility throws ArgumentException)
            }
        }

        LocalRecordsDocument ParseDocument(string raw)
        {
            try
            {
                var parsed = JsonUtility.FromJson<LocalRecordsDocument>(raw);
                if (parsed == null)
                    return null;
                Normalize(parsed);
                return parsed;
            }
            catch (Exception)
            {
                return null;
            }
        }

        LegacyRecordsDocumentV1 ParseLegacy(string raw, out string state)
        {
            state = MigrationNone;
            if (raw == null)
                return null;
            var header = ParseHeader(raw);
            if (header == null)
            {
                state = MigrationLegacyUnreadable;
                return null;
            }
            if (header.schemaVersion != LegacySchemaVersion)
            {
                state = MigrationLegacyUnsupported;
                return null;
            }
            try
            {
                var legacy = JsonUtility.FromJson<LegacyRecordsDocumentV1>(raw);
                legacy.entries ??= new List<StoredRecordEntry>();
                legacy.entries.RemoveAll(e => e == null || string.IsNullOrEmpty(e.recordId));
                state = MigrationCarried;
                return legacy;
            }
            catch (Exception)
            {
                state = MigrationLegacyUnreadable;
                return null;
            }
        }

        /// <summary>The starting document when no readable version 2 document exists.</summary>
        LocalRecordsDocument FromLegacy(string legacyState, bool legacyPresent)
        {
            var document = SeedDocument(legacyState);
            if (legacyPresent)
            {
                document.migration.fromKey = LegacyStorageKey;
                document.migration.fromSchemaVersion = LegacySchemaVersion;
            }
            if (m_legacy != null)
            {
                document.migration.sourceUpdatedAt = m_legacy.updatedAt ?? "";
                document.migration.sourceEntries = m_legacy.entries.Count;
                foreach (var entry in m_legacy.entries)
                    document.rackNotes.Add(entry.Clone());  // same IDs, text, revisions and dates
                document.migration.carriedEntries = document.rackNotes.Count;
            }
            return document;
        }

        LocalRecordsDocument SeedDocument(string migrationState)
        {
            var document = new LocalRecordsDocument
            {
                schema = DocumentSchema,
                schemaVersion = DocumentSchemaVersion,
                siteId = m_site.siteId,
                notice = Notice,
                updatedAt = "",
                migration = new StoredMigration { state = migrationState }
            };
            foreach (var seed in m_site.labels ?? Array.Empty<DemoLabelSeed>())
            {
                var name = CleanName(seed?.name, m_rules.maxLabelNameLength, out var problem);
                if (seed?.labelId == null || problem != null || document.labels.Any(l => l.labelId == seed.labelId))
                    continue;  // the validator reports these; never let a bad seed stop the store
                document.labels.Add(new StoredLabel { labelId = seed.labelId, name = name, revision = 1, createdAt = "", updatedAt = "" });
            }
            return document;
        }

        static void Normalize(LocalRecordsDocument document)
        {
            document.migration ??= new StoredMigration();
            document.rackNotes ??= new List<StoredRecordEntry>();
            document.rackNotes.RemoveAll(e => e == null || string.IsNullOrEmpty(e.recordId));
            document.labels ??= new List<StoredLabel>();
            document.equipment ??= new List<StoredEquipment>();
            foreach (var label in document.labels)
            {
                if (label == null)
                    continue;
                label.name ??= "";
                label.previousNames ??= new List<string>();
                label.reassignedDescriptionIds ??= new List<string>();
            }
            foreach (var item in document.equipment)
            {
                if (item == null)
                    continue;
                item.descriptions ??= new List<StoredDescription>();
                foreach (var d in item.descriptions)
                    if (d != null)
                    {
                        d.labelId ??= "";
                        d.text ??= "";
                    }
            }
        }

        string DescribeUnwritten(string legacyState)
        {
            switch (legacyState)
            {
                case MigrationCarried when m_document.rackNotes.Count > 0:
                    return $"{m_document.rackNotes.Count} rack note(s) saved with the earlier demo version are shown. " +
                           "The earlier saved copy stays unchanged as a backup; the new format is written at your first save.";
                case MigrationLegacyUnreadable:
                    return "Saved data from the earlier demo version could not be read. It is kept unchanged and included in " +
                           "JSON exports; showing the original demo content.";
                case MigrationLegacyUnsupported:
                    return "Saved data under the earlier demo version's key has an unexpected format. It is kept unchanged " +
                           "and included in JSON exports; showing the original demo content.";
                default:
                    return "No saved edits yet in this browser profile; showing the original demo content.";
            }
        }

        string DescribeLoaded(bool legacyPresent)
        {
            var notes = m_document.rackNotes.Count(e => m_seeds.ContainsKey(e.recordId));
            var items = m_document.equipment.Count(e => e != null);
            var names = m_document.labels.Count(l => l != null && !l.retired);
            var text = notes == 0 && items == 0
                ? $"No rack notes edited and no equipment recorded yet in this browser profile; {names} description names."
                : $"{notes} edited rack note(s), {items} equipment record(s) and {names} description names loaded from this browser profile.";
            if (!legacyPresent)
                return text;
            var migration = m_document.migration;
            if (m_legacy == null)
                text += " Saved data from the earlier demo version could not be read; it is kept unchanged and included in JSON exports.";
            else if (migration.state == MigrationReset)
                text += " The earlier demo version's saved copy is kept unchanged and included in JSON exports.";
            else if (migration.state != MigrationCarried)
                text += " The earlier demo version saved rack notes after this format was started; that copy is kept " +
                        "unchanged and included in JSON exports, but not shown here.";
            else if ((m_legacy.updatedAt ?? "") != migration.sourceUpdatedAt)
                text += " The earlier demo version changed its own saved copy after the carry-over; that copy is kept " +
                        "unchanged and included in JSON exports, but its later changes are not shown here.";
            return text;
        }

        // ============================================================== views

        public DemoRecordView Get(string recordId)
        {
            if (recordId == null || !m_seeds.TryGetValue(recordId, out var seed))
                return null;
            var entry = FindNote(m_document, recordId);
            var view = new DemoRecordView
            {
                recordId = seed.recordId,
                kind = seed.kind ?? "",
                name = seed.name ?? "",
                location = seed.location ?? "",
                anchorIds = m_anchorsByRecord[recordId].ToArray(),
                description = entry != null ? entry.description ?? "" : seed.description ?? "",
                revision = entry?.revision ?? 0,
                updatedAt = entry?.updatedAt ?? "",
                source = entry != null ? SourceLocalEdit : SourceSeed,
                rackUnits = RackUnits(recordId),
                ruNumbering = m_rules.ruNumbering
            };
            foreach (var item in TopFirst(m_document, recordId))
                view.equipment.Add(new EquipmentSummary
                {
                    equipmentId = item.equipmentId,
                    name = item.name ?? "",
                    ruStart = item.ruStart,
                    ruEnd = item.ruEnd,
                    revision = item.revision,
                    descriptions = item.descriptions.Count,
                    named = item.descriptions.Count(d => d != null && !string.IsNullOrEmpty(d.labelId)),
                    overlaps = OverlapText(Overlapping(m_document, recordId, item.equipmentId, item.ruStart, item.ruEnd))
                });
            return view;
        }

        public List<DemoRecordView> All()
        {
            var list = new List<DemoRecordView>(m_recordOrder.Count);
            foreach (var id in m_recordOrder)
                list.Add(Get(id));
            return list;
        }

        /// <summary>The equipment item with its descriptions, or null when it is unknown here.</summary>
        public EquipmentView GetEquipment(string equipmentId)
        {
            var item = FindItem(m_document, equipmentId);
            if (item == null || !m_seeds.TryGetValue(item.rackRecordId ?? "", out var rack))
                return null;
            var view = new EquipmentView
            {
                equipmentId = item.equipmentId,
                rackRecordId = item.rackRecordId,
                rackName = rack.name ?? "",
                name = item.name ?? "",
                ruStart = item.ruStart,
                ruEnd = item.ruEnd,
                rackUnits = RackUnits(item.rackRecordId),
                ruNumbering = m_rules.ruNumbering,
                revision = item.revision,
                createdAt = item.createdAt ?? "",
                updatedAt = item.updatedAt ?? "",
                overlaps = OverlapText(Overlapping(m_document, item.rackRecordId, item.equipmentId, item.ruStart, item.ruEnd))
            };
            foreach (var d in item.descriptions)
            {
                if (d == null)
                    continue;
                var label = FindLabel(m_document, d.labelId);
                view.descriptions.Add(new DescriptionView
                {
                    descriptionId = d.descriptionId ?? "",
                    labelId = d.labelId ?? "",
                    labelName = label?.name ?? "",
                    labelState = string.IsNullOrEmpty(d.labelId) ? "none" : label == null ? "unknown" : label.retired ? "retired" : "active",
                    text = d.text ?? "",
                    createdAt = d.createdAt ?? "",
                    updatedAt = d.updatedAt ?? ""
                });
            }
            return view;
        }

        /// <summary>Every description name with its current use; active names A-Z, then retired names.</summary>
        public CatalogView Catalog()
        {
            var catalog = new CatalogView();
            var uses = new Dictionary<string, int>();
            var items = new Dictionary<string, HashSet<string>>();
            foreach (var item in m_document.equipment)
            {
                if (item == null)
                    continue;
                foreach (var d in item.descriptions)
                {
                    if (d == null || string.IsNullOrEmpty(d.labelId))
                        continue;
                    uses[d.labelId] = uses.TryGetValue(d.labelId, out var n) ? n + 1 : 1;
                    if (!items.TryGetValue(d.labelId, out var set))
                        items[d.labelId] = set = new HashSet<string>();
                    set.Add(item.equipmentId);
                }
            }
            foreach (var label in m_document.labels
                         .Where(l => l != null)
                         .OrderBy(l => l.retired)
                         .ThenBy(l => l.name ?? "", StringComparer.OrdinalIgnoreCase))
            {
                var replacement = FindLabel(m_document, label.replacedByLabelId);
                catalog.labels.Add(new LabelView
                {
                    labelId = label.labelId ?? "",
                    name = label.name ?? "",
                    revision = label.revision,
                    retired = label.retired,
                    retiredAt = label.retiredAt ?? "",
                    replacedByLabelId = label.replacedByLabelId ?? "",
                    replacedByName = replacement?.name ?? "",
                    previousNames = string.Join("; ", label.previousNames),
                    uses = uses.TryGetValue(label.labelId ?? "", out var n) ? n : 0,
                    items = items.TryGetValue(label.labelId ?? "", out var set) ? set.Count : 0,
                    reassigned = label.reassignedDescriptionIds.Count
                });
                if (!label.retired)
                    catalog.active++;
            }
            return catalog;
        }

        // ============================================================== rack notes

        /// <summary>
        /// Saves a new rack note for one rack. baseRevision is the revision the editor opened; a
        /// mismatch with storage is a Conflict and writes nothing.
        /// </summary>
        public SaveResult Save(string recordId, string description, int baseRevision)
        {
            if (recordId == null || !m_seeds.ContainsKey(recordId))
                return new SaveResult { Status = SaveStatus.UnknownRecord, Message = "That record is not part of this demo site." };

            var clean = Sanitize(description, out var tooLong);
            if (tooLong)
                return Result(SaveStatus.Invalid, recordId,
                    $"The note is longer than {MaxDescriptionLength} characters; nothing was saved.");

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

            var now = Timestamp(m_utcNow());
            var next = Copy(m_document);
            var entry = FindNote(next, recordId);
            if (entry == null)
            {
                entry = new StoredRecordEntry { recordId = recordId };
                next.rackNotes.Add(entry);
            }
            entry.description = clean;
            entry.revision = current.revision + 1;
            entry.updatedAt = now;

            if (!Commit(next, out var error))
                return Result(SaveStatus.StorageError, recordId,
                    $"The browser refused to save ({error}). Nothing was saved; your text is still in the editor.");
            return Result(SaveStatus.Saved, recordId, $"Saved in this browser profile (revision {entry.revision}).");
        }

        // ============================================================== equipment

        /// <summary>
        /// Adds an equipment record to a rack. It always starts with exactly one empty, unnamed
        /// description (D038). A multi-RU item is one record with ruStart..ruEnd.
        /// </summary>
        public AuthoringResult CreateEquipment(string rackRecordId, string name, int ruStart, int ruEnd)
        {
            if (rackRecordId == null || !m_seeds.ContainsKey(rackRecordId))
                return Refused(SaveStatus.UnknownRecord, "That rack is not part of this demo site. Nothing was saved.");
            var cleanName = CleanName(name, m_rules.maxEquipmentNameLength, out var nameProblem);
            if (nameProblem != null)
                return Refused(SaveStatus.Invalid, $"Equipment name: {nameProblem} Nothing was saved.");
            var rangeProblem = CheckRange(ruStart, ruEnd, RackUnits(rackRecordId));
            if (rangeProblem != null)
                return Refused(SaveStatus.Invalid, rangeProblem + " Nothing was saved.");

            Reload();
            if (IsReadOnly)
                return Refused(SaveStatus.ReadOnly, StatusMessage);
            var count = ItemsInRack(m_document, rackRecordId).Count;
            if (count >= m_rules.maxEquipmentPerRack)
                return Refused(SaveStatus.Invalid,
                    $"This rack already has {count} equipment records, the prototype's limit. Nothing was saved.");
            var overlaps = Overlapping(m_document, rackRecordId, null, ruStart, ruEnd);
            if (overlaps.Count > 0 && m_rules.ruOverlap == DemoAuthoringSettings.OverlapBlock)
                return Refused(SaveStatus.Overlap, OverlapWarning(ruStart, ruEnd, overlaps) + " Nothing was saved.");

            var now = Timestamp(m_utcNow());
            var item = new StoredEquipment
            {
                equipmentId = NewId("eq"),
                rackRecordId = rackRecordId,
                name = cleanName,
                ruStart = ruStart,
                ruEnd = ruEnd,
                revision = 1,
                createdAt = now,
                updatedAt = now
            };
            item.descriptions.Add(new StoredDescription { descriptionId = NewId("dsc"), labelId = "", text = "", createdAt = now, updatedAt = now });
            var next = Copy(m_document);
            next.equipment.Add(item);
            if (!Commit(next, out var error))
                return Refused(SaveStatus.StorageError, $"The browser refused to save ({error}). Nothing was saved.");

            var result = Done($"Added {cleanName} at {RangeText(ruStart, ruEnd)} with one empty, unnamed description.");
            result.EquipmentId = item.equipmentId;
            if (overlaps.Count > 0)
                result.Warnings.Add(OverlapWarning(ruStart, ruEnd, overlaps));
            return result;
        }

        /// <summary>
        /// Saves the equipment editor: name, RU range and the descriptions in display order.
        /// Descriptions keep their IDs; new ones (empty ID) get one. Only empty descriptions may be
        /// left out (removed). Text and name references of other items are never touched.
        /// </summary>
        public AuthoringResult SaveEquipment(EquipmentDraft draft)
        {
            if (draft == null || string.IsNullOrEmpty(draft.equipmentId))
                return Refused(SaveStatus.Invalid, "No equipment record was named. Nothing was saved.");
            var cleanName = CleanName(draft.name, m_rules.maxEquipmentNameLength, out var nameProblem);
            if (nameProblem != null)
                return Refused(SaveStatus.Invalid, $"Equipment name: {nameProblem} Nothing was saved.");
            var drafts = draft.descriptions ?? new List<DescriptionDraft>();
            if (drafts.Count == 0)
                return Refused(SaveStatus.Invalid, "An equipment record keeps at least one description. Nothing was saved.");
            if (drafts.Count > m_rules.maxDescriptionsPerItem)
                return Refused(SaveStatus.Invalid,
                    $"An equipment record can have at most {m_rules.maxDescriptionsPerItem} descriptions in this prototype. Nothing was saved.");
            var texts = new List<string>(drafts.Count);
            for (var i = 0; i < drafts.Count; i++)
            {
                if (drafts[i] == null)
                    return Refused(SaveStatus.Invalid, "An empty description entry was sent. Nothing was saved.");
                texts.Add(Sanitize(drafts[i].text, out var tooLong));
                if (tooLong)
                    return Refused(SaveStatus.Invalid,
                        $"Description {i + 1} is longer than {MaxDescriptionLength} characters. Nothing was saved.");
            }

            Reload();
            if (IsReadOnly)
                return Refused(SaveStatus.ReadOnly, StatusMessage);
            var stored = FindItem(m_document, draft.equipmentId);
            if (stored == null || !m_seeds.ContainsKey(stored.rackRecordId ?? ""))
                return Refused(SaveStatus.UnknownRecord, "That equipment record is not in this browser profile. Nothing was saved.");
            if (stored.revision != draft.baseRevision)
                return Refused(SaveStatus.Conflict,
                    $"This equipment record changed after you opened it (now version {stored.revision}, you opened version " +
                    $"{draft.baseRevision}). Nothing was saved. Copy your text, reopen the record and save again.");
            var rangeProblem = CheckRange(draft.ruStart, draft.ruEnd, RackUnits(stored.rackRecordId));
            if (rangeProblem != null)
                return Refused(SaveStatus.Invalid, rangeProblem + " Nothing was saved.");

            var storedById = new Dictionary<string, StoredDescription>();
            foreach (var d in stored.descriptions)
                if (d?.descriptionId != null)
                    storedById[d.descriptionId] = d;
            var seen = new HashSet<string>();
            for (var i = 0; i < drafts.Count; i++)
            {
                var d = drafts[i];
                var id = d.descriptionId ?? "";
                var labelId = d.labelId ?? "";
                StoredDescription before = null;
                if (id.Length > 0)
                {
                    if (!storedById.TryGetValue(id, out before))
                        return Refused(SaveStatus.Conflict,
                            "A description in your editor is no longer part of this record. Nothing was saved; reopen the record.");
                    if (!seen.Add(id))
                        return Refused(SaveStatus.Invalid, "The same description was sent twice. Nothing was saved.");
                }
                if (labelId.Length == 0 || (before != null && before.labelId == labelId))
                    continue;  // unnamed, or a reference kept as it was (even an unknown one is preserved)
                var label = FindLabel(m_document, labelId);
                if (label == null)
                    return Refused(SaveStatus.Invalid, $"Description {i + 1} uses a name that is not in the list. Nothing was saved.");
                if (label.retired)
                    return Refused(SaveStatus.Conflict,
                        $"The name '{label.name}' was replaced by '{FindLabel(m_document, label.replacedByLabelId)?.name}' while you " +
                        $"were editing. Choose a name again for description {i + 1}. Nothing was saved.");
            }
            foreach (var d in stored.descriptions)
                if (d != null && !seen.Contains(d.descriptionId ?? "") && !string.IsNullOrWhiteSpace(d.text))
                    return Refused(SaveStatus.Invalid,
                        "A description that holds text can't be removed in this prototype (deleting values is not decided). Nothing was saved.");

            var overlaps = Overlapping(m_document, stored.rackRecordId, stored.equipmentId, draft.ruStart, draft.ruEnd);
            if (overlaps.Count > 0 && m_rules.ruOverlap == DemoAuthoringSettings.OverlapBlock)
                return Refused(SaveStatus.Overlap, OverlapWarning(draft.ruStart, draft.ruEnd, overlaps) + " Nothing was saved.");

            var now = Timestamp(m_utcNow());
            var next = Copy(m_document);
            var item = FindItem(next, stored.equipmentId);
            var previous = new Dictionary<string, StoredDescription>();
            foreach (var d in item.descriptions)
                if (d != null)
                    previous.TryAdd(d.descriptionId ?? "", d);
            var changed = item.name != cleanName || item.ruStart != draft.ruStart || item.ruEnd != draft.ruEnd ||
                          item.descriptions.Count != drafts.Count;
            var list = new List<StoredDescription>(drafts.Count);
            var added = 0;
            for (var i = 0; i < drafts.Count; i++)
            {
                var id = drafts[i].descriptionId ?? "";
                var labelId = drafts[i].labelId ?? "";
                if (id.Length == 0)
                {
                    list.Add(new StoredDescription { descriptionId = NewId("dsc"), labelId = labelId, text = texts[i], createdAt = now, updatedAt = now });
                    added++;
                    changed = true;
                    continue;
                }
                var d = previous[id];
                if (i >= item.descriptions.Count || item.descriptions[i]?.descriptionId != id)
                    changed = true;  // moved
                if (d.labelId != labelId || d.text != texts[i])
                {
                    d.labelId = labelId;
                    d.text = texts[i];
                    d.updatedAt = now;
                    changed = true;
                }
                list.Add(d);
            }
            if (!changed)
                return Refused(SaveStatus.NoChange, "No changes to save.");
            var removed = item.descriptions.Count(d => d != null && !seen.Contains(d.descriptionId ?? ""));
            item.descriptions = list;
            item.name = cleanName;
            item.ruStart = draft.ruStart;
            item.ruEnd = draft.ruEnd;
            item.revision++;
            item.updatedAt = now;
            if (!Commit(next, out var error))
                return Refused(SaveStatus.StorageError,
                    $"The browser refused to save ({error}). Nothing was saved; your changes are still in the editor.");

            var result = Done($"Saved {cleanName} (version {item.revision}).");
            result.EquipmentId = item.equipmentId;
            if (added > 0)
                result.Message += $" {added} new description(s) added to this item only.";
            if (removed > 0)
                result.Message += $" {removed} empty description(s) removed.";
            if (overlaps.Count > 0)
                result.Warnings.Add(OverlapWarning(item.ruStart, item.ruEnd, overlaps));
            foreach (var group in list.Where(d => !string.IsNullOrEmpty(d.labelId)).GroupBy(d => d.labelId).Where(g => g.Count() > 1))
                result.Warnings.Add($"This item has {group.Count()} descriptions named '{FindLabel(next, group.Key)?.name}'; " +
                                    "each keeps its own text.");
            return result;
        }

        // ============================================================== description names

        /// <summary>Adds a name to the shared list. An existing name (any capitalisation) is reused, not duplicated.</summary>
        public AuthoringResult CreateLabel(string name)
        {
            var clean = CleanName(name, m_rules.maxLabelNameLength, out var problem);
            if (problem != null)
                return Refused(SaveStatus.Invalid, $"Description name: {problem} Nothing was added.");
            Reload();
            if (IsReadOnly)
                return Refused(SaveStatus.ReadOnly, StatusMessage);
            var existing = ActiveLabelNamed(m_document, clean, null);
            if (existing != null)
            {
                var same = Refused(SaveStatus.NoChange, $"'{existing.name}' is already in the list; it was used instead of a duplicate.");
                same.LabelId = existing.labelId;
                return same;
            }
            if (m_document.labels.Count(l => l != null && !l.retired) >= m_rules.maxLabels)
                return Refused(SaveStatus.Invalid, $"The list already holds {m_rules.maxLabels} names, the prototype's limit. Nothing was added.");
            var now = Timestamp(m_utcNow());
            var label = new StoredLabel { labelId = NewId("lbl"), name = clean, revision = 1, createdAt = now, updatedAt = now };
            var next = Copy(m_document);
            next.labels.Add(label);
            if (!Commit(next, out var error))
                return Refused(SaveStatus.StorageError, $"The browser refused to save ({error}). Nothing was added.");
            var result = Done($"Added '{clean}' to the description names. No equipment record changed.");
            result.LabelId = label.labelId;
            return result;
        }

        /// <summary>
        /// Corrects a name everywhere (D041 "Rename"): every description that uses it shows the new
        /// spelling; no text changes. A clash with another existing name is refused.
        /// </summary>
        public AuthoringResult RenameLabel(string labelId, int baseRevision, string newName)
        {
            var clean = CleanName(newName, m_rules.maxLabelNameLength, out var problem);
            if (problem != null)
                return Refused(SaveStatus.Invalid,
                    $"New name: {problem} Nothing was renamed. To stop using a name, use Replace and choose a replacement.");
            Reload();
            if (IsReadOnly)
                return Refused(SaveStatus.ReadOnly, StatusMessage);
            var label = FindLabel(m_document, labelId);
            if (label == null)
                return Refused(SaveStatus.UnknownRecord, "That name is not in the list. Nothing was renamed.");
            if (label.retired)
                return Refused(SaveStatus.Conflict, $"'{label.name}' was already replaced. Nothing was renamed.");
            if (label.revision != baseRevision)
                return Refused(SaveStatus.Conflict, $"'{label.name}' changed after you opened the list. Nothing was renamed; check it and try again.");
            if (label.name == clean)
                return Refused(SaveStatus.NoChange, "That is already the name's spelling.");
            var other = ActiveLabelNamed(m_document, clean, label.labelId);
            if (other != null)
                return Refused(SaveStatus.Collision,
                    $"'{other.name}' is already in the list, so '{label.name}' was not renamed. To combine the two names, " +
                    $"use Replace on '{label.name}' and choose '{other.name}'.");

            var now = Timestamp(m_utcNow());
            var next = Copy(m_document);
            var target = FindLabel(next, label.labelId);
            var oldName = target.name;
            target.previousNames.Add(oldName);
            target.name = clean;
            target.revision++;
            target.updatedAt = now;
            if (!Commit(next, out var error))
                return Refused(SaveStatus.StorageError, $"The browser refused to save ({error}). Nothing was renamed.");
            CountUses(m_document, label.labelId, out var uses, out var items);
            var result = Done($"Renamed '{oldName}' to '{clean}'. {uses} description(s) on {items} equipment item(s) now show " +
                              "the new name; their text is unchanged.");
            result.LabelId = label.labelId;
            result.Affected = uses;
            return result;
        }

        /// <summary>
        /// Retires a name by moving every description that uses it to a replacement (D041). Give
        /// either replacementLabelId (an existing active name) or replacementName (a new or existing
        /// name). Without a valid replacement nothing changes. All references move in one write.
        /// </summary>
        public AuthoringResult ReplaceLabel(string labelId, int baseRevision, string replacementLabelId, string replacementName)
        {
            var hasId = !string.IsNullOrEmpty(replacementLabelId);
            var hasName = !string.IsNullOrWhiteSpace(replacementName);
            if (!hasId && !hasName)
                return Refused(SaveStatus.Invalid,
                    "Choose the name that replaces it: an existing name or a new one. A description name can't be removed " +
                    "without a replacement, so nothing was changed.");
            if (hasId && hasName)
                return Refused(SaveStatus.Invalid, "Choose either an existing name or a new name as the replacement, not both. Nothing was changed.");
            string cleanReplacement = null;
            if (hasName)
            {
                cleanReplacement = CleanName(replacementName, m_rules.maxLabelNameLength, out var problem);
                if (problem != null)
                    return Refused(SaveStatus.Invalid, $"Replacement name: {problem} Nothing was changed.");
            }

            Reload();
            if (IsReadOnly)
                return Refused(SaveStatus.ReadOnly, StatusMessage);
            var old = FindLabel(m_document, labelId);
            if (old == null)
                return Refused(SaveStatus.UnknownRecord, "That name is not in the list. Nothing was changed.");
            if (old.retired)
                return Refused(SaveStatus.Conflict, $"'{old.name}' was already replaced. Nothing was changed.");
            if (old.revision != baseRevision)
                return Refused(SaveStatus.Conflict, $"'{old.name}' changed after you opened the list. Nothing was changed; check it and try again.");

            var now = Timestamp(m_utcNow());
            var next = Copy(m_document);
            var oldNext = FindLabel(next, old.labelId);
            StoredLabel target;
            var reusedExisting = false;
            if (hasId)
            {
                target = FindLabel(next, replacementLabelId);
                if (target == null)
                    return Refused(SaveStatus.Invalid, "The chosen replacement is not in the list. Nothing was changed.");
                if (target.retired)
                    return Refused(SaveStatus.Invalid, $"'{target.name}' was itself replaced; choose another replacement. Nothing was changed.");
                if (target.labelId == old.labelId)
                    return Refused(SaveStatus.Invalid, "Choose a different name as the replacement. To fix the spelling, use Rename. Nothing was changed.");
            }
            else
            {
                target = ActiveLabelNamed(next, cleanReplacement, null);
                if (target != null && target.labelId == old.labelId)
                    return Refused(SaveStatus.Invalid,
                        "The replacement must be a different name. To fix the spelling, use Rename. Nothing was changed.");
                if (target != null)
                    reusedExisting = true;
                else
                {
                    target = new StoredLabel { labelId = NewId("lbl"), name = cleanReplacement, revision = 1, createdAt = now, updatedAt = now };
                    next.labels.Add(target);
                }
            }

            // Every description that used the old name, and the items that already use the target name.
            var before = new Dictionary<string, (string equipmentId, string text)>();
            var affected = new List<StoredDescription>();
            var owners = new List<StoredEquipment>();
            var collisions = new List<StoredEquipment>();
            foreach (var item in next.equipment)
            {
                if (item == null)
                    continue;
                var touches = false;
                var hasTarget = false;
                foreach (var d in item.descriptions)
                {
                    if (d == null)
                        continue;
                    before[d.descriptionId ?? ""] = (item.equipmentId, d.text);
                    if (d.labelId == old.labelId)
                    {
                        affected.Add(d);
                        touches = true;
                    }
                    else if (d.labelId == target.labelId)
                        hasTarget = true;
                }
                if (touches)
                    owners.Add(item);
                if (touches && hasTarget)
                    collisions.Add(item);
            }
            if (collisions.Count > 0 && m_rules.labelCollision == DemoAuthoringSettings.CollisionBlock)
                return Refused(SaveStatus.Collision,
                    $"{Names(collisions)} already {(collisions.Count == 1 ? "has" : "have")} a description named '{target.name}'. " +
                    "Nothing was changed. Give one of the two descriptions on " +
                    $"{(collisions.Count == 1 ? "that item" : "those items")} a different name first, then replace again.");

            foreach (var d in affected)
            {
                d.labelId = target.labelId;
                d.updatedAt = now;
            }
            foreach (var item in owners)
            {
                item.revision++;  // an editor opened before this change must reopen, not write the old name back
                item.updatedAt = now;
            }
            oldNext.retired = true;
            oldNext.retiredAt = now;
            oldNext.replacedByLabelId = target.labelId;
            oldNext.reassignedDescriptionIds = affected.Select(d => d.descriptionId).ToList();
            oldNext.revision++;
            oldNext.updatedAt = now;

            // Preservation check before anything is written: same descriptions, same items, same text,
            // nothing left on the retired name.
            var after = 0;
            foreach (var item in next.equipment)
            {
                if (item == null)
                    continue;
                foreach (var d in item.descriptions)
                {
                    if (d == null)
                        continue;
                    after++;
                    if (d.labelId == old.labelId || !before.TryGetValue(d.descriptionId ?? "", out var was) ||
                        was.equipmentId != item.equipmentId || was.text != d.text)
                        return Refused(SaveStatus.Invalid, "The replacement failed its preservation check, so nothing was changed.");
                }
            }
            if (after != before.Count)
                return Refused(SaveStatus.Invalid, "The replacement failed its preservation check, so nothing was changed.");

            if (!Commit(next, out var error))
                return Refused(SaveStatus.StorageError,
                    $"The browser refused to save ({error}). Nothing was changed: '{old.name}' is still in the list and its " +
                    $"{affected.Count} description(s) still use it.");

            var result = Done($"Replaced '{old.name}' with '{target.name}' on {affected.Count} description(s) across " +
                              $"{owners.Count} equipment item(s); every description kept its text. '{old.name}' is no longer " +
                              "offered in the list.");
            if (reusedExisting)
                result.Message += $" '{target.name}' was already in the list, so it was used.";
            if (collisions.Count > 0)
                result.Warnings.Add($"{Names(collisions)} already had a description named '{target.name}'. Both descriptions " +
                                    "are kept with their own text and now share that name.");
            result.LabelId = target.labelId;
            result.Affected = affected.Count;
            return result;
        }

        // ============================================================== reset and export

        /// <summary>
        /// Starts this site's demo data over: original rack notes, no equipment, the starter names.
        /// Earlier-format data and backups are kept. Refused for data written by a newer version.
        /// </summary>
        public bool Clear(out string error)
        {
            Reload();
            if (IsReadOnly)
            {
                error = StatusMessage;
                return false;
            }
            var next = SeedDocument(MigrationReset);
            if (m_storage.TryRead(LegacyStorageKey, out var legacyRaw, out _) && legacyRaw != null)
            {
                next.migration.fromKey = LegacyStorageKey;
                next.migration.fromSchemaVersion = LegacySchemaVersion;
            }
            next.migration.migratedAt = Timestamp(m_utcNow());
            if (!Commit(next, out var writeError))
            {
                error = writeError;
                return false;
            }
            error = null;
            StatusMessage = "Saved demo data was reset to the original demo content." +
                            (legacyRaw != null ? " The earlier demo version's saved copy is kept unchanged and included in JSON exports." : "");
            return true;
        }

        public DemoRecordsExport BuildExport(string origin, string build)
        {
            var export = new DemoRecordsExport
            {
                notice = Notice,
                mappingNotice = MappingNotice,
                exportedAt = Timestamp(m_utcNow()),
                siteId = m_site.siteId,
                siteName = m_site.siteName,
                storageKey = StorageKey,
                storageDescription = StorageDescription,
                origin = origin ?? "",
                build = build ?? "",
                readOnly = IsReadOnly,
                storeStatus = StatusMessage,
                authoring = m_rules,
                migration = Clone(m_document.migration),
                records = All()
            };
            foreach (var id in m_recordOrder)
                foreach (var item in TopFirst(m_document, id))
                    export.equipment.Add(GetEquipment(item.equipmentId));
            export.labels = Catalog().labels;
            foreach (var entry in m_document.rackNotes)
                if (!m_seeds.ContainsKey(entry.recordId))
                    export.unmatchedStoredEntries.Add(entry.Clone());
            foreach (var item in m_document.equipment)
                if (item != null && !m_seeds.ContainsKey(item.rackRecordId ?? ""))
                    export.unmatchedEquipment.Add(JsonUtility.FromJson<StoredEquipment>(JsonUtility.ToJson(item)));
            if (m_storage.TryListKeys(KeyPrefix, out var keys, out _))
                foreach (var key in keys.Where(k => k != StorageKey).OrderBy(k => k, StringComparer.Ordinal))
                {
                    if (!m_storage.TryRead(key, out var raw, out _) || raw == null)
                        continue;
                    var truncated = raw.Length > MaxStoredCopyCharacters;
                    export.storedCopies.Add(new StoredCopy
                    {
                        key = key,
                        role = key == LegacyStorageKey ? "earlier demo format (version 1); never changed by this build"
                            : key.Contains(".unreadable-") ? "backup of saved data that could not be read"
                            : "other demo data under the same prefix",
                        characters = raw.Length,
                        truncated = truncated,
                        raw = truncated ? raw.Substring(0, MaxStoredCopyCharacters) : raw
                    });
                }
            return export;
        }

        public string ExportJson(string origin, string build) => JsonUtility.ToJson(BuildExport(origin, build), true);

        // ============================================================== text rules

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
                        sb.Append('\uFFFD');
                }
                else if (char.IsLowSurrogate(c))
                    sb.Append('\uFFFD');
                else
                    sb.Append(c);
            }
            tooLong = sb.Length > MaxDescriptionLength;
            return sb.ToString();
        }

        /// <summary>
        /// A one-line name: line breaks and tabs become spaces, other control characters go, runs of
        /// spaces collapse and the ends are trimmed. problem is null when the name can be used.
        /// </summary>
        public static string CleanName(string raw, int maxLength, out string problem)
        {
            var text = Sanitize(raw, out _);
            var sb = new StringBuilder(text.Length);
            var space = false;
            foreach (var c in text)
            {
                if (char.IsWhiteSpace(c))
                {
                    space = sb.Length > 0;
                    continue;
                }
                if (space)
                    sb.Append(' ');
                space = false;
                sb.Append(c);
            }
            var clean = sb.ToString();
            problem = clean.Length == 0 ? "a name is needed."
                : clean.Length > maxLength ? $"use at most {maxLength} characters."
                : null;
            return clean;
        }

        /// <summary>Comparison key for names: equal keys mean the same name (case is ignored).</summary>
        public static string NameKey(string cleanName) => (cleanName ?? "").ToLowerInvariant();

        public static string Timestamp(DateTime utc) =>
            utc.ToUniversalTime().ToString("yyyy-MM-dd'T'HH:mm:ss'Z'", CultureInfo.InvariantCulture);

        public static string RangeText(int start, int end) =>
            start == end ? $"RU {start}" : $"RU {start}-{end} ({end - start + 1}U)";

        // ============================================================== helpers

        public int RackUnits(string recordId) =>
            recordId != null && m_seeds.TryGetValue(recordId, out var seed) && seed.rackUnits > 0 ? seed.rackUnits : m_rules.rackUnitsDefault;

        static string CheckRange(int start, int end, int units)
        {
            if (start < 1 || end < 1 || start > units || end > units)
                return $"Rack units must be whole numbers from 1 to {units} (this rack's size in the prototype).";
            if (start > end)
                return $"The first rack unit ({start}) is above the last ({end}). For a 2U item at RU 20 and 21, enter 20 to 21.";
            return null;
        }

        /// <summary>Items in the rack whose RU range shares at least one unit with start..end.</summary>
        static List<StoredEquipment> Overlapping(LocalRecordsDocument document, string rackRecordId, string exceptId, int start, int end) =>
            ItemsInRack(document, rackRecordId)
                .Where(e => e.equipmentId != exceptId && e.ruStart <= end && start <= e.ruEnd)
                .ToList();

        static string OverlapText(List<StoredEquipment> overlaps) =>
            overlaps.Count == 0 ? "" : "Shares rack units with " + string.Join(", ", overlaps.Select(e => $"{e.name} ({RangeText(e.ruStart, e.ruEnd)})"));

        static string OverlapWarning(int start, int end, List<StoredEquipment> overlaps) =>
            $"{RangeText(start, end)} overlaps {string.Join(", ", overlaps.Select(e => $"{e.name} ({RangeText(e.ruStart, e.ruEnd)})"))}. " +
            "Two items can share rack units only when one is mounted at the front and one at the rear, which this prototype " +
            "does not record; check the numbers.";

        static List<StoredEquipment> ItemsInRack(LocalRecordsDocument document, string rackRecordId) =>
            document.equipment.Where(e => e != null && e.rackRecordId == rackRecordId).ToList();

        /// <summary>The rack's items as a rack elevation lists them: top position first.</summary>
        List<StoredEquipment> TopFirst(LocalRecordsDocument document, string rackRecordId)
        {
            var items = ItemsInRack(document, rackRecordId);
            var bottomUp = m_rules.ruNumbering != DemoAuthoringSettings.NumberingTopDown;  // bottom-up: higher RU = higher up
            return (bottomUp
                    ? items.OrderByDescending(e => e.ruEnd).ThenByDescending(e => e.ruStart)
                    : items.OrderBy(e => e.ruStart).ThenBy(e => e.ruEnd))
                .ThenBy(e => e.name ?? "", StringComparer.OrdinalIgnoreCase)
                .ThenBy(e => e.equipmentId, StringComparer.Ordinal)
                .ToList();
        }

        static StoredRecordEntry FindNote(LocalRecordsDocument document, string recordId)
        {
            foreach (var entry in document.rackNotes)
                if (entry.recordId == recordId)
                    return entry;
            return null;
        }

        static StoredEquipment FindItem(LocalRecordsDocument document, string equipmentId)
        {
            if (string.IsNullOrEmpty(equipmentId))
                return null;
            foreach (var item in document.equipment)
                if (item != null && item.equipmentId == equipmentId)
                    return item;
            return null;
        }

        static StoredLabel FindLabel(LocalRecordsDocument document, string labelId)
        {
            if (string.IsNullOrEmpty(labelId))
                return null;
            foreach (var label in document.labels)
                if (label != null && label.labelId == labelId)
                    return label;
            return null;
        }

        static StoredLabel ActiveLabelNamed(LocalRecordsDocument document, string cleanName, string exceptLabelId)
        {
            var key = NameKey(cleanName);
            foreach (var label in document.labels)
                if (label != null && !label.retired && label.labelId != exceptLabelId && NameKey(label.name) == key)
                    return label;
            return null;
        }

        static void CountUses(LocalRecordsDocument document, string labelId, out int uses, out int items)
        {
            uses = 0;
            items = 0;
            foreach (var item in document.equipment)
            {
                if (item == null)
                    continue;
                var n = item.descriptions.Count(d => d != null && d.labelId == labelId);
                uses += n;
                if (n > 0)
                    items++;
            }
        }

        string Names(List<StoredEquipment> items) =>
            string.Join(", ", items.Select(e => $"{e.name} in {(m_seeds.TryGetValue(e.rackRecordId ?? "", out var r) ? r.name : "an unknown rack")}"));

        string NewId(string prefix) => prefix + "-" + m_newGuid().ToLowerInvariant();

        /// <summary>
        /// The one place that writes the document: back up unreadable data first, then a single
        /// write of the complete next document. m_document changes only after that write worked.
        /// </summary>
        bool Commit(LocalRecordsDocument next, out string error)
        {
            if (m_unreadableRaw != null)
            {
                var backupKey = StorageKey + ".unreadable-" + m_utcNow().ToString("yyyyMMdd'T'HHmmss'Z'", CultureInfo.InvariantCulture);
                if (!m_storage.TryWrite(backupKey, m_unreadableRaw, out var backupError))
                {
                    IsReadOnly = true;
                    StatusMessage = $"Could not back up unreadable saved data ({backupError}); saving is disabled so it is not overwritten.";
                    error = StatusMessage;
                    return false;
                }
            }
            var now = Timestamp(m_utcNow());
            next.schema = DocumentSchema;
            next.schemaVersion = DocumentSchemaVersion;
            next.siteId = m_site.siteId;
            next.notice = Notice;
            next.updatedAt = now;
            if (string.IsNullOrEmpty(next.migration.migratedAt))
                next.migration.migratedAt = now;
            if (!m_storage.TryWrite(StorageKey, JsonUtility.ToJson(next), out error))
                return false;
            m_document = next;
            m_persisted = true;
            m_unreadableRaw = null;
            StatusMessage = DescribeLoaded(m_legacyPresent);  // describe what is stored now
            return true;
        }

        static LocalRecordsDocument Copy(LocalRecordsDocument source)
        {
            var copy = JsonUtility.FromJson<LocalRecordsDocument>(JsonUtility.ToJson(source));
            Normalize(copy);
            return copy;
        }

        static StoredMigration Clone(StoredMigration source) =>
            JsonUtility.FromJson<StoredMigration>(JsonUtility.ToJson(source ?? new StoredMigration()));

        SaveResult Result(SaveStatus status, string recordId, string message) =>
            new() { Status = status, Message = message, Record = Get(recordId) };

        static AuthoringResult Done(string message) => new() { Status = SaveStatus.Saved, Message = message };

        static AuthoringResult Refused(SaveStatus status, string message) => new() { Status = status, Message = message };
    }
}
