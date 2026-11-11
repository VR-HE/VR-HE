// VR-HE interactive browser demo: JSON messages between Unity and the page.
// Unity -> page messages go through DemoBrowser.Post and are handled in demo-ui.js
// (onUnityMessage, switch on "type"). Field names are part of that contract; change both sides
// together. JsonUtility cannot write null objects, so absent records arrive with an empty
// recordId.

using System;
using System.Collections.Generic;
using VRHE.InteractiveDemo.Records;

namespace VRHE.InteractiveDemo
{
    [Serializable]
    sealed class StatusMessage
    {
        public string type = "status";
        public string phase;
        public string text;
        public float progress;
    }

    [Serializable]
    sealed class ErrorMessage
    {
        public string type = "error";
        public string text;
    }

    [Serializable]
    sealed class RecordSummary
    {
        public string recordId;
        public string name;
        public string kind;
        public string location;
        public int revision;
        public string source;
    }

    [Serializable]
    sealed class SiteMessage
    {
        public string type = "site";
        public string siteId;
        public string siteName;
        public string dataNotice;
        public string notice;
        public string storageKey;
        public string storageDescription;
        public string storeStatus;
        public bool readOnly;
        public string build;
        public List<RecordSummary> records = new();
    }

    [Serializable]
    sealed class ReadyMessage
    {
        public string type = "ready";
        public int splats;
        public double loadSeconds;
        public int screenWidth;
        public int screenHeight;
        public string view;
        public string inputSource;
        public bool arrowKeysTurn;
    }

    [Serializable]
    sealed class SelectionMessage
    {
        public string type = "selection";
        public string recordId = "";
        public string anchorId = "";
        public string name = "";
        public string how = "";
    }

    [Serializable]
    sealed class HoverMessage
    {
        public string type = "hover";
        public string recordId = "";
        public string name = "";
    }

    [Serializable]
    sealed class RecordMessage
    {
        public string type;  // "openRecord" or "saveResult"
        public string requestId = "";
        public string how = "";
        public string status = "";
        public string message = "";
        public bool readOnly;
        public string storeStatus = "";
        public DemoRecordView record;
    }

    [Serializable]
    sealed class HudMessage
    {
        public string type = "hud";
        public float fps;
        public float frameMs;
        public int screenWidth;
        public int screenHeight;
        public string view;
    }

    [Serializable]
    sealed class StateMessage
    {
        public string type = "state";
        public string requestId = "";
        public bool ready;
        public bool inputAllowed;
        public string view;
        public float[] feet;
        public float[] camera;
        public float viewYaw;
        public float bodyYaw;
        public float pitch;
        public float heightOffset;
        public float eyeHeight;
        public float orbitDistance;
        public float cameraDistance;
        public string selectedRecordId = "";
        public string hoveredRecordId = "";
        public int screenWidth;
        public int screenHeight;
        public long frame;
        public float lookSpeed;
    }

    [Serializable]
    sealed class ProjectionMessage
    {
        public string type = "projection";
        public string requestId = "";
        public string recordId = "";
        public bool visible;
        public float x;  // Unity screen pixels, origin bottom-left
        public float y;
    }

    [Serializable]
    sealed class PacingMessage
    {
        public string type = "pacing";
        public string requestId = "";
        public PacingStats window;
    }

    [Serializable]
    sealed class FileMessage
    {
        public string type;  // "export" (download + report copy) or "report" (results only)
        public string fileName;
        public string json;
    }

    [Serializable]
    sealed class SaveRequest
    {
        public string recordId;
        public string description;
        public int baseRevision;
        public string requestId;
    }

    [Serializable]
    sealed class UiState
    {
        public bool inputAllowed = true;
        public string panel = "";
        public bool typing;
        public float lookSpeed = 1f;
    }

    [Serializable]
    sealed class BuildInfo
    {
        public string label = "";
        public string commit = "";
        public string builtAt = "";
        public string unityVersion = "";
    }

    [Serializable]
    sealed class SessionEvents
    {
        public int selections;
        public int recordsOpened;
        public int saves;
        public int noChangeSaves;
        public int conflicts;
        public int failedSaves;
        public int exports;
        public int viewToggles;
        public int viewResets;
        public int clears;
    }

    [Serializable]
    sealed class SessionReport
    {
        public string schema = "vrhe.demo.session-report";
        public int schemaVersion = 1;
        public string notice = "Synthetic demo session. Counts and timings only; record text is not included.";
        public string reason;
        public string build;
        public double uptimeSeconds;
        public double loadSeconds;
        public int splats;
        public int screenWidth;
        public int screenHeight;
        public string inputSource;
        public SessionEvents events = new();
        public List<PacingStats> pacing = new();
    }
}
