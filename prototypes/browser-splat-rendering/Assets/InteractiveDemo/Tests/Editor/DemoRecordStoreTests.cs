// VR-HE interactive browser demo: EditMode tests for record identity and local persistence.
// They exercise DemoRecordStore against in-memory storage; real browser storage, reloads and
// relaunches are checked separately in real browsers (Tools/verify_interactive_demo.py).

using System;
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
        string m_a, m_b;

        [SetUp]
        public void SetUp()
        {
            m_site = DemoSiteDefinition.FromJson(File.ReadAllText(k_sitePath));
            m_storage = new InMemoryKeyValueStorage();
            m_now = new DateTime(2026, 11, 10, 12, 0, 0, DateTimeKind.Utc);
            m_a = m_site.records[0].recordId;
            m_b = m_site.records[1].recordId;
        }

        DemoRecordStore NewStore() => new(m_site, m_storage, () => m_now);
        string Key => DemoRecordStore.StorageKeyFor(m_site.siteId);

        [Test]
        public void ShippedSiteFileIsValid()
        {
            var problems = DemoSiteValidator.Validate(m_site);
            Assert.IsEmpty(problems, string.Join("\n", problems));
            Assert.GreaterOrEqual(m_site.anchors.Length, 2, "the task needs at least two selectable items");
            foreach (var anchor in m_site.anchors)
                Assert.AreNotEqual(anchor.anchorId, anchor.recordId);
        }

        [Test]
        public void IdentifiersAreFrozen()
        {
            // These identifiers are the durable link between saved descriptions and records.
            // Changing them orphans every tester's saved edits; add new records instead.
            Assert.AreEqual("site-bfaaec37-26c3-4ca9-99f2-b1fb9de68f5a", m_site.siteId);
            Assert.AreEqual("rec-9040bad6-d264-4969-b923-a7df2cba2e93", m_site.records[0].recordId);
            Assert.AreEqual("rec-a9955c73-733d-4e06-8b70-e03eead46856", m_site.records[1].recordId);
            Assert.AreEqual("anc-836007b1-09cd-41f9-82e8-52da9a18fe75", m_site.anchors[0].anchorId);
            Assert.AreEqual("vrhe.demo.records.v1.site-bfaaec37-26c3-4ca9-99f2-b1fb9de68f5a", Key);
        }

        [Test]
        public void ValidatorRejectsBrokenLinksAndDuplicates()
        {
            m_site.anchors[1].recordId = "rec-00000000-0000-0000-0000-000000000000";
            m_site.records[2].recordId = m_site.records[3].recordId;
            m_site.anchors[4].anchorId = "Rack A1";
            var problems = DemoSiteValidator.Validate(m_site);
            Assert.IsTrue(problems.Any(p => p.Contains("unknown record")));
            Assert.IsTrue(problems.Any(p => p.Contains("duplicate recordId")));
            Assert.IsTrue(problems.Any(p => p.Contains("anc-<uuid>")));
        }

        [Test]
        public void EmptyStorageShowsSeedText()
        {
            var store = NewStore();
            var view = store.Get(m_a);
            Assert.AreEqual(m_site.records[0].description, view.description);
            Assert.AreEqual(0, view.revision);
            Assert.AreEqual(DemoRecordStore.SourceSeed, view.source);
            Assert.AreEqual(m_site.anchors[0].anchorId, view.anchorIds.Single());
            Assert.IsFalse(store.IsReadOnly);
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
            m_storage.SetRaw(Key, "{\"schema\":\"vrhe.demo.local-records\",\"schemaVersion\":1,\"siteId\":\"" + m_site.siteId +
                                  "\",\"entries\":[{\"recordId\":\"rec-11111111-2222-3333-4444-555555555555\",\"description\":\"future\",\"revision\":4,\"updatedAt\":\"2026-11-09T00:00:00Z\"}]}");
            var store = NewStore();
            Assert.AreEqual(SaveStatus.Saved, store.Save(m_a, "edit", 0).Status);
            var export = store.BuildExport("http://127.0.0.1:8791", "test");
            Assert.AreEqual(1, export.unmatchedStoredEntries.Count);
            Assert.AreEqual("future", export.unmatchedStoredEntries[0].description);
            StringAssert.Contains("rec-11111111-2222-3333-4444-555555555555", m_storage.Values[Key]);
        }

        [Test]
        public void NewerSchemaIsReadOnlyAndNeverRewritten()
        {
            var raw = "{\"schema\":\"vrhe.demo.local-records\",\"schemaVersion\":2,\"entries\":[]}";
            m_storage.SetRaw(Key, raw);
            var store = NewStore();
            Assert.IsTrue(store.IsReadOnly);
            Assert.AreEqual(SaveStatus.ReadOnly, store.Save(m_a, "edit", 0).Status);
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
        }

        [Test]
        public void DescriptionsAreSanitizedAndLimited()
        {
            var clean = DemoRecordStore.Sanitize("a\r\nb\rc\u0000d\te\u0007\ud800", out var tooLong);
            Assert.IsFalse(tooLong);
            Assert.AreEqual("a\nb\ncd\te�", clean);
            Assert.AreEqual("😀", DemoRecordStore.Sanitize("😀", out _), "valid pairs are kept");

            var store = NewStore();
            var exact = new string('x', DemoRecordStore.MaxDescriptionLength);
            Assert.AreEqual(SaveStatus.Saved, store.Save(m_a, exact, 0).Status);
            Assert.AreEqual(SaveStatus.Invalid, store.Save(m_a, exact + "y", 1).Status);
            Assert.AreEqual(exact, store.Get(m_a).description);
        }

        [Test]
        public void ExportIsLabelledAndComplete()
        {
            var store = NewStore();
            store.Save(m_b, "exported edit", 0);
            var json = store.ExportJson("http://127.0.0.1:8791", "build-x");
            var export = JsonUtility.FromJson<DemoRecordsExport>(json);
            Assert.AreEqual("vrhe.demo.records-export", export.schema);
            Assert.AreEqual(1, export.schemaVersion);
            StringAssert.StartsWith("LOCAL DEMO DATA", export.notice);
            Assert.AreEqual(m_site.records.Length, export.records.Count);
            var b = export.records.Single(r => r.recordId == m_b);
            Assert.AreEqual("exported edit", b.description);
            Assert.AreEqual(DemoRecordStore.SourceLocalEdit, b.source);
            Assert.AreEqual(DemoRecordStore.SourceSeed, export.records.Single(r => r.recordId == m_a).source);
            Assert.AreEqual(Key, export.storageKey);
        }

        [Test]
        public void ClearRemovesOnlyThisSitesKey()
        {
            m_storage.SetRaw("unrelated.key", "keep me");
            var store = NewStore();
            store.Save(m_a, "edit", 0);
            Assert.IsTrue(store.Clear(out _));
            Assert.IsFalse(m_storage.Values.ContainsKey(Key));
            Assert.AreEqual("keep me", m_storage.Values["unrelated.key"]);
            Assert.AreEqual(m_site.records[0].description, store.Get(m_a).description);
            Assert.AreEqual(0, NewStore().Get(m_a).revision);
        }
    }
}
