// VR-HE interactive browser demo: EditMode tests for record identity, local persistence,
// migration of the first demo's data, equipment/RU authoring and description names (D036-D041).
// They exercise DemoRecordStore against in-memory storage; real browser storage, reloads,
// relaunches and the page are checked separately in real browsers (Tools/verify_interactive_demo.py).

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using NUnit.Framework;
using UnityEngine;
using VRHE.InteractiveDemo.Records;

namespace VRHE.InteractiveDemo.Tests
{
    public sealed class DemoRecordStoreTests
    {
        static readonly string k_sitePath = Path.Combine(Application.dataPath, "InteractiveDemo/Data/demo-site.json");

        DemoSiteDefinition m_site;
        InMemoryKeyValueStorage m_storage;
        DateTime m_now;
        int m_guid;
        string m_a, m_b, m_c;

        [SetUp]
        public void SetUp()
        {
            m_site = DemoSiteDefinition.FromJson(File.ReadAllText(k_sitePath));
            m_storage = new InMemoryKeyValueStorage();
            m_now = new DateTime(2026, 11, 10, 12, 0, 0, DateTimeKind.Utc);
            m_guid = 0;
            m_a = m_site.records[0].recordId;  // Rack A1
            m_b = m_site.records[1].recordId;  // Rack A2
            m_c = m_site.records[5].recordId;  // Rack B1
        }

        DemoRecordStore NewStore() => new(m_site, m_storage, () => m_now, () => $"00000000-0000-4000-8000-{++m_guid:x12}");
        string Key => DemoRecordStore.StorageKeyFor(m_site.siteId);
        string LegacyKey => DemoRecordStore.LegacyStorageKeyFor(m_site.siteId);
        string SerialNumber => m_site.labels.Single(l => l.name == "Serial number").labelId;

        string LegacyRaw(string updatedAt, params (string id, string text, int revision)[] entries) =>
            "{\"schema\":\"vrhe.demo.local-records\",\"schemaVersion\":1,\"siteId\":\"" + m_site.siteId +
            "\",\"notice\":\"LOCAL DEMO DATA\",\"updatedAt\":\"" + updatedAt + "\",\"entries\":[" +
            string.Join(",", entries.Select(e => "{\"recordId\":\"" + e.id + "\",\"description\":\"" + e.text +
                                                 "\",\"revision\":" + e.revision + ",\"updatedAt\":\"2026-11-10T08:00:00Z\"}")) + "]}";

        static EquipmentDraft DraftOf(EquipmentView view) => new()
        {
            equipmentId = view.equipmentId,
            baseRevision = view.revision,
            name = view.name,
            ruStart = view.ruStart,
            ruEnd = view.ruEnd,
            descriptions = view.descriptions.Select(d => new DescriptionDraft
                { descriptionId = d.descriptionId, labelId = d.labelId, text = d.text }).ToList()
        };

        EquipmentView Create(DemoRecordStore store, string rack, string name, int start, int end)
        {
            var result = store.CreateEquipment(rack, name, start, end);
            Assert.AreEqual(SaveStatus.Saved, result.Status, result.Message);
            return store.GetEquipment(result.EquipmentId);
        }

        /// <summary>Saves an item whose descriptions are (labelId, text) pairs, reusing the existing IDs in order.</summary>
        EquipmentView SetDescriptions(DemoRecordStore store, EquipmentView view, params (string labelId, string text)[] wanted)
        {
            var draft = DraftOf(view);
            draft.descriptions = wanted.Select((w, i) => new DescriptionDraft
            {
                descriptionId = i < view.descriptions.Count ? view.descriptions[i].descriptionId : "",
                labelId = w.labelId,
                text = w.text
            }).ToList();
            var result = store.SaveEquipment(draft);
            Assert.AreEqual(SaveStatus.Saved, result.Status, result.Message);
            return store.GetEquipment(view.equipmentId);
        }

        static string LabelId(DemoRecordStore store, string name) =>
            store.Catalog().labels.Single(l => !l.retired && l.name == name).labelId;

        static int LabelRevision(DemoRecordStore store, string labelId) =>
            store.Catalog().labels.Single(l => l.labelId == labelId).revision;

        // ============================================================== site file

        [Test]
        public void ShippedSiteFileIsValid()
        {
            var problems = DemoSiteValidator.Validate(m_site);
            Assert.IsEmpty(problems, string.Join("\n", problems));
            Assert.GreaterOrEqual(m_site.anchors.Length, 2, "the task needs at least two selectable items");
            foreach (var anchor in m_site.anchors)
                Assert.AreNotEqual(anchor.anchorId, anchor.recordId);
            Assert.GreaterOrEqual(m_site.labels.Length, 1, "the dropdown needs starter names");
            Assert.AreEqual(42, m_site.Authoring.rackUnitsDefault);
            Assert.AreEqual(DemoAuthoringSettings.OverlapWarn, m_site.Authoring.ruOverlap);
            Assert.AreEqual(DemoAuthoringSettings.CollisionKeepBoth, m_site.Authoring.labelCollision);
        }

        [Test]
        public void IdentifiersAreFrozen()
        {
            // These identifiers are the durable link between saved data and records. Changing them
            // orphans every tester's saved edits; add new records instead.
            Assert.AreEqual("site-bfaaec37-26c3-4ca9-99f2-b1fb9de68f5a", m_site.siteId);
            Assert.AreEqual("rec-9040bad6-d264-4969-b923-a7df2cba2e93", m_site.records[0].recordId);
            Assert.AreEqual("rec-a9955c73-733d-4e06-8b70-e03eead46856", m_site.records[1].recordId);
            Assert.AreEqual("anc-836007b1-09cd-41f9-82e8-52da9a18fe75", m_site.anchors[0].anchorId);
            Assert.AreEqual("vrhe.demo.records.v2.site-bfaaec37-26c3-4ca9-99f2-b1fb9de68f5a", Key);
            Assert.AreEqual("vrhe.demo.records.v1.site-bfaaec37-26c3-4ca9-99f2-b1fb9de68f5a", LegacyKey,
                "the first demo's key: migration reads it, so it must not move");
        }

