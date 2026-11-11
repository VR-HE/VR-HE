// VR-HE interactive browser demo: the synthetic site definition (Data/demo-site.json).
//
// Data contract "vrhe.demo.site", schema version 2 (version 1 plus the authoring settings and
// the starter list of description names). The site file is read-only seed data that ships with
// the demo; user edits never change it (they live in DemoRecordStore). It keeps identities
// separate on purpose:
//   recordId  durable identity of a rack record; its rack note and its equipment attach to it.
//   anchorId  identity of one placed selection/collision proxy in the viewer's world.
//   labelId   identity of one starter description name ("Serial number", ...).
//   name      display text only; renaming must not break any link.
// Nothing refers to splat array indexes. The splat is a picture of the room; anchors are aligned
// to it in world coordinates (metres, Unity axes x right / y up / z forward, the same frame as
// Tools/generate_synthetic_splats.py). Tools/check_demo_site.py checks that alignment.
//
// Equipment records are not in the site file: testers add them, and they live in the local
// store with their own IDs (eq-..., dsc-...). The racks' RU capacity and numbering below are
// prototype assumptions, not measurements of the synthetic splat.
//
// Extension point: a production site model would add versions, nested places (room, rack, RU
// range) and several anchors per record (front/rear, cabinet open/closed). Keep recordId as the
// join key when that happens.

using System;
using System.Collections.Generic;
using System.Text.RegularExpressions;
using UnityEngine;

namespace VRHE.InteractiveDemo.Records
{
    [Serializable]
    public sealed class DemoSiteDefinition
    {
        public const string SchemaName = "vrhe.demo.site";
        public const int SupportedSchemaVersion = 2;

        public string schema;
        public int schemaVersion;
        public string siteId;
        public string siteName;
        public string dataNotice;
        public string coordinateFrame;
        public DemoSplatSource splat;
        public DemoSpawn spawn;
        public DemoBox[] obstacles;
        public DemoAnchorDefinition[] anchors;
        public DemoRecordSeed[] records;
        public DemoAuthoringSettings authoring;  // missing -> the defaults in DemoAuthoringSettings
        public DemoLabelSeed[] labels;            // starter description names

        /// <summary>Parses the site file; throws ArgumentException on malformed JSON.</summary>
        public static DemoSiteDefinition FromJson(string json)
        {
            var site = JsonUtility.FromJson<DemoSiteDefinition>(json);
            if (site == null)
                throw new ArgumentException("empty site definition");
            return site;
        }

        /// <summary>The authoring settings in effect (the file's values or the documented defaults).</summary>
        public DemoAuthoringSettings Authoring => authoring ?? new DemoAuthoringSettings();
    }

    [Serializable]
    public sealed class DemoSplatSource
    {
        public string file;   // fixture name served under fixtures/
        public int splats;
        public string source;
    }

    [Serializable]
    public sealed class DemoSpawn
    {
        public float[] feet;  // world position of the player's feet
        public float yawDegrees;
    }

    /// <summary>Axis-aligned box in world space: floor, wall or boundary collider.</summary>
    [Serializable]
    public sealed class DemoBox
    {
        public string name;
        public float[] center;
        public float[] size;
        public bool visibleInSplat;  // false for invisible boundaries at the room's open sides
    }

    [Serializable]
    public sealed class DemoAnchorDefinition
    {
        public string anchorId;
        public string recordId;
        public string kind;
        public float[] center;  // world-space box aligned to the item in the splat
        public float[] size;
        public string frontFacing;
    }

    [Serializable]
    public sealed class DemoRecordSeed
    {
        public string recordId;
        public string kind;
        public string name;
        public string location;
        public string description;  // original rack note (revision 0)
        public int rackUnits;       // RU capacity; 0 = authoring.rackUnitsDefault
    }

    [Serializable]
    public sealed class DemoLabelSeed
    {
        public string labelId;
        public string name;
    }

    /// <summary>
    /// Prototype authoring rules. They are implementation choices for the demo, not user
    /// decisions; each can be changed in the site file without code changes. See the prototype
    /// README for the reasons behind the defaults.
    /// </summary>
    [Serializable]
    public sealed class DemoAuthoringSettings
    {
        public const string NumberingBottomUp = "bottom-up";
        public const string NumberingTopDown = "top-down";
        public const string OverlapWarn = "warn";
        public const string OverlapBlock = "block";
        public const string CollisionKeepBoth = "keep-both";
        public const string CollisionBlock = "block";

        public int rackUnitsDefault = 42;              // a common full-height rack size
        public string ruNumbering = NumberingBottomUp; // display wording only; RU 1 is the bottom position
        public string ruOverlap = OverlapWarn;         // overlapping RU ranges: warn (default) or block
        public string labelCollision = CollisionKeepBoth; // name replacement meets the target name on one item
        public int maxEquipmentPerRack = 50;
        public int maxDescriptionsPerItem = 20;
        public int maxLabels = 100;
        public int maxEquipmentNameLength = 80;
        public int maxLabelNameLength = 60;
    }

    public static class DemoSiteValidator
    {
        // Prefix plus a lower-case UUID, for example rec-9040bad6-d264-4969-b923-a7df2cba2e93.
        static readonly Regex k_id = new("^(site|rec|anc|lbl|eq|dsc)-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$");
        static readonly Regex k_fileName = new("^[A-Za-z0-9_][A-Za-z0-9_.-]{0,120}$");

        public static bool IsWellFormedId(string id, string prefix) =>
            id != null && id.StartsWith(prefix + "-", StringComparison.Ordinal) && k_id.IsMatch(id);

