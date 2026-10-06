import { getLanguage, t } from "/i18n.mjs";

// Requests use fetch's default cors mode. With no-referrer, explicitly selecting
// same-origin mode would make POST Origin:null in conforming browsers.
export async function requestJSON(path, token, options = {}) {
  if (!token) throw new Error(t("no_token"));
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30000);
  try {
    const response = await fetch(path, {
      ...options, credentials: "omit", cache: "no-store", signal: controller.signal,
      // Accept-Language makes the host answer in the interface language.
      headers: { ...options.headers, "X-SnapPaste-Token": token, "Accept-Language": getLanguage() },
    });
    let data;
    try { data = await response.json(); }
    catch { throw new Error(t("unreadable_reply")); }
    if (!response.ok || data.ok !== true) {
      throw new Error(data.message || t("send_failed"));
    }
    return data;
  } catch (error) {
    if (error.name === "AbortError") throw new Error(t("send_timeout"));
    if (error instanceof TypeError) throw new Error(t("unreachable"));
    throw error;
  } finally { clearTimeout(timeout); }
}

export async function uploadImage(file, token, endpoint = "/api/upload") {
  const data = await requestJSON(endpoint, token, {
    method: "POST", headers: { "Content-Type": "application/octet-stream" }, body: file,
  });
  if (data.dry_run !== true && data.clipboard_updated !== true) {
    throw new Error(t("unconfirmed"));
  }
  return data;
}
