import React, { useState, useEffect } from "react";
import { RefreshCw, ExternalLink, Server, AlertTriangle } from "lucide-react";

export function LiveAnprStream() {
  const [anprUrl, setAnprUrl] = useState("http://127.0.0.1:5000");
  const [customUrl, setCustomUrl] = useState("");
  const [isOnline, setIsOnline] = useState(false);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    const check = () => {
      fetch("http://127.0.0.1:5000/plates_json")
        .then((r) => setIsOnline(r.ok))
        .catch(() => setIsOnline(false))
        .finally(() => setIsChecking(false));
    };
    check();
    const interval = setInterval(check, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleConnect = () => {
    if (customUrl.trim()) {
      setAnprUrl(customUrl.trim().replace(/\/+$/, ""));
      setCustomUrl("");
    }
  };

  return (
    <div className="live-anpr-container">
      <div className="live-anpr-header" style={{ marginBottom: "1rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <Server size={20} style={{ color: "var(--accent-amber)" }} />
          <h2 style={{ margin: 0, fontSize: "1.2rem", fontWeight: 700 }}>Live ANPR Stream</h2>
          <span
            style={{
              padding: "3px 10px",
              borderRadius: "12px",
              fontSize: "11px",
              fontWeight: 600,
              background: isOnline ? "rgba(16,185,129,0.15)" : "rgba(239,68,68,0.15)",
              color: isOnline ? "#6EE7B7" : "#FCA5A5",
              border: `1px solid ${isOnline ? "rgba(16,185,129,0.4)" : "rgba(239,68,68,0.4)"}`,
            }}
          >
            {isOnline ? "STREAM ONLINE" : "STREAM OFFLINE"}
          </span>
        </div>
        <p style={{ margin: "4px 0 0", fontSize: "13px", color: "var(--text-muted)" }}>
          Powered by <code style={{ color: "var(--accent-amber)" }}>stream_anpr.py</code> — YOLOv8 plate detection + EasyOCR text recognition on the server.
        </p>
      </div>

      {!isOnline && (
        <div className="live-anpr-error-banner">
          <AlertTriangle size={18} style={{ color: "#EF4444", flexShrink: 0 }} />
          <span>
            Standalone ANPR stream dashboard not reachable at {anprUrl}. Start it with:{" "}
            <code>python stream_anpr.py --port 5000</code>
          </span>
          <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
            <input
              type="text"
              placeholder="http://127.0.0.1:5000"
              value={customUrl}
              onChange={(e) => setCustomUrl(e.target.value)}
              style={{
                flex: 1,
                minWidth: "200px",
                padding: "6px 12px",
                background: "rgba(255,255,255,0.08)",
                border: "1px solid rgba(255,255,255,0.25)",
                borderRadius: "5px",
                color: "#F9FAFB",
                fontSize: "12px",
                fontFamily: "monospace",
              }}
            />
            <button
              type="button"
              onClick={handleConnect}
              style={{
                padding: "6px 16px",
                background: "#059669",
                color: "#FFFFFF",
                border: "none",
                borderRadius: "5px",
                fontSize: "12px",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              Connect
            </button>
            <button
              type="button"
              onClick={() => window.open(anprUrl, "_blank")}
              style={{
                padding: "6px 12px",
                background: "transparent",
                color: "#9CA3AF",
                border: "1px solid rgba(255,255,255,0.15)",
                borderRadius: "5px",
                fontSize: "12px",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "4px",
              }}
              title="Open in new tab"
            >
              <ExternalLink size={13} />
            </button>
          </div>
        </div>
      )}

      <div style={{ position: "relative", height: "85vh" }}>
        {isChecking && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              background: "rgba(0,0,0,0.5)",
              zIndex: 10,
            }}
          >
            <RefreshCw size={20} className="icon-spin text-amber" />
          </div>
        )}
        <iframe
          src={anprUrl}
          title="ANPR Stream Dashboard"
          style={{
            width: "100%",
            height: "100%",
            border: "none",
            borderRadius: "8px",
            background: "#000",
          }}
          sandbox="allow-scripts allow-same-origin"
        />
      </div>

      <div
        style={{
          marginTop: "12px",
          padding: "8px 14px",
          background: "rgba(0,0,0,0.3)",
          borderRadius: "6px",
          fontSize: "12px",
          color: "var(--text-muted)",
          display: "flex",
          alignItems: "center",
          gap: "8px",
          flexWrap: "wrap",
        }}
      >
        <span>
          <strong style={{ color: "var(--text-primary)" }}>stream_anpr.py</strong> —
          Live camera feed with YOLOv8 plate detection + EasyOCR. Detected plates auto-refresh every 3s.
        </span>
        <span style={{ marginLeft: "auto", color: "var(--accent-amber)" }}>
          Press <kbd style={{ background: "rgba(255,255,255,0.1)", padding: "1px 6px", borderRadius: "3px", fontFamily: "monospace" }}>Ctrl+C</kbd> in terminal to stop
        </span>
      </div>
    </div>
  );
}