        /// <summary>Every problem found; an empty list means the site can be used.</summary>
        public static List<string> Validate(DemoSiteDefinition site)
        {
            var problems = new List<string>();
            if (site == null)
            {
                problems.Add("no site definition");
                return problems;
            }
            if (site.schema != DemoSiteDefinition.SchemaName)
                problems.Add($"schema is '{site.schema}', expected '{DemoSiteDefinition.SchemaName}'");
            if (site.schemaVersion != DemoSiteDefinition.SupportedSchemaVersion)
                problems.Add($"schemaVersion {site.schemaVersion} is not supported (expected {DemoSiteDefinition.SupportedSchemaVersion})");
            if (!IsWellFormedId(site.siteId, "site"))
                problems.Add($"siteId '{site.siteId}' is not a site-<uuid> identifier");
            if (site.splat == null || string.IsNullOrEmpty(site.splat.file) || !k_fileName.IsMatch(site.splat.file))
                problems.Add("splat.file must be a plain file name");
            if (site.spawn == null || !IsVector(site.spawn.feet))
                problems.Add("spawn.feet must have three numbers");

            var authoring = site.Authoring;
            if (authoring.rackUnitsDefault < 1 || authoring.rackUnitsDefault > 100)
                problems.Add("authoring.rackUnitsDefault must be 1-100");
            if (authoring.ruNumbering != DemoAuthoringSettings.NumberingBottomUp && authoring.ruNumbering != DemoAuthoringSettings.NumberingTopDown)
                problems.Add("authoring.ruNumbering must be 'bottom-up' or 'top-down'");
            if (authoring.ruOverlap != DemoAuthoringSettings.OverlapWarn && authoring.ruOverlap != DemoAuthoringSettings.OverlapBlock)
                problems.Add("authoring.ruOverlap must be 'warn' or 'block'");
            if (authoring.labelCollision != DemoAuthoringSettings.CollisionKeepBoth && authoring.labelCollision != DemoAuthoringSettings.CollisionBlock)
                problems.Add("authoring.labelCollision must be 'keep-both' or 'block'");
            if (authoring.maxEquipmentPerRack < 1 || authoring.maxDescriptionsPerItem < 1 || authoring.maxLabels < 1 ||
                authoring.maxEquipmentNameLength < 1 || authoring.maxLabelNameLength < 1)
                problems.Add("authoring limits must be positive");

            var records = new HashSet<string>();
            foreach (var record in site.records ?? Array.Empty<DemoRecordSeed>())
            {
                if (record == null || !IsWellFormedId(record.recordId, "rec"))
                    problems.Add($"record id '{record?.recordId}' is not a rec-<uuid> identifier");
                else if (!records.Add(record.recordId))
                    problems.Add($"duplicate recordId {record.recordId}");
                if (record != null && string.IsNullOrWhiteSpace(record.name))
                    problems.Add($"record {record.recordId} has no name");
                if (record != null && (record.rackUnits < 0 || record.rackUnits > 100))
                    problems.Add($"record {record.recordId} rackUnits must be 0 (default) or 1-100");
            }
            if (records.Count == 0)
                problems.Add("the site has no records");

            var anchors = new HashSet<string>();
            foreach (var anchor in site.anchors ?? Array.Empty<DemoAnchorDefinition>())
            {
                if (anchor == null || !IsWellFormedId(anchor.anchorId, "anc"))
                {
                    problems.Add($"anchor id '{anchor?.anchorId}' is not an anc-<uuid> identifier");
                    continue;
                }
                if (!anchors.Add(anchor.anchorId))
                    problems.Add($"duplicate anchorId {anchor.anchorId}");
                if (!records.Contains(anchor.recordId))
                    problems.Add($"anchor {anchor.anchorId} points to unknown record {anchor.recordId}");
                if (!IsVector(anchor.center) || !IsPositiveVector(anchor.size))
                    problems.Add($"anchor {anchor.anchorId} needs a center and a positive size");
            }
            foreach (var box in site.obstacles ?? Array.Empty<DemoBox>())
                if (box == null || !IsVector(box.center) || !IsPositiveVector(box.size))
                    problems.Add($"obstacle '{box?.name}' needs a center and a positive size");

            var labelIds = new HashSet<string>();
            var labelNames = new HashSet<string>();
            foreach (var label in site.labels ?? Array.Empty<DemoLabelSeed>())
            {
                if (label == null || !IsWellFormedId(label.labelId, "lbl"))
                {
                    problems.Add($"label id '{label?.labelId}' is not a lbl-<uuid> identifier");
                    continue;
                }
                if (!labelIds.Add(label.labelId))
                    problems.Add($"duplicate labelId {label.labelId}");
                var clean = DemoRecordStore.CleanName(label.name, authoring.maxLabelNameLength, out var nameProblem);
                if (nameProblem != null)
                    problems.Add($"label {label.labelId}: {nameProblem}");
                else if (!labelNames.Add(DemoRecordStore.NameKey(clean)))
                    problems.Add($"duplicate label name '{clean}'");
            }
            if (labelIds.Count > authoring.maxLabels)
                problems.Add("more starter labels than authoring.maxLabels");
            return problems;
        }

        static bool IsVector(float[] v) => v != null && v.Length == 3 && !float.IsNaN(v[0] + v[1] + v[2]) &&
                                           !float.IsInfinity(v[0] + v[1] + v[2]);

        static bool IsPositiveVector(float[] v) => IsVector(v) && v[0] > 0 && v[1] > 0 && v[2] > 0;
    }
}
