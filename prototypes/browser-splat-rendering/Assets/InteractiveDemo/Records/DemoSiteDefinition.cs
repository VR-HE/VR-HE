// VR-HE interactive browser demo: the synthetic site definition (Data/demo-site.json).
//
// Data contract "vrhe.demo.site", schema version 1. The site file is read-only seed data that
// ships with the demo; user edits never change it (they live in DemoRecordStore). It keeps three
// identities separate on purpose:
//   recordId  durable identity of an equipment record; descriptions and edits attach to it.
//   anchorId  identity of one placed selection/collision proxy in the viewer's world.
//   name      display label only; renaming must not break either link.
// Nothing refers to splat array indexes. The splat is a picture of the room; anchors are aligned
// to it in world coordinates (metres, Unity axes x right / y up / z forward, the same frame as
// Tools/generate_synthetic_splats.py). Tools/check_demo_site.py checks that alignment.
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
        public const int SupportedSchemaVersion = 1;

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

        /// <summary>Parses the site file; throws ArgumentException on malformed JSON.</summary>
        public static DemoSiteDefinition FromJson(string json)
        {
            var site = JsonUtility.FromJson<DemoSiteDefinition>(json);
            if (site == null)
                throw new ArgumentException("empty site definition");
            return site;
        }
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
        public string description;  // original demo text (revision 0)
    }

    public static class DemoSiteValidator
    {
        // Prefix plus a lower-case UUID, for example rec-9040bad6-d264-4969-b923-a7df2cba2e93.
        static readonly Regex k_id = new("^(site|rec|anc)-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$");
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

            var records = new HashSet<string>();
            foreach (var record in site.records ?? Array.Empty<DemoRecordSeed>())
            {
                if (record == null || !IsWellFormedId(record.recordId, "rec"))
                    problems.Add($"record id '{record?.recordId}' is not a rec-<uuid> identifier");
                else if (!records.Add(record.recordId))
                    problems.Add($"duplicate recordId {record.recordId}");
                if (record != null && string.IsNullOrWhiteSpace(record.name))
                    problems.Add($"record {record.recordId} has no name");
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
            return problems;
        }

        static bool IsVector(float[] v) => v != null && v.Length == 3 && !float.IsNaN(v[0] + v[1] + v[2]) &&
                                           !float.IsInfinity(v[0] + v[1] + v[2]);

        static bool IsPositiveVector(float[] v) => IsVector(v) && v[0] > 0 && v[1] > 0 && v[2] > 0;
    }
}