        [Test]
        public void ValidatorRejectsBrokenLinksAndDuplicates()
        {
            m_site.anchors[1].recordId = "rec-00000000-0000-0000-0000-000000000000";
            m_site.records[2].recordId = m_site.records[3].recordId;
            m_site.anchors[4].anchorId = "Rack A1";
            m_site.labels[1].name = " serial   NUMBER ";
            m_site.labels[2].labelId = "Model";
            var problems = DemoSiteValidator.Validate(m_site);
            Assert.IsTrue(problems.Any(p => p.Contains("unknown record")));
            Assert.IsTrue(problems.Any(p => p.Contains("duplicate recordId")));
            Assert.IsTrue(problems.Any(p => p.Contains("anc-<uuid>")));
            Assert.IsTrue(problems.Any(p => p.Contains("duplicate label name")), "names differing only in case/spaces clash");
            Assert.IsTrue(problems.Any(p => p.Contains("lbl-<uuid>")));
        }

        // ============================================================== rack notes (version 1 behaviour kept)

        [Test]
        public void EmptyStorageShowsSeedContentWithoutWriting()
        {
            var store = NewStore();
            var view = store.Get(m_a);
            Assert.AreEqual(m_site.records[0].description, view.description);
            Assert.AreEqual(0, view.revision);
            Assert.AreEqual(DemoRecordStore.SourceSeed, view.source);
            Assert.AreEqual(m_site.anchors[0].anchorId, view.anchorIds.Single());
            Assert.AreEqual(42, view.rackUnits);
            Assert.IsEmpty(view.equipment);
            CollectionAssert.AreEquivalent(m_site.labels.Select(l => l.labelId), store.Catalog().labels.Select(l => l.labelId));
            Assert.IsFalse(store.IsReadOnly);
            Assert.IsFalse(store.IsPersisted);
            Assert.AreEqual(0, m_storage.WriteCount, "opening must not write");
        }

        [Test]
        public void SavingOneRecordLeavesTheOtherUnchanged()
        {
            var store = NewStore();
            var before = store.Get(m_b).description;
            var result = store.Save(m_a, "Edited A1 note", 0);
            Assert.AreEqual(SaveStatus.Saved, result.Status, result.Message);
            Assert.AreEqual("Edited A1 note", store.Get(m_a).description);
            Assert.AreEqual(1, store.Get(m_a).revision);
            Assert.AreEqual(before, store.Get(m_b).description);
            Assert.AreEqual(0, store.Get(m_b).revision);
            Assert.AreEqual(DemoRecordStore.SourceSeed, store.Get(m_b).source);
        }

        [Test]
        public void SavedTextSurvivesANewStoreInstance()
        {
            NewStore().Save(m_a, "first", 0);
            NewStore().Save(m_b, "second", 0);
            var reopened = NewStore();
            Assert.AreEqual("first", reopened.Get(m_a).description);
            Assert.AreEqual("second", reopened.Get(m_b).description);
            Assert.AreEqual("2026-11-10T12:00:00Z", reopened.Get(m_a).updatedAt);
            Assert.AreEqual(DemoRecordStore.SourceLocalEdit, reopened.Get(m_a).source);
            Assert.IsTrue(reopened.IsPersisted);
        }

        [Test]
        public void StaleRevisionIsRefusedWithoutWriting()
        {
            var tab1 = NewStore();
            var tab2 = NewStore();
            Assert.AreEqual(SaveStatus.Saved, tab1.Save(m_a, "from tab 1", 0).Status);
            var writes = m_storage.WriteCount;
            var result = tab2.Save(m_a, "from tab 2", 0);
            Assert.AreEqual(SaveStatus.Conflict, result.Status);
            Assert.AreEqual(writes, m_storage.WriteCount);
            Assert.AreEqual("from tab 1", NewStore().Get(m_a).description);
            Assert.AreEqual("from tab 1", result.Record.description, "a conflict returns the current text");
        }

        [Test]
        public void SaveInOtherTabOfDifferentRecordIsKept()
        {
            var tab1 = NewStore();
            var tab2 = NewStore();
            tab1.Save(m_a, "A from tab 1", 0);
            Assert.AreEqual(SaveStatus.Saved, tab2.Save(m_b, "B from tab 2", 0).Status);
            var reopened = NewStore();
            Assert.AreEqual("A from tab 1", reopened.Get(m_a).description, "tab 2 must not overwrite tab 1's record");
            Assert.AreEqual("B from tab 2", reopened.Get(m_b).description);
        }

        [Test]
        public void UnchangedAndUnknownSavesWriteNothing()
        {
            var store = NewStore();
            Assert.AreEqual(SaveStatus.NoChange, store.Save(m_a, m_site.records[0].description, 0).Status);
            Assert.AreEqual(SaveStatus.UnknownRecord, store.Save("rec-00000000-0000-0000-0000-000000000000", "x", 0).Status);
            Assert.AreEqual(SaveStatus.UnknownRecord, store.Save(m_site.records[0].name, "x", 0).Status,
                "display names are not identifiers");
            Assert.AreEqual(0, m_storage.WriteCount);
        }

        [Test]
        public void StoredTextFollowsRecordIdNotNameOrAnchor()
        {
            NewStore().Save(m_a, "kept by id", 0);
            m_site.records[0].name = "Renamed rack";
            m_site.anchors[0].center = new[] { 9f, 9f, 9f };
            (m_site.records[0], m_site.records[1]) = (m_site.records[1], m_site.records[0]);
            var store = NewStore();
            Assert.AreEqual("kept by id", store.Get(m_a).description);
            Assert.AreEqual("Renamed rack", store.Get(m_a).name);
            Assert.AreEqual(0, store.Get(m_b).revision);
        }

