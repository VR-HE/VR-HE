// VR-HE interactive browser demo: data shapes of the provisional local record store.
//
// PROVISIONAL PROTOTYPE DATA MODEL, not a production schema. Three groups of types:
//   Stored*      what DemoRecordStore writes to browser storage (schema "vrhe.demo.local-records" v2).
//   *View        what the page shows (read-only projections, rebuilt after every change).
//   *Draft       what the equipment editor sends back on Save.
// JsonUtility (de)serializes all of them, so they are plain [Serializable] classes with public
// fields; field names are part of the storage, export and page contracts (DemoMessages.cs,
// demo-ui.js, Tools/verify_interactive_demo.py). Rename a field only together with a schema
// version change and a migration.
//
// Identity, kept separate from display text and position on purpose:
//   rack       recordId (rec-...)      from the site file; its rack note stays rack-level.
//   equipment  equipmentId (eq-...)    belongs to one rack; occupies ruStart..ruEnd (inclusive).
//   description descriptionId (dsc-...) belongs to one equipment item; list order is display order only.
//   name       labelId (lbl-...)       a reusable description name ("Serial number"); a description
//                                      refers to it by labelId ("" = unnamed), never by text.
// A spreadsheet adapter would map these IDs explicitly; none exists in this demo.

using System;
using System.Collections.Generic;

namespace VRHE.InteractiveDemo.Records
{
    public enum SaveStatus
    {
        Saved,
        NoChange,
        Conflict,       // stale revision: someone else saved first; nothing written
        ReadOnly,
        UnknownRecord,
        Invalid,        // input refused by a rule; nothing written
        StorageError,   // the browser refused the write; nothing changed
        Collision,      // a name clash that the rules say must be resolved first; nothing written
        Overlap         // RU ranges overlap and the rules say block; nothing written
    }

    // ------------------------------------------------------------------ stored (schema v2)

    /// <summary>One rack note (rack-level text). Same shape as a version 1 "entries" item.</summary>
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

    /// <summary>One reusable description name. Retired names stay listed with their replacement.</summary>
    [Serializable]
    public sealed class StoredLabel
    {
        public string labelId;
        public string name;
        public int revision;
        public string createdAt;   // "" for a starter name copied from the site file
        public string updatedAt;
        public bool retired;
        public string retiredAt;
        public string replacedByLabelId;
        public List<string> previousNames = new();             // earlier spellings, oldest first
        public List<string> reassignedDescriptionIds = new();  // descriptions moved to the replacement
    }

    [Serializable]
    public sealed class StoredDescription
    {
        public string descriptionId;
        public string labelId;   // "" = unnamed
        public string text;
        public string createdAt;
        public string updatedAt;
    }

    [Serializable]
    public sealed class StoredEquipment
    {
        public string equipmentId;
        public string rackRecordId;
        public string name;
        public int ruStart;   // inclusive; RU 1 is the bottom position (prototype numbering)
        public int ruEnd;     // inclusive; a 2U item at RU 20 and 21 is one record, 20..21
        public int revision;
        public string createdAt;
        public string updatedAt;
        public List<StoredDescription> descriptions = new();
    }

    /// <summary>Where this document's starting data came from.</summary>
    [Serializable]
    public sealed class StoredMigration
    {
        public string state = "";        // see DemoRecordStore.Migration* constants
        public string fromKey = "";      // the earlier format's storage key, if one was found
        public int fromSchemaVersion;
        public string sourceUpdatedAt = "";
        public int sourceEntries;
        public int carriedEntries;
        public string migratedAt = "";   // when this document was first written
    }

    [Serializable]
    public sealed class LocalRecordsDocument
    {
        public string schema;
        public int schemaVersion;
        public string siteId;
        public string notice;
        public string updatedAt;
        public StoredMigration migration = new();
        public List<StoredRecordEntry> rackNotes = new();
        public List<StoredLabel> labels = new();
        public List<StoredEquipment> equipment = new();
    }

    /// <summary>The first demo's format (schema version 1). Read for migration only, never written.</summary>
    [Serializable]
    public sealed class LegacyRecordsDocumentV1
    {
        public string schema;
        public int schemaVersion;
        public string siteId;
        public string notice;
        public string updatedAt;
        public List<StoredRecordEntry> entries = new();
    }

    [Serializable]
    sealed class DocumentHeader
    {
        public string schema;
        public int schemaVersion;
        public string siteId;
    }

