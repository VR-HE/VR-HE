// VR-HE interactive browser demo: storage seam for the local record store.
//
// The browser build implements this over window.localStorage (DemoBrowser.cs); tests use the
// in-memory version below. A later backend or spreadsheet adapter would not implement this
// interface: it needs per-record operations, identity mapping and conflict policy, which are
// still open decisions (docs/SPREADSHEET_SYNC.md). This seam only stores the demo's one document.

using System.Collections.Generic;

namespace VRHE.InteractiveDemo.Records
{
    public interface IKeyValueStorage
    {
        /// <summary>Plain-language description of where values live, shown to the user.</summary>
        string Description { get; }

        /// <summary>True when the read worked; value is null when the key does not exist.</summary>
        bool TryRead(string key, out string value, out string error);

        bool TryWrite(string key, string value, out string error);

        bool TryRemove(string key, out string error);
    }

    /// <summary>Dictionary-backed storage for tests and Editor play mode; can simulate failures.</summary>
    public sealed class InMemoryKeyValueStorage : IKeyValueStorage
    {
        readonly Dictionary<string, string> m_values = new();

        public string Description => "in-memory test storage";
        public bool FailReads { get; set; }
        public bool FailWrites { get; set; }
        public int WriteCount { get; private set; }
        public IReadOnlyDictionary<string, string> Values => m_values;

        public bool TryRead(string key, out string value, out string error)
        {
            value = null;
            error = null;
            if (FailReads)
            {
                error = "simulated read failure";
                return false;
            }
            m_values.TryGetValue(key, out value);
            return true;
        }

        public bool TryWrite(string key, string value, out string error)
        {
            error = null;
            if (FailWrites)
            {
                error = "simulated write failure (for example a full or blocked storage area)";
                return false;
            }
            m_values[key] = value;
            WriteCount++;
            return true;
        }

        public bool TryRemove(string key, out string error)
        {
            error = null;
            if (FailWrites)
            {
                error = "simulated write failure";
                return false;
            }
            m_values.Remove(key);
            return true;
        }

        /// <summary>Test helper: put a raw value in place, as another tab or an older page would.</summary>
        public void SetRaw(string key, string value) => m_values[key] = value;
    }
}