        [Test]
        public void EntriesForUnknownRecordsArePreserved()
        {
            var store = NewStore();
            Create(store, m_a, "Known item", 10, 10);
            var raw = m_storage.Values[Key]
                .Replace("\"rackNotes\":[]", "\"rackNotes\":[{\"recordId\":\"rec-11111111-2222-3333-4444-555555555555\",\"description\":\"future\",\"revision\":4,\"updatedAt\":\"2026-11-09T00:00:00Z\"}]")
                .Replace("\"rackRecordId\":\"" + m_a + "\"", "\"rackRecordId\":\"rec-11111111-2222-3333-4444-666666666666\"");
            m_storage.SetRaw(Key, raw);
            store = NewStore();
            Assert.AreEqual(SaveStatus.Saved, store.Save(m_a, "edit", 0).Status);
            var export = store.BuildExport("http://127.0.0.1:8791", "test");
            Assert.AreEqual("future", export.unmatchedStoredEntries.Single().description);
            Assert.AreEqual("Known item", export.unmatchedEquipment.Single().name, "equipment under an unknown rack is kept");
            StringAssert.Contains("rec-11111111-2222-3333-4444-555555555555", m_storage.Values[Key]);
            StringAssert.Contains("rec-11111111-2222-3333-4444-666666666666", m_storage.Values[Key]);
        }

        [Test]
        public void NewerSchemaIsReadOnlyAndNeverRewritten()
        {
            var raw = "{\"schema\":\"vrhe.demo.local-records\",\"schemaVersion\":3,\"rackNotes\":[]}";
            m_storage.SetRaw(Key, raw);
            var store = NewStore();
            Assert.IsTrue(store.IsReadOnly);
            Assert.AreEqual(SaveStatus.ReadOnly, store.Save(m_a, "edit", 0).Status);
            Assert.AreEqual(SaveStatus.ReadOnly, store.CreateEquipment(m_a, "x", 1, 1).Status);
            Assert.AreEqual(SaveStatus.ReadOnly, store.CreateLabel("New name").Status);
            Assert.AreEqual(SaveStatus.ReadOnly, store.ReplaceLabel(SerialNumber, 1, "", "Other").Status);
            Assert.IsFalse(store.Clear(out _), "reset must not overwrite a newer version's data");
            Assert.AreEqual(raw, m_storage.Values[Key]);
            Assert.AreEqual(0, m_storage.WriteCount);
        }

        [Test]
        public void UnreadableDataIsBackedUpBeforeTheFirstWrite()
        {
            m_storage.SetRaw(Key, "{not json");
            var store = NewStore();
            Assert.IsFalse(store.IsReadOnly);
            Assert.AreEqual(m_site.records[0].description, store.Get(m_a).description);
            Assert.AreEqual(SaveStatus.Saved, store.Save(m_a, "edit", 0).Status);
            var backup = Key + ".unreadable-20261110T120000Z";
            Assert.AreEqual("{not json", m_storage.Values[backup]);
            Assert.AreEqual("edit", NewStore().Get(m_a).description);
            var copies = NewStore().BuildExport("", "").storedCopies;
            Assert.AreEqual("{not json", copies.Single(c => c.key == backup).raw, "backups are exported for recovery");
        }

        [Test]
        public void UnreadableDataIsNotOverwrittenWhenBackupFails()
        {
            m_storage.SetRaw(Key, "[1,2,3]");
            var store = NewStore();
            m_storage.FailWrites = true;
            Assert.AreEqual(SaveStatus.StorageError, store.Save(m_a, "edit", 0).Status);
            Assert.AreEqual("[1,2,3]", m_storage.Values[Key]);
        }

        [Test]
        public void WriteFailureIsReportedAndChangesNothing()
        {
            var store = NewStore();
            m_storage.FailWrites = true;
            var result = store.Save(m_a, "edit", 0);
            Assert.AreEqual(SaveStatus.StorageError, result.Status);
            Assert.AreEqual(m_site.records[0].description, store.Get(m_a).description);
            Assert.AreEqual(0, store.Get(m_a).revision);
            m_storage.FailWrites = false;
            Assert.AreEqual(SaveStatus.Saved, store.Save(m_a, "edit", 0).Status, "a retry after the failure works");
        }

        [Test]
        public void ReadFailureDisablesSaving()
        {
            m_storage.FailReads = true;
            var store = NewStore();
            Assert.IsTrue(store.IsReadOnly);
            Assert.AreEqual(SaveStatus.ReadOnly, store.Save(m_a, "edit", 0).Status);
            Assert.AreEqual(SaveStatus.ReadOnly, store.CreateEquipment(m_a, "x", 1, 1).Status);
        }

        [Test]
        public void DescriptionsAreSanitizedAndLimited()
        {
            var clean = DemoRecordStore.Sanitize("a\r\nb\rc\u0000d\te\u0007\ud800", out var tooLong);
            Assert.IsFalse(tooLong);
            Assert.AreEqual("a\nb\ncd\te\uFFFD", clean);
            Assert.AreEqual("\U0001F600", DemoRecordStore.Sanitize("\U0001F600", out _), "valid pairs are kept");

            var store = NewStore();
            var exact = new string('x', DemoRecordStore.MaxDescriptionLength);
            Assert.AreEqual(SaveStatus.Saved, store.Save(m_a, exact, 0).Status);
            Assert.AreEqual(SaveStatus.Invalid, store.Save(m_a, exact + "y", 1).Status);
            Assert.AreEqual(exact, store.Get(m_a).description);

            Assert.AreEqual("Power feed", DemoRecordStore.CleanName("  Power\t\n  feed ", 60, out var problem));
            Assert.IsNull(problem);
            DemoRecordStore.CleanName(" \t ", 60, out problem);
            Assert.IsNotNull(problem, "a blank name is not a name");
            DemoRecordStore.CleanName(new string('n', 61), 60, out problem);
            Assert.IsNotNull(problem);
        }

        // ============================================================== migration from the first demo (version 1)