    // ------------------------------------------------------------------ views

    /// <summary>A rack: seed fields, its rack note and a summary of its equipment.</summary>
    [Serializable]
    public sealed class DemoRecordView
    {
        public string recordId;
        public string kind;
        public string name;
        public string location;
        public string[] anchorIds;
        public string description;   // the rack note: rack-level text, not an equipment description
        public int revision;         // rack note revision; 0 = original demo text
        public string updatedAt;     // empty for original demo text
        public string source;        // "seed" or "local edit"
        public int rackUnits;
        public string ruNumbering;
        public List<EquipmentSummary> equipment = new();  // top of the rack first
    }

    [Serializable]
    public sealed class EquipmentSummary
    {
        public string equipmentId;
        public string name;
        public int ruStart;
        public int ruEnd;
        public int revision;
        public int descriptions;
        public int named;
        public string overlaps;  // "" or plain text naming overlapping items
    }

    [Serializable]
    public sealed class DescriptionView
    {
        public string descriptionId;
        public string labelId;
        public string labelName;   // "" when unnamed
        public string labelState;  // "none", "active", "retired" or "unknown"
        public string text;
        public string createdAt;
        public string updatedAt;
    }

    [Serializable]
    public sealed class EquipmentView
    {
        public string equipmentId;
        public string rackRecordId;
        public string rackName;
        public string name;
        public int ruStart;
        public int ruEnd;
        public int rackUnits;
        public string ruNumbering;
        public int revision;
        public string createdAt;
        public string updatedAt;
        public string overlaps;
        public List<DescriptionView> descriptions = new();
    }

    [Serializable]
    public sealed class LabelView
    {
        public string labelId;
        public string name;
        public int revision;
        public bool retired;
        public string retiredAt;
        public string replacedByLabelId;
        public string replacedByName;
        public string previousNames;  // earlier spellings joined with "; "
        public int uses;              // descriptions using this name now
        public int items;             // equipment items with such a description
        public int reassigned;        // retired names: descriptions moved to the replacement
    }

    [Serializable]
    public sealed class CatalogView
    {
        public int active;
        public List<LabelView> labels = new();  // active names A-Z, then retired names
    }

    // ------------------------------------------------------------------ editor input

    [Serializable]
    public sealed class EquipmentDraft
    {
        public string equipmentId;
        public int baseRevision;
        public string name;
        public int ruStart;
        public int ruEnd;
        public List<DescriptionDraft> descriptions = new();  // in display order
    }

    [Serializable]
    public sealed class DescriptionDraft
    {
        public string descriptionId;  // "" for a description added in the editor and not saved yet
        public string labelId;        // "" = unnamed
        public string text;
    }

    // ------------------------------------------------------------------ results and export

    public sealed class SaveResult
    {
        public SaveStatus Status;
        public string Message;
        public DemoRecordView Record;  // current view after the attempt (null for unknown records)
    }

    public sealed class AuthoringResult
    {
        public SaveStatus Status;
        public string Message = "";
        public readonly List<string> Warnings = new();
        public string EquipmentId = "";
        public string LabelId = "";
        public int Affected;          // descriptions moved by a name replacement
    }

    /// <summary>Raw text of another demo storage key, for inspection and recovery.</summary>
    [Serializable]
    public sealed class StoredCopy
    {
        public string key;
        public string role;
        public int characters;
        public bool truncated;
        public string raw;
    }

    [Serializable]
    public sealed class DemoRecordsExport
    {
        public string schema = "vrhe.demo.records-export";
        public int schemaVersion = 2;
        public string notice;
        public string mappingNotice;
        public string exportedAt;
        public string siteId;
        public string siteName;
        public string storageKey;
        public string storageDescription;
        public string origin;
        public string build;
        public bool readOnly;
        public string storeStatus;
        public DemoAuthoringSettings authoring;
        public StoredMigration migration;
        public List<DemoRecordView> records = new();       // racks with rack notes
        public List<EquipmentView> equipment = new();      // every equipment item with its descriptions
        public List<LabelView> labels = new();             // description names, including retired ones
        public List<StoredRecordEntry> unmatchedStoredEntries = new();  // rack notes for racks this build lacks
        public List<StoredEquipment> unmatchedEquipment = new();        // equipment under racks this build lacks
        public List<StoredCopy> storedCopies = new();      // earlier-format data and backups, raw
    }
}
