import { requestJSON, uploadImage } from "/api.mjs";
import { getLanguage, pickLanguage, setLanguage, t } from "/i18n.mjs";

const $ = (id) => document.getElementById(id);
function savedLanguage() { try { return localStorage.getItem("snappaste-lang"); } catch { return null; } }
setLanguage(pickLanguage({ search: location.search, saved: savedLanguage(),
  languages: navigator.languages?.length ? navigator.languages : [navigator.language || ""] }));
const token = new URLSearchParams(location.hash.slice(1)).get("token") || "";
let selected = null;
let previewURL = null;
let selectionVersion = 0;
let connected = false;
let busy = false;
let maxBytes = 25 * 1024 * 1024;
let maxEdge = 1920;
let dryRun = false;
// Text that depends on state is kept as keys, so switching language can redraw it.
let result = { key: "choose_and_check", params: {}, state: "" };
let connection = { title: "checking", detail: "checking_detail", raw: "" };

function message(key, state = "", params = {}) { result = { key, params, state }; showResult(); }
function showResult() {
  $("result").textContent = result.raw ?? t(result.key, result.params);
  $("result").className = `result ${result.state}`;
}
// Server and network messages arrive already in the interface language.
function rawMessage(text, state) { result = { raw: text, state }; showResult(); }

function showConnection() {
  $("connectionTitle").textContent = t(connection.title);
  $("connectionDetail").textContent = connection.raw || t(connection.detail, { mib: Math.round(maxBytes / 1024 / 1024) });
}

function showPasteNote() {
  $("pasteTitle").textContent = t(dryRun ? "dry_run_paste_title" : "paste_title");
  const note = $("pasteNote");
  if (dryRun) { note.textContent = t("dry_run_paste_note"); return; }
  const key = (name) => { const element = document.createElement("kbd"); element.textContent = name; return element; };
  const gap = getLanguage() === "ja" ? "" : " ";
  note.replaceChildren(`${t("paste_before")} `, key("Ctrl"), " + ", key("V"), `${gap}${t("paste_after")}`);
}

function applyText() {
  document.documentElement.lang = getLanguage();
  document.title = t("page_title");
  for (const element of document.querySelectorAll("[data-i18n]")) element.textContent = t(element.dataset.i18n);
  for (const element of document.querySelectorAll("[data-i18n-attr]")) {
    for (const pair of element.dataset.i18nAttr.split(";")) {
      const [attribute, name] = pair.split(":");
      element.setAttribute(attribute, t(name));
    }
  }
  $("lang").textContent = t("switch_language");
  $("lang").setAttribute("lang", getLanguage() === "ja" ? "en" : "ja");
  $("processingNote").textContent = t("processing_note", { edge: maxEdge });
  if (!selected) $("selectionDetail").textContent = t("no_photo");
  showConnection(); showPasteNote(); showResult(); updateControls();
}

function updateControls() {
  $("send").disabled = !selected || !connected || busy;
  $("cameraInput").disabled = busy;
  $("galleryInput").disabled = busy;
  $("clear").disabled = busy;
  $("reconnect").disabled = busy;
  $("sendLabel").textContent = busy ? t("sending_label") : t("send");
}

function clearSelection() {
  selectionVersion += 1;
  selected = null;
  if (previewURL) URL.revokeObjectURL(previewURL);
  previewURL = null;
  $("previewImage").removeAttribute("src");
  $("previewImage").hidden = true;
  $("placeholder").hidden = false;
  $("clear").hidden = true;
  $("selectionDetail").textContent = t("no_photo");
  $("cameraInput").value = "";
  $("galleryInput").value = "";
  updateControls();
}

function selectPhoto(event) {
  const file = event.target.files[0];
  if (!file || busy) return;
  clearSelection();
  if (!file.size || file.size > maxBytes) {
    message("size_limit", "error", { mib: Math.round(maxBytes / 1024 / 1024) });
    return;
  }
  const version = selectionVersion;
  previewURL = URL.createObjectURL(file);
  const image = $("previewImage");
  image.onload = () => {
    if (version !== selectionVersion) return;
    selected = file;
    image.hidden = false;
    $("placeholder").hidden = true;
    $("clear").hidden = false;
    $("selectionDetail").textContent = `${image.naturalWidth} × ${image.naturalHeight}px · ${(file.size / 1024 / 1024).toFixed(1)}MiB`;
    message("check_then_send");
    updateControls();
  };
  image.onerror = () => {
    if (version !== selectionVersion) return;
    clearSelection();
    message("preview_failed", "error");
  };
  image.src = previewURL;
  message("loading_preview", "busy");
}

async function connect() {
  connected = false;
  connection = { title: "checking", detail: "checking_detail", raw: "" };
  showConnection();
  $("connectionDot").className = "status-dot";
  updateControls();
  try {
    const status = await requestJSON("/api/status", token);
    connected = true;
    maxBytes = status.max_bytes;
    maxEdge = status.max_edge;
    dryRun = status.mode === "dry-run";
    connection = { title: "connected", detail: "host_running", raw: "" };
    $("connectionDot").className = "status-dot connected";
    $("dryRun").hidden = !dryRun;
    $("processingNote").textContent = t("processing_note", { edge: maxEdge });
    showPasteNote();
  } catch (error) {
    connection = { title: "cannot_connect", detail: "", raw: error.message };
    $("connectionDot").className = "status-dot error";
    rawMessage(error.message, "error");
  }
  showConnection();
  updateControls();
}

$("lang").addEventListener("click", () => {
  setLanguage(getLanguage() === "ja" ? "en" : "ja");
  try { localStorage.setItem("snappaste-lang", getLanguage()); } catch {}
  applyText();
});
$("cameraInput").addEventListener("change", selectPhoto);
$("galleryInput").addEventListener("change", selectPhoto);
$("clear").addEventListener("click", () => {
  clearSelection();
  message("choose_and_check");
});
$("reconnect").addEventListener("click", connect);
$("send").addEventListener("click", async () => {
  if (!selected || !connected || busy) return;
  busy = true;
  updateControls();
  message("sending", "busy");
  try {
    const response = await uploadImage(selected, token);
    $("dryRun").hidden = !response.dry_run;
    rawMessage(`${response.message} (${response.width} × ${response.height}px)`, response.dry_run ? "" : "success");
  } catch (error) {
    rawMessage(error.message, "error");
  } finally {
    busy = false;
    updateControls();
  }
});
window.addEventListener("pagehide", () => { if (previewURL) URL.revokeObjectURL(previewURL); });
applyText();
connect();