        [Test]
        public void LegacyRackNotesAreShownWithoutWriting()
        {
            var legacy = LegacyRaw("2026-11-10T09:00:00Z", (m_a, "A1 note from the first demo", 3), (m_c, "B1 note", 1),
                ("rec-11111111-2222-3333-4444-555555555555", "unknown rack", 2));
            m_storage.SetRaw(LegacyKey, legacy);
            var store = NewStore();
            var a = store.Get(m_a);
            Assert.AreEqual("A1 note from the first demo", a.description);
            Assert.AreEqual(3, a.revision, "revisions are carried over");
            Assert.AreEqual("2026-11-10T08:00:00Z", a.updatedAt);
            Assert.AreEqual(DemoRecordStore.SourceLocalEdit, a.source);
            Assert.AreEqual("B1 note", store.Get(m_c).description);
            Assert.IsEmpty(a.equipment, "a rack note is not turned into an equipment description");
            Assert.AreEqual(DemoRecordStore.MigrationCarried, store.Migration.state);
            Assert.AreEqual(3, store.Migration.carriedEntries);
            StringAssert.Contains("earlier demo version", store.StatusMessage);
            Assert.IsFalse(store.IsPersisted);
            Assert.AreEqual(0, m_storage.WriteCount, "opening must not write");
            Assert.AreEqual(legacy, m_storage.Values[LegacyKey]);
        }

        [Test]
        public void FirstSaveWritesTheNewFormatAndKeepsTheLegacyCopy()
        {
            var legacy = LegacyRaw("2026-11-10T09:00:00Z", (m_a, "A1 note", 3), ("rec-11111111-2222-3333-4444-555555555555", "unknown rack", 2));
            m_storage.SetRaw(LegacyKey, legacy);
            var store = NewStore();
            m_storage.FailWritesToPrefix = LegacyKey;  // any attempt to write the first demo's key would fail the save
            Assert.AreEqual(SaveStatus.Conflict, store.Save(m_a, "stale", 0).Status, "the carried revision counts");
            Assert.AreEqual(SaveStatus.Saved, store.Save(m_b, "A2 edit", 0).Status);
            Assert.AreEqual(SaveStatus.Saved, store.CreateEquipment(m_a, "Switch", 40, 40).Status);
            Assert.AreEqual(legacy, m_storage.Values[LegacyKey], "the first demo's copy is never changed");
            var reopened = NewStore();
            Assert.IsTrue(reopened.IsPersisted);
            Assert.AreEqual("A1 note", reopened.Get(m_a).description);
            Assert.AreEqual(3, reopened.Get(m_a).revision);
            Assert.AreEqual("A2 edit", reopened.Get(m_b).description);
            Assert.AreEqual("unknown rack", reopened.BuildExport("", "").unmatchedStoredEntries.Single().description);
            var migration = reopened.Migration;
            Assert.AreEqual(DemoRecordStore.MigrationCarried, migration.state);
            Assert.AreEqual(LegacyKey, migration.fromKey);
            Assert.AreEqual("2026-11-10T09:00:00Z", migration.sourceUpdatedAt);
            Assert.AreEqual(2, migration.sourceEntries);
            Assert.AreEqual("2026-11-10T12:00:00Z", migration.migratedAt);
            Assert.AreEqual(SaveStatus.Saved, reopened.Save(m_a, "A1 updated", 3).Status);
            Assert.AreEqual(legacy, m_storage.Values[LegacyKey]);
        }

        [Test]
        public void UnreadableLegacyDataIsKeptAndExported()
        {
            m_storage.SetRaw(LegacyKey, "{oops");
            var store = NewStore();
            Assert.AreEqual(m_site.records[0].description, store.Get(m_a).description);
            StringAssert.Contains("could not be read", store.StatusMessage);
            Assert.AreEqual(SaveStatus.Saved, store.Save(m_a, "edit", 0).Status);
            Assert.AreEqual("{oops", m_storage.Values[LegacyKey]);
            var copy = NewStore().BuildExport("", "").storedCopies.Single(c => c.key == LegacyKey);
            Assert.AreEqual("{oops", copy.raw);
            StringAssert.Contains("version 1", copy.role);
        }

        [Test]
        public void LegacyChangesAfterTheCarryOverAreReportedNotLost()
        {
            m_storage.SetRaw(LegacyKey, LegacyRaw("2026-11-10T09:00:00Z", (m_a, "A1 note", 1)));
            NewStore().Save(m_b, "A2 edit", 0);
            var changed = LegacyRaw("2026-11-10T13:00:00Z", (m_a, "A1 changed in the old build", 2));
            m_storage.SetRaw(LegacyKey, changed);
            var store = NewStore();
            Assert.AreEqual("A1 note", store.Get(m_a).description, "the new format stays the source");
            StringAssert.Contains("changed its own saved copy", store.StatusMessage);
            Assert.AreEqual(changed, store.BuildExport("", "").storedCopies.Single(c => c.key == LegacyKey).raw);
        }

        [Test]
        public void ResetStartsOverWithoutResurrectingLegacyNotes()
        {
            var legacy = LegacyRaw("2026-11-10T09:00:00Z", (m_a, "A1 note", 1));
            m_storage.SetRaw(LegacyKey, legacy);
            m_storage.SetRaw("unrelated.key", "keep me");
            var store = NewStore();
            Create(store, m_a, "Switch", 40, 40);
            Assert.IsTrue(store.Clear(out var error), error);
            Assert.AreEqual(m_site.records[0].description, store.Get(m_a).description);
            Assert.IsEmpty(store.Get(m_a).equipment);
            var reopened = NewStore();
            Assert.AreEqual(m_site.records[0].description, reopened.Get(m_a).description, "reset is not undone by the legacy copy");
            Assert.AreEqual(DemoRecordStore.MigrationReset, reopened.Migration.state);
            Assert.AreEqual(legacy, m_storage.Values[LegacyKey]);
            Assert.AreEqual("keep me", m_storage.Values["unrelated.key"]);
        }

        // ============================================================== equipment and rack units (D037, D038)

        [Test]
        public void NewEquipmentStartsWithOneEmptyUnnamedDescription()
        {
            var store = NewStore();
            var item = Create(store, m_a, "Core switch", 40, 40);
            Assert.IsTrue(DemoSiteValidator.IsWellFormedId(item.equipmentId, "eq"), item.equipmentId);
            var only = item.descriptions.Single();
            Assert.IsTrue(DemoSiteValidator.IsWellFormedId(only.descriptionId, "dsc"), only.descriptionId);
            Assert.AreEqual("", only.labelId);
            Assert.AreEqual("none", only.labelState);
            Assert.AreEqual("", only.text);
            Assert.AreEqual(1, item.revision);
            Assert.AreEqual(m_a, item.rackRecordId);
            var rack = store.Get(m_a);
            Assert.AreEqual(item.equipmentId, rack.equipment.Single().equipmentId);
            Assert.AreEqual(m_site.records[0].description, rack.description, "the rack note is separate");
            Assert.AreEqual(0, rack.revision);
        }

