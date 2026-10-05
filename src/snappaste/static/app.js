import { requestJSON, uploadImage } from "/api.mjs";

const $ = (id) => document.getElementById(id);
const token = new URLSearchParams(location.hash.slice(1)).get("token") || "";
let selected = null;
let previewURL = null;
let selectionVersion = 0;
let connected = false;
let busy = false;
let maxBytes = 25 * 1024 * 1024;

function message(text, state = "") {
  $("result").textContent = text;
  $("result").className = `result ${state}`;
}

function updateControls() {
  $("send").disabled = !selected || !connected || busy;
  $("cameraInput").disabled = busy;
  $("galleryInput").disabled = busy;
  $("clear").disabled = busy;
  $("reconnect").disabled = busy;
  $("sendLabel").textContent = busy ? "送信・画像処理中…" : "PCへ送信する";
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
  $("selectionDetail").textContent = "写真はまだ選ばれていません";
  $("cameraInput").value = "";
  $("galleryInput").value = "";
  updateControls();
}

function selectPhoto(event) {
  const file = event.target.files[0];
  if (!file || busy) return;
  clearSelection();
  if (!file.size || file.size > maxBytes) {
    message(`画像の容量は${Math.round(maxBytes / 1024 / 1024)}MiB以内にしてください。`, "error");
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
    message("写真を確認したら、「PCへ送信する」を押してください。");
    updateControls();
  };
  image.onerror = () => {
    if (version !== selectionVersion) return;
    clearSelection();
    message("プレビューを開けません。JPEG・PNG・WebPを選んでください。HEICはJPEGへ変換してください。", "error");
  };
  image.src = previewURL;
  message("プレビューを読み込んでいます…", "busy");
}

async function connect() {
  connected = false;
  $("connectionTitle").textContent = "接続を確認中";
  $("connectionDot").className = "status-dot";
  updateControls();
  try {
    const status = await requestJSON("/api/status", token);
    connected = true;
    maxBytes = status.max_bytes;
    $("connectionTitle").textContent = "PCに接続しました";
    $("connectionDetail").textContent = `受信ホストが起動中 · 上限${Math.round(maxBytes / 1024 / 1024)}MiB`;
    $("connectionDot").className = "status-dot connected";
    $("dryRun").hidden = status.mode !== "dry-run";
    if (status.mode === "dry-run") {
      $("pasteTitle").textContent = "画像処理の確認";
      $("pasteNote").textContent = "このモードではクリップボードを更新しません。貼り付けの確認にはWindowsの通常モードで起動してください。";
    }
    $("processingNote").textContent = `向きを補正し、長辺${status.max_edge}px以内に縮小します。メタデータを除去し、透過部分は白背景になります。`;
  } catch (error) {
    $("connectionTitle").textContent = "接続できません";
    $("connectionDetail").textContent = error.message;
    $("connectionDot").className = "status-dot error";
    message(error.message, "error");
  }
  updateControls();
}

$("cameraInput").addEventListener("change", selectPhoto);
$("galleryInput").addEventListener("change", selectPhoto);
$("clear").addEventListener("click", () => {
  clearSelection();
  message("写真を選び、プレビューを確認してください。");
});
$("reconnect").addEventListener("click", connect);
$("send").addEventListener("click", async () => {
  if (!selected || !connected || busy) return;
  busy = true;
  updateControls();
  message("PCへ送信し、画像を処理しています…", "busy");
  try {
    const result = await uploadImage(selected, token);
    $("dryRun").hidden = !result.dry_run;
    message(`${result.message} (${result.width} × ${result.height}px)`, result.dry_run ? "" : "success");
  } catch (error) {
    message(error.message, "error");
  } finally {
    busy = false;
    updateControls();
  }
});
window.addEventListener("pagehide", () => { if (previewURL) URL.revokeObjectURL(previewURL); });
connect();
