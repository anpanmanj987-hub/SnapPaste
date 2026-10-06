/** Interface text in Japanese and English. Tests parse TEXT as JSON. */
export const TEXT = Object.freeze({
 "ja": {
  "page_title": "SnapPaste — 写真を、PCへ。",
  "switch_language": "English",
  "hero_1": "写真を、",
  "hero_2": "PCへ。",
  "lead_1": "撮る。確かめる。送る。",
  "lead_2": "あとはPCで貼り付けるだけ。",
  "connection_label": "PCとの接続",
  "checking": "接続を確認中",
  "checking_detail": "PCの受信ホストを確認しています。",
  "reconnect": "再接続",
  "dry_run_title": "dry-run / 動作確認モード",
  "dry_run_detail": "画像処理と転送を確認できます。PCのクリップボードは更新しません。",
  "choose_heading": "写真を選ぶ",
  "take_photo": "写真を撮る",
  "take_photo_hint": "スマホのカメラを開く",
  "pick_photo": "写真を選ぶ",
  "pick_photo_hint": "ライブラリから選ぶ",
  "preview_placeholder": "ここにプレビューが表示されます",
  "not_sent_yet": "選んだだけでは送信されません。",
  "preview_alt": "送信する写真のプレビュー",
  "no_photo": "写真はまだ選ばれていません",
  "clear": "取り消す",
  "send_heading": "確認して送る",
  "processing_note": "向きを補正し、長辺{edge}px以内に縮小します。メタデータを除去し、透過部分は白背景になります。",
  "send": "PCへ送信する",
  "sending_label": "送信・画像処理中…",
  "choose_and_check": "写真を選び、プレビューを確認してください。",
  "paste_label": "PCで貼り付け",
  "paste_title": "PCで貼り付ける",
  "paste_before": "コピー完了後、貼り付けたいアプリで",
  "paste_after": "。",
  "footer_1": "同じネットワーク内で使う、写真の受け渡し。",
  "footer_2": "画像は既定では保存しません。LAN通信は平文HTTPです。信頼できるネットワークでご利用ください。",
  "size_limit": "画像の容量は{mib}MiB以内にしてください。",
  "check_then_send": "写真を確認したら、「PCへ送信する」を押してください。",
  "preview_failed": "プレビューを開けません。JPEG・PNG・WebPを選んでください。HEICはJPEGへ変換してください。",
  "loading_preview": "プレビューを読み込んでいます…",
  "connected": "PCに接続しました",
  "host_running": "受信ホストが起動中 · 上限{mib}MiB",
  "dry_run_paste_title": "画像処理の確認",
  "dry_run_paste_note": "このモードではクリップボードを更新しません。貼り付けの確認にはWindowsの通常モードで起動してください。",
  "cannot_connect": "接続できません",
  "sending": "PCへ送信し、画像を処理しています…",
  "no_token": "PCのQRコードから接続してください。",
  "unreadable_reply": "PCからの返答を確認できませんでした。接続を確認してください。",
  "send_failed": "送信できませんでした。PCとの接続を確認してください。",
  "send_timeout": "送信がタイムアウトしました。PCで状態を確認し、再送してください。",
  "unreachable": "PCに接続できません。同じネットワークと受信ホストを確認してください。",
  "unconfirmed": "コピーの完了を確認できませんでした。PCで状態を確認してください。"
 },
 "en": {
  "page_title": "SnapPaste — Photos to your PC.",
  "switch_language": "日本語",
  "hero_1": "Photos,",
  "hero_2": "to your PC.",
  "lead_1": "Shoot. Check. Send. ",
  "lead_2": "Then just paste on your PC.",
  "connection_label": "Connection to the PC",
  "checking": "Checking connection",
  "checking_detail": "Looking for the host on your PC.",
  "reconnect": "Reconnect",
  "dry_run_title": "dry-run / test mode",
  "dry_run_detail": "Checks processing and transfer. The PC clipboard is not updated.",
  "choose_heading": "Choose a photo",
  "take_photo": "Take a photo",
  "take_photo_hint": "Opens the phone camera",
  "pick_photo": "Choose a photo",
  "pick_photo_hint": "From your library",
  "preview_placeholder": "Your preview appears here",
  "not_sent_yet": "Choosing a photo does not send it.",
  "preview_alt": "Preview of the photo to send",
  "no_photo": "No photo selected yet",
  "clear": "Clear",
  "send_heading": "Check and send",
  "processing_note": "Orientation is corrected and the long edge reduced to {edge} px or less. Metadata is removed and transparency becomes white.",
  "send": "Send to PC",
  "sending_label": "Sending and processing…",
  "choose_and_check": "Choose a photo and check the preview.",
  "paste_label": "Paste on the PC",
  "paste_title": "Paste on your PC",
  "paste_before": "After the copy, press",
  "paste_after": "in the app where you want it.",
  "footer_1": "Photo hand-off within your own network.",
  "footer_2": "Images are not saved by default. LAN traffic is plain HTTP; use a trusted network.",
  "size_limit": "Images must be {mib} MiB or smaller.",
  "check_then_send": "Check the photo, then press “Send to PC”.",
  "preview_failed": "Cannot open a preview. Choose a JPEG, PNG or WebP image; convert HEIC to JPEG first.",
  "loading_preview": "Loading the preview…",
  "connected": "Connected to the PC",
  "host_running": "Host is running · limit {mib} MiB",
  "dry_run_paste_title": "Processing check",
  "dry_run_paste_note": "This mode never updates the clipboard. To test pasting, start SnapPaste normally on Windows.",
  "cannot_connect": "Cannot connect",
  "sending": "Sending to the PC and processing…",
  "no_token": "Connect from the QR code on the PC.",
  "unreadable_reply": "Could not read the PC's reply. Check the connection.",
  "send_failed": "Could not send. Check the connection to the PC.",
  "send_timeout": "Sending timed out. Check the PC and send again.",
  "unreachable": "Cannot reach the PC. Check that you are on the same network and the host is running.",
  "unconfirmed": "Could not confirm the copy. Check the PC."
 }
});

let current = 'ja';
export function setLanguage(lang) { current = lang === 'en' ? 'en' : 'ja'; }
export function getLanguage() { return current; }
export function t(key, params = {}) {
  const template = TEXT[current][key] ?? TEXT.en[key] ?? key;
  return template.replace(/\{(\w+)\}/g, (_, name) => String(params[name] ?? ''));
}
/** ?lang=ja|en, then a remembered choice, then the first ja/en entry of the browser's languages. */
export function pickLanguage({search = '', saved = null, languages = []} = {}) {
  const asked = new URLSearchParams(search).get('lang');
  if (asked === 'ja' || asked === 'en') return asked;
  if (saved === 'ja' || saved === 'en') return saved;
  for (const tag of languages) {
    if (/^ja\b/i.test(tag)) return 'ja';
    if (/^en\b/i.test(tag)) return 'en';
  }
  return 'en';
}