        [Test]
        public void MultiRuItemIsOneRecordAndRacksListTopFirst()
        {
            var store = NewStore();
            var server = Create(store, m_a, "Server", 20, 21);
            Create(store, m_a, "Patch panel", 42, 42);
            Create(store, m_a, "Shelf", 1, 1);
            Assert.AreEqual(20, server.ruStart);
            Assert.AreEqual(21, server.ruEnd);
            var rack = NewStore().Get(m_a);
            CollectionAssert.AreEqual(new[] { "Patch panel", "Server", "Shelf" }, rack.equipment.Select(e => e.name),
                "RU 1 is the bottom position, so the highest RU is listed first");
            Assert.AreEqual(3, rack.equipment.Count, "a 2U item is one record, not one per rack unit");
            Assert.IsEmpty(NewStore().Get(m_b).equipment, "other racks are unchanged");
        }

        [Test]
        public void RackUnitBoundsAreChecked()
        {
            var store = NewStore();
            foreach (var (start, end) in new[] { (0, 1), (42, 43), (21, 20), (-1, 2) })
                Assert.AreEqual(SaveStatus.Invalid, store.CreateEquipment(m_a, "x", start, end).Status, $"{start}-{end}");
            Assert.AreEqual(SaveStatus.Invalid, store.CreateEquipment(m_a, "   ", 1, 1).Status, "a name is needed");
            Assert.AreEqual(SaveStatus.UnknownRecord, store.CreateEquipment("Rack A1", "x", 1, 1).Status);
            Assert.AreEqual(0, m_storage.WriteCount);
            Assert.AreEqual(SaveStatus.Saved, store.CreateEquipment(m_a, "Top", 42, 42).Status);
            Assert.AreEqual(SaveStatus.Saved, store.CreateEquipment(m_a, "Full height", 1, 42).Status);
        }

        [Test]
        public void OverlapWarnsByDefaultAndBlocksWhenConfigured()
        {
            var store = NewStore();
            Create(store, m_a, "Server", 20, 21);
            var result = store.CreateEquipment(m_a, "Patch panel", 21, 21);
            Assert.AreEqual(SaveStatus.Saved, result.Status);
            StringAssert.Contains("overlaps Server", result.Warnings.Single());
            Assert.IsTrue(store.Get(m_a).equipment.All(e => e.overlaps.Length > 0), "both items show the overlap");
            Assert.AreEqual(SaveStatus.Saved, store.CreateEquipment(m_b, "Elsewhere", 20, 21).Status, "other racks never overlap");

            m_site.authoring.ruOverlap = DemoAuthoringSettings.OverlapBlock;
            var writes = m_storage.WriteCount;
            var blocked = NewStore().CreateEquipment(m_a, "Third", 19, 20);
            Assert.AreEqual(SaveStatus.Overlap, blocked.Status);
            Assert.AreEqual(writes, m_storage.WriteCount);
        }

        [Test]
        public void AddDescriptionIsRecordLocal()
        {
            var store = NewStore();
            var first = Create(store, m_a, "Switch", 40, 40);
            var second = Create(store, m_a, "Server", 20, 21);
            first = SetDescriptions(store, first, ("", "uplinks"), (SerialNumber, "SYN-0001"), ("", ""));
            Assert.AreEqual(3, first.descriptions.Count);
            Assert.AreEqual(first.descriptions.Count, first.descriptions.Select(d => d.descriptionId).Distinct().Count());
            Assert.IsTrue(first.descriptions.All(d => DemoSiteValidator.IsWellFormedId(d.descriptionId, "dsc")));
            Assert.AreEqual(2, first.revision);
            var other = NewStore().GetEquipment(second.equipmentId);
            Assert.AreEqual(1, other.revision, "the other item is untouched");
            Assert.AreEqual("", other.descriptions.Single().text);
            Assert.AreEqual(0, NewStore().Get(m_a).revision, "the rack note is untouched");
        }

        [Test]
        public void ReusedNameKeepsDistinctTextPerItem()
        {
            var store = NewStore();
            var a = SetDescriptions(store, Create(store, m_a, "Switch", 40, 40), (SerialNumber, "SYN-0001"));
            var b = SetDescriptions(store, Create(store, m_c, "Router", 10, 11), (SerialNumber, "SYN-0002"));
            var reopened = NewStore();
            Assert.AreEqual("SYN-0001", reopened.GetEquipment(a.equipmentId).descriptions.Single().text);
            Assert.AreEqual("SYN-0002", reopened.GetEquipment(b.equipmentId).descriptions.Single().text,
                "choosing a name never copies another item's text");
            Assert.AreEqual("Serial number", reopened.GetEquipment(b.equipmentId).descriptions.Single().labelName);
            var serial = reopened.Catalog().labels.Single(l => l.labelId == SerialNumber);
            Assert.AreEqual(2, serial.uses);
            Assert.AreEqual(2, serial.items);
        }

        [Test]
        public void DescriptionIdentityIsIndependentOfOrderAndText()
        {
            var store = NewStore();
            var item = SetDescriptions(store, Create(store, m_a, "Switch", 40, 40), ("", "one"), (SerialNumber, "two"));
            var ids = item.descriptions.Select(d => d.descriptionId).ToArray();
            var draft = DraftOf(item);
            draft.descriptions.Reverse();
            draft.descriptions[0].text = "two, edited";
            Assert.AreEqual(SaveStatus.Saved, store.SaveEquipment(draft).Status);
            var after = NewStore().GetEquipment(item.equipmentId);
            CollectionAssert.AreEqual(new[] { ids[1], ids[0] }, after.descriptions.Select(d => d.descriptionId));
            CollectionAssert.AreEqual(new[] { "two, edited", "one" }, after.descriptions.Select(d => d.text));
            Assert.AreEqual(SerialNumber, after.descriptions[0].labelId);
        }

