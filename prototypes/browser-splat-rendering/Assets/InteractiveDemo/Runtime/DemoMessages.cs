// VR-HE interactive browser demo: JSON messages between Unity and the page.
// Unity -> page messages go through DemoBrowser.Post and are handled in demo-ui.js
// (onUnityMessage, switch on "type"). Field names are part of that contract; change both sides
// together. JsonUtility cannot write null objects, so absent records arrive with an empty
// recordId (racks) or equipmentId (equipment). The record, equipment and name views themselves
// are defined in Records/DemoRecordModel.cs.

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
        public int revision;      // rack note revision
        public string source;     // rack note: "seed" or "local edit"
        public int rackUnits;
        public List<EquipmentSummary> equipment = new();  // top of the rack first
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
        public string legacyStorageKey;   // the first demo's key, read for migration only
        public bool persisted;            // the current format has been written in this profile
        public StoredMigration migration;
        public DemoAuthoringSettings authoring;
        public int activeNames;
        public int equipmentCount;
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

    /// <summary>Reply to JsAuthoring: the outcome plus the current views the page needs to redraw.</summary>
    [Serializable]
    sealed class AuthoringMessage
    {
        public string type = "authoring";
        public string requestId = "";
        public string op = "";
        public string status = "";      // a SaveStatus name, or "Opened" for openEquipment/catalog
        public string message = "";
        public List<string> warnings = new();
        public bool readOnly;
        public string storeStatus = "";
        public string equipmentId = "";
        public string labelId = "";
        public int affected;
        public DemoRecordView rack;      // the rack involved, if any (empty recordId otherwise)
        public EquipmentView equipment;  // the item involved as stored now (empty equipmentId otherwise)
        public CatalogView catalog;      // always the current list of description names
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

    /// <summary>
    /// Page -> Unity authoring command. op: openEquipment | catalog | createEquipment |
    /// saveEquipment | createLabel | renameLabel | replaceLabel. Every rule is enforced in
    /// DemoRecordStore; the page's disabled buttons are convenience only.
    /// </summary>
    [Serializable]
    sealed class AuthoringRequest
    {
        public string op;
        public string requestId;
        public string recordId;            // createEquipment: the rack
        public string equipmentId;         // openEquipment
        public string name;                // createEquipment, createLabel, renameLabel (the new spelling)
        public int ruStart;
        public int ruEnd;
        public EquipmentDraft draft;       // saveEquipment
        public string labelId;             // renameLabel, replaceLabel: the name being changed
        public int baseRevision;           // renameLabel, replaceLabel: that name's revision when shown
        public string replacementLabelId;  // replaceLabel: an existing name ...
        public string replacementName;     // ... or a new name (exactly one of the two)
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
        public int equipmentOpened;
        public int equipmentAdded;
        public int equipmentSaved;
        public int namesAdded;
        public int namesRenamed;
        public int namesReplaced;
        public int authoringNoChange;
        public int authoringConflicts;
        public int authoringRefused;      // a rule said no (invalid input, name clash, overlap block, read-only)
        public int authoringStorageErrors;
    }

    [Serializable]
    sealed class SessionReport
    {
        public string schema = "vrhe.demo.session-report";
        public int schemaVersion = 2;  // 2: equipment and description-name counts
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
