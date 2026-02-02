const statusEl = document.getElementById("status");
const viewOnlyEl = document.getElementById("viewOnly");
const fpsEl = document.getElementById("fps");
const lastActionEl = document.getElementById("lastAction");
const logsEl = document.getElementById("logs");
const screenEl = document.getElementById("screen");

document.getElementById("btnStart").onclick = () => fetch("/api/start", { method: "POST" });
document.getElementById("btnStop").onclick = () => fetch("/api/stop", { method: "POST" });
document.getElementById("btnViewOnly").onclick = () => fetch("/api/toggle_view_only", { method: "POST" });

function setStatus(running) {
  statusEl.textContent = "STATUS: " + (running ? "RUNNING ✅" : "STOPPED 💤");
}

function connectWS() {
  const ws = new WebSocket(`ws://${location.host}/ws`);

  ws.onmessage = (ev) => {
    const d = JSON.parse(ev.data);
    setStatus(d.running);
    viewOnlyEl.textContent = String(d.view_only);
    fpsEl.textContent = (d.fps ?? 0).toFixed(1);
    lastActionEl.textContent = d.last_action ?? "—";
    logsEl.textContent = (d.logs ?? []).join("\n");

    if (d.frame_b64) screenEl.src = "data:image/jpeg;base64," + d.frame_b64;
  };

  ws.onclose = () => {
    statusEl.textContent = "STATUS: DISCONNECTED 🫠 (reconnecting...)";
    setTimeout(connectWS, 800);
  };
}
connectWS();