        [Test]
        public void OnlyEmptyDescriptionsCanBeRemoved()
        {
            var store = NewStore();
            var item = SetDescriptions(store, Create(store, m_a, "Switch", 40, 40), ("", "keep me"), (SerialNumber, ""), ("", "   "));
            var draft = DraftOf(item);
            draft.descriptions.RemoveAt(0);
            var writes = m_storage.WriteCount;
            Assert.AreEqual(SaveStatus.Invalid, store.SaveEquipment(draft).Status, "text is never deleted this way");
            Assert.AreEqual(writes, m_storage.WriteCount);

            draft = DraftOf(item);
            draft.descriptions.RemoveRange(1, 2);
            var result = store.SaveEquipment(draft);
            Assert.AreEqual(SaveStatus.Saved, result.Status, result.Message);
            Assert.AreEqual("keep me", NewStore().GetEquipment(item.equipmentId).descriptions.Single().text);

            draft = DraftOf(NewStore().GetEquipment(item.equipmentId));
            draft.descriptions.Clear();
            Assert.AreEqual(SaveStatus.Invalid, store.SaveEquipment(draft).Status, "an item keeps at least one description");
        }

        [Test]
        public void StaleOrForeignEquipmentEditsAreRefused()
        {
            var store = NewStore();
            var item = Create(store, m_a, "Switch", 40, 40);
            var other = Create(store, m_a, "Server", 20, 21);
            var stale = DraftOf(item);
            SetDescriptions(store, item, ("", "saved in tab 1"));
            stale.descriptions[0].text = "tab 2";
            var writes = m_storage.WriteCount;
            Assert.AreEqual(SaveStatus.Conflict, NewStore().SaveEquipment(stale).Status);
            Assert.AreEqual(writes, m_storage.WriteCount);
            Assert.AreEqual("saved in tab 1", NewStore().GetEquipment(item.equipmentId).descriptions.Single().text);

            var foreign = DraftOf(NewStore().GetEquipment(item.equipmentId));
            foreign.descriptions.Add(new DescriptionDraft { descriptionId = other.descriptions[0].descriptionId, labelId = "", text = "moved?" });
            Assert.AreEqual(SaveStatus.Conflict, store.SaveEquipment(foreign).Status, "a description cannot move between items");
            var unknownName = DraftOf(NewStore().GetEquipment(item.equipmentId));
            unknownName.descriptions[0].labelId = "lbl-00000000-0000-4000-8000-ffffffffffff";
            Assert.AreEqual(SaveStatus.Invalid, store.SaveEquipment(unknownName).Status);
            Assert.AreEqual(writes, m_storage.WriteCount);
        }

        // ============================================================== description names (D039, D041)

        [Test]
        public void CreatingANameReusesAnExistingOneAndChangesNoEquipment()
        {
            var store = NewStore();
            var item = Create(store, m_a, "Switch", 40, 40);
            var same = store.CreateLabel("  serial   NUMBER ");
            Assert.AreEqual(SaveStatus.NoChange, same.Status);
            Assert.AreEqual(SerialNumber, same.LabelId);
            var created = store.CreateLabel("Rack position");
            Assert.AreEqual(SaveStatus.Saved, created.Status, created.Message);
            Assert.IsTrue(DemoSiteValidator.IsWellFormedId(created.LabelId, "lbl"));
            Assert.AreEqual(m_site.labels.Length + 1, NewStore().Catalog().active);
            Assert.AreEqual(1, NewStore().GetEquipment(item.equipmentId).revision, "a new name is not a bulk record edit");
            Assert.AreEqual(SaveStatus.Invalid, store.CreateLabel(" ").Status);
        }

        [Test]
        public void RenameFixesTheSpellingEverywhereWithoutTouchingText()
        {
            var store = NewStore();
            var typo = store.CreateLabel("Serail no").LabelId;
            var a = SetDescriptions(store, Create(store, m_a, "Switch", 40, 40), (typo, "SN-A"), ("", "note"));
            var b = SetDescriptions(store, Create(store, m_c, "Router", 5, 6), (typo, "SN-B"));
            var result = store.RenameLabel(typo, LabelRevision(store, typo), "Serial no.");
            Assert.AreEqual(SaveStatus.Saved, result.Status, result.Message);
            Assert.AreEqual(2, result.Affected);
            var reopened = NewStore();
            var a2 = reopened.GetEquipment(a.equipmentId);
            var b2 = reopened.GetEquipment(b.equipmentId);
            Assert.AreEqual("Serial no.", a2.descriptions[0].labelName);
            Assert.AreEqual("Serial no.", b2.descriptions[0].labelName);
            Assert.AreEqual("SN-A", a2.descriptions[0].text);
            Assert.AreEqual("SN-B", b2.descriptions[0].text);
            Assert.AreEqual(a.descriptions[0].descriptionId, a2.descriptions[0].descriptionId);
            Assert.AreEqual(typo, a2.descriptions[0].labelId, "references follow the name's ID, not its text");
            Assert.AreEqual(a.revision, a2.revision, "a spelling fix changes no equipment record");
            Assert.AreEqual("Serail no", reopened.Catalog().labels.Single(l => l.labelId == typo).previousNames);
        }

        [Test]
        public void RenamingOntoAnotherExistingNameIsRefused()
        {
            var store = NewStore();
            var typo = store.CreateLabel("Serail no").LabelId;
            var writes = m_storage.WriteCount;
            var result = store.RenameLabel(typo, LabelRevision(store, typo), "serial NUMBER");
            Assert.AreEqual(SaveStatus.Collision, result.Status);
            StringAssert.Contains("Replace", result.Message, "the message points to Replace for combining names");
            Assert.AreEqual(writes, m_storage.WriteCount);
            Assert.AreEqual(SaveStatus.Invalid, store.RenameLabel(typo, LabelRevision(store, typo), "  ").Status,
                "blank is not a new name");
        }

