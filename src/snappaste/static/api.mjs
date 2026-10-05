// Requests use fetch's default cors mode. With no-referrer, explicitly selecting
// same-origin mode would make POST Origin:null in conforming browsers.
export async function requestJSON(path, token, options = {}) {
  if (!token) throw new Error("PCのQRコードから接続してください。");
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30000);
  try {
    const response = await fetch(path, {
      ...options, credentials: "omit", cache: "no-store", signal: controller.signal,
      headers: { ...options.headers, "X-SnapPaste-Token": token },
    });
    let data;
    try { data = await response.json(); }
    catch { throw new Error("PCからの返答を確認できませんでした。接続を確認してください。"); }
    if (!response.ok || data.ok !== true) {
      throw new Error(data.message || "送信できませんでした。PCとの接続を確認してください。");
    }
    return data;
  } catch (error) {
    if (error.name === "AbortError") throw new Error("送信がタイムアウトしました。PCで状態を確認し、再送してください。");
    if (error instanceof TypeError) throw new Error("PCに接続できません。同じネットワークと受信ホストを確認してください。");
    throw error;
  } finally { clearTimeout(timeout); }
}

export async function uploadImage(file, token, endpoint = "/api/upload") {
  const data = await requestJSON(endpoint, token, {
    method: "POST", headers: { "Content-Type": "application/octet-stream" }, body: file,
  });
  if (data.dry_run !== true && data.clipboard_updated !== true) {
    throw new Error("コピーの完了を確認できませんでした。PCで状態を確認してください。");
  }
  return data;
}
