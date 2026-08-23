import base64
import json
import os
import urllib.request
from fastapi import FastAPI, Request, Response

app = FastAPI()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")


def analyze_with_gemini(prompt_text, image_path=None):
  # Utilizziamo gemini-2.5-flash sull'endpoint v1beta supportato per le chiamate dirette
  url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
  
  parts = [{"text": prompt_text}]

  if image_path and os.path.exists(image_path):
    try:
      with open(image_path, "rb") as img_file:
        img_bytes = img_file.read()
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")
        parts.append({
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": img_base64
            }
        })
    except Exception as e:
      print(f"Errore lettura immagine: {e}")

  payload = {"contents": [{"parts": parts}]}
  data = json.dumps(payload).encode("utf-8")
  
  req = urllib.request.Request(
      url, data=data, headers={"Content-Type": "application/json"}, method="POST"
  )

  try:
    with urllib.request.urlopen(req) as response:
      res_data = json.loads(response.read().decode("utf-8"))
      return (
          res_data.get("candidates", [{}])[0]
          .get("content", {})
          .get("parts", [{}])[0]
          .get("text", "Nessuna risposta generata.")
      )
  except urllib.error.HTTPError as e:
    error_body = e.read().decode("utf-8")
    print(f"Errore HTTP Gemini ({e.code}): {error_body}")
    return f"⚠️ Errore API Gemini ({e.code}). Controlla che la chiave supporti 'gemini-2.5-flash'."
  except Exception as e:
    print(f"Errore imprevisto API Gemini: {e}")
    return "⚠️ Si è verificato un errore imprevisto durante l'elaborazione con l'IA."


def send_telegram_message(chat_id, text):
  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
  payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
  data = json.dumps(payload).encode("utf-8")
  req = urllib.request.Request(
      url, data=data, headers={"Content-Type": "application/json"}, method="POST"
  )
  try:
    urllib.request.urlopen(req)
  except Exception as e:
    print(f"Errore invio Telegram: {e}")


@app.get("/")
def health_check():
  return Response(content="==> NonCiCascoMai Service is running (Zero-Trace active)", media_type="text/plain")


@app.post("/telegram")
async def telegram_webhook(request: Request):
  try:
    update = await request.json()
    if "message" in update:
      message = update["message"]
      chat_id = message["chat"]["id"]
      text_content = message.get("text", message.get("caption", ""))

      prompt_base = (
          "Sei NonCiCascoMai, un assistente di sicurezza digitale esperto in "
          "anti-phishing e prevenzione frodi. Analizza il seguente contenuto "
          "fornendo una valutazione del rischio strutturata in 4 parti: "
          "1. Livello di rischio (Basso/Medio/Alto), "
          "2. Indicatori di allerta rilevati (red flags), "
          "3. Motivazione dettagliata, "
          "4. Consigli pratici su cosa fare.\n\nContenuto da analizzare: "
          + text_content
      )

      temp_file_path = None
      if "photo" in message:
        photo_file_id = message["photo"][-1]["file_id"]
        file_info_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={photo_file_id}"
        with urllib.request.urlopen(file_info_url) as f_info:
          file_data = json.loads(f_info.read().decode("utf-8"))
          if file_data.get("ok"):
            file_path_tg = file_data["result"]["file_path"]
            download_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path_tg}"
            temp_file_path = f"/tmp/img_{chat_id}.jpg"
            urllib.request.urlretrieve(download_url, temp_file_path)

      analysis_result = analyze_with_gemini(prompt_base, temp_file_path)

      if temp_file_path and os.path.exists(temp_file_path):
        os.remove(temp_file_path)
        print(f"[PRIVACY ZERO-TRACE] File {temp_file_path} eliminato definitivamente.")

      send_telegram_message(chat_id, analysis_result)

    return {"status": "ok"}
  except Exception as e:
    print(f"Errore webhook: {e}")
    return {"status": "error"}