        [Test]
        public void RemovingANameWithoutAValidReplacementIsRefusedInTheStore()
        {
            var store = NewStore();
            var item = SetDescriptions(store, Create(store, m_a, "Switch", 40, 40), (SerialNumber, "SYN-0001"));
            var revision = LabelRevision(store, SerialNumber);
            var writes = m_storage.WriteCount;
            foreach (var (id, name) in new[] { ("", ""), ("", "   "), (null, null), (SerialNumber, ""), ("", "Serial Number"),
                         ("lbl-00000000-0000-4000-8000-ffffffffffff", "") })
            {
                var result = store.ReplaceLabel(SerialNumber, revision, id, name);
                Assert.AreNotEqual(SaveStatus.Saved, result.Status, $"replacement ({id}, {name})");
            }
            Assert.AreEqual(SaveStatus.Invalid, store.ReplaceLabel(SerialNumber, revision, "", "").Status);
            Assert.AreEqual(writes, m_storage.WriteCount, "a refused removal writes nothing");
            var after = NewStore();
            Assert.IsFalse(after.Catalog().labels.Single(l => l.labelId == SerialNumber).retired);
            Assert.AreEqual(SerialNumber, after.GetEquipment(item.equipmentId).descriptions.Single().labelId);
        }

        [Test]
        public void AReplacedNameCannotBeTheReplacement()
        {
            var store = NewStore();
            var typo = store.CreateLabel("Serail no").LabelId;
            var other = store.CreateLabel("Asset no.").LabelId;
            var item = SetDescriptions(store, Create(store, m_a, "Switch", 40, 40), (other, "AS-1"));
            Assert.AreEqual(SaveStatus.Saved, store.ReplaceLabel(typo, LabelRevision(store, typo), SerialNumber, "").Status);
            var writes = m_storage.WriteCount;
            var result = store.ReplaceLabel(other, LabelRevision(store, other), typo, "");
            Assert.AreEqual(SaveStatus.Invalid, result.Status, result.Message);
            Assert.AreEqual(writes, m_storage.WriteCount, "nothing is written");
            var after = NewStore();
            Assert.IsFalse(after.Catalog().labels.Single(l => l.labelId == other).retired);
            Assert.AreEqual(other, after.GetEquipment(item.equipmentId).descriptions.Single().labelId);
        }

        [Test]
        public void ReplacementMovesEveryReferenceAndPreservesEveryDescription()
        {
            var store = NewStore();
            var old = store.CreateLabel("Serial no.").LabelId;
            var model = LabelId(store, "Model");
            var a = SetDescriptions(store, Create(store, m_a, "Switch", 40, 40), (old, "SN-A"), (model, "M-A"));
            var b = SetDescriptions(store, Create(store, m_a, "Server", 20, 21), ("", "unnamed"), (old, "SN-B"));
            var c = SetDescriptions(store, Create(store, m_c, "Router", 5, 6), (old, "SN-C"));
            var untouched = Create(store, m_c, "Shelf", 1, 1);
            var before = new[] { a, b, c }.ToDictionary(e => e.equipmentId, e => e.descriptions.Select(d => (d.descriptionId, d.text)).ToArray());

            var result = store.ReplaceLabel(old, LabelRevision(store, old), SerialNumber, "");
            Assert.AreEqual(SaveStatus.Saved, result.Status, result.Message);
            Assert.AreEqual(3, result.Affected);
            Assert.AreEqual(SerialNumber, result.LabelId);

            var reopened = NewStore();
            foreach (var original in new[] { a, b, c })
            {
                var now = reopened.GetEquipment(original.equipmentId);
                CollectionAssert.AreEqual(before[original.equipmentId], now.descriptions.Select(d => (d.descriptionId, d.text)).ToArray(),
                    "same descriptions, same IDs, same order, same text");
                Assert.IsFalse(now.descriptions.Any(d => d.labelId == old));
                Assert.AreEqual(original.revision + 1, now.revision, "open editors of moved items must reopen");
            }
            Assert.AreEqual(model, reopened.GetEquipment(a.equipmentId).descriptions[1].labelId, "other names are untouched");
            Assert.AreEqual(SerialNumber, reopened.GetEquipment(b.equipmentId).descriptions[1].labelId);
            Assert.AreEqual(1, reopened.GetEquipment(untouched.equipmentId).revision);
            var retired = reopened.Catalog().labels.Single(l => l.labelId == old);
            Assert.IsTrue(retired.retired);
            Assert.AreEqual(SerialNumber, retired.replacedByLabelId);
            Assert.AreEqual(3, retired.reassigned);
            Assert.IsFalse(reopened.Catalog().labels.Any(l => !l.retired && l.labelId == old), "the old name leaves the dropdown");
            Assert.AreEqual(3, reopened.Catalog().labels.Single(l => l.labelId == SerialNumber).uses);
            Assert.AreEqual(SaveStatus.Conflict, reopened.ReplaceLabel(old, retired.revision, SerialNumber, "").Status,
                "a retired name cannot be replaced twice");
        }

        [Test]
        public void ReplacementByANewNameCreatesIt()
        {
            var store = NewStore();
            var item = SetDescriptions(store, Create(store, m_a, "Switch", 40, 40), (SerialNumber, "SYN-1"));
            var result = store.ReplaceLabel(SerialNumber, LabelRevision(store, SerialNumber), "", "Serial / service tag");
            Assert.AreEqual(SaveStatus.Saved, result.Status, result.Message);
            var now = NewStore().GetEquipment(item.equipmentId).descriptions.Single();
            Assert.AreEqual("Serial / service tag", now.labelName);
            Assert.AreEqual("SYN-1", now.text);
            Assert.AreEqual(result.LabelId, now.labelId);
        }

        [Test]
        public void CollisionKeepsBothDescriptionsByDefault()
        {
            var store = NewStore();
            var old = store.CreateLabel("Serial no.").LabelId;
            var item = SetDescriptions(store, Create(store, m_a, "Switch", 40, 40), (SerialNumber, "X-1"), (old, "Y-2"));
            var result = store.ReplaceLabel(old, LabelRevision(store, old), SerialNumber, "");
            Assert.AreEqual(SaveStatus.Saved, result.Status, result.Message);
            StringAssert.Contains("Both descriptions are kept", result.Warnings.Single());
            var now = NewStore().GetEquipment(item.equipmentId);
            CollectionAssert.AreEqual(new[] { "X-1", "Y-2" }, now.descriptions.Select(d => d.text), "neither value is overwritten");
            Assert.IsTrue(now.descriptions.All(d => d.labelId == SerialNumber));
            Assert.AreEqual(2, now.descriptions.Select(d => d.descriptionId).Distinct().Count());
        }

        [Test]
        public void CollisionBlocksWhenConfigured()
        {
            m_site.authoring.labelCollision = DemoAuthoringSettings.CollisionBlock;
            var store = NewStore();
            var old = store.CreateLabel("Serial no.").LabelId;
            var item = SetDescriptions(store, Create(store, m_a, "Switch", 40, 40), (SerialNumber, "X-1"), (old, "Y-2"));
            var writes = m_storage.WriteCount;
            var result = store.ReplaceLabel(old, LabelRevision(store, old), SerialNumber, "");
            Assert.AreEqual(SaveStatus.Collision, result.Status);
            StringAssert.Contains("Switch in Rack A1", result.Message);
            Assert.AreEqual(writes, m_storage.WriteCount);
            var now = NewStore();
            Assert.IsFalse(now.Catalog().labels.Single(l => l.labelId == old).retired);
            CollectionAssert.AreEqual(new[] { SerialNumber, old }, now.GetEquipment(item.equipmentId).descriptions.Select(d => d.labelId));
        }

        [Test]
        public void FailedReplacementChangesNothingAndCanBeRetried()
        {
            var store = NewStore();
            var old = store.CreateLabel("Serial no.").LabelId;
            var a = SetDescriptions(store, Create(store, m_a, "Switch", 40, 40), (old, "SN-A"));
            var b = SetDescriptions(store, Create(store, m_c, "Router", 5, 6), (old, "SN-B"));
            var raw = m_storage.Values[Key];
            m_storage.FailWrites = true;
            var result = store.ReplaceLabel(old, LabelRevision(store, old), SerialNumber, "");
            Assert.AreEqual(SaveStatus.StorageError, result.Status);
            StringAssert.Contains("Nothing was changed", result.Message);
            Assert.AreEqual(raw, m_storage.Values[Key], "stored data is exactly as before");
            Assert.AreEqual(old, store.GetEquipment(a.equipmentId).descriptions.Single().labelId, "the page's view is unchanged too");
            Assert.IsFalse(store.Catalog().labels.Single(l => l.labelId == old).retired);
            m_storage.FailWrites = false;
            var retry = store.ReplaceLabel(old, LabelRevision(store, old), SerialNumber, "");
            Assert.AreEqual(SaveStatus.Saved, retry.Status, retry.Message);
            Assert.AreEqual("SN-B", NewStore().GetEquipment(b.equipmentId).descriptions.Single().text);
        }

        [Test]
        public void AnEditorOpenedBeforeAReplacementCannotWriteTheRetiredName()
        {
            var store = NewStore();
            var old = store.CreateLabel("Serial no.").LabelId;
            SetDescriptions(store, Create(store, m_c, "Router", 5, 6), (old, "SN-B"));
            var open = Create(store, m_a, "Switch", 40, 40);       // editor opened; this item does not use the old name yet
            Assert.AreEqual(SaveStatus.Saved, NewStore().ReplaceLabel(old, LabelRevision(store, old), SerialNumber, "").Status);
            var draft = DraftOf(open);
            draft.descriptions[0].labelId = old;                   // chosen from the editor's out-of-date list
            draft.descriptions[0].text = "typed text";
            var writes = m_storage.WriteCount;
            var result = store.SaveEquipment(draft);
            Assert.AreEqual(SaveStatus.Conflict, result.Status);
            StringAssert.Contains("Serial number", result.Message, "the message names the replacement");
            Assert.AreEqual(writes, m_storage.WriteCount);
        }

        [Test]
        public void ExportIsLabelledAndComplete()
        {
            m_storage.SetRaw(LegacyKey, LegacyRaw("2026-11-10T09:00:00Z", (m_a, "A1 note", 1)));
            var store = NewStore();
            store.Save(m_b, "exported edit", 0);
            var old = store.CreateLabel("Serial no.").LabelId;
            var item = SetDescriptions(store, Create(store, m_a, "Switch", 40, 40), ("", "unnamed text"), (old, "SN-1"));
            store.ReplaceLabel(old, LabelRevision(store, old), SerialNumber, "");
            var json = store.ExportJson("http://127.0.0.1:8791", "build-x");
            var export = JsonUtility.FromJson<DemoRecordsExport>(json);
            Assert.AreEqual("vrhe.demo.records-export", export.schema);
            Assert.AreEqual(2, export.schemaVersion);
            StringAssert.StartsWith("LOCAL DEMO DATA", export.notice);
            StringAssert.Contains("never renames, clears or deletes a spreadsheet column", export.mappingNotice);
            Assert.AreEqual(m_site.records.Length, export.records.Count);
            Assert.AreEqual("exported edit", export.records.Single(r => r.recordId == m_b).description);
            Assert.AreEqual("A1 note", export.records.Single(r => r.recordId == m_a).description);
            var exported = export.equipment.Single();
            Assert.AreEqual(item.equipmentId, exported.equipmentId);
            CollectionAssert.AreEqual(new[] { "unnamed text", "SN-1" }, exported.descriptions.Select(d => d.text));
            Assert.AreEqual("Serial number", exported.descriptions[1].labelName);
            Assert.IsTrue(export.labels.Single(l => l.labelId == old).retired, "retired names stay inspectable");
            Assert.AreEqual(DemoRecordStore.MigrationCarried, export.migration.state);
            Assert.AreEqual(LegacyKey, export.storedCopies.Single().key);
            Assert.AreEqual(Key, export.storageKey);
            Assert.AreEqual(42, export.authoring.rackUnitsDefault);
        }
    }
}
