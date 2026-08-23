import base64
import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

# Configurazione delle credenziali dalle variabili d'ambiente di Render
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Controllo preliminare delle chiavi
if not GEMINI_API_KEY:
    print(
        "ATTENZIONE: La variabile d'ambiente GEMINI_API_KEY non è configurata!"
    )
if not TELEGRAM_BOT_TOKEN:
    print(
        "ATTENZIONE: La variabile d'ambiente TELEGRAM_BOT_TOKEN non è configurata!"
    )


def analyze_with_gemini(prompt_text, image_path=None):
  """Funzione centrale per l'analisi tramite Gemini (usando l'endpoint v1beta o v1 e gemini-2.5-flash / gemini-1.5-flash)"""
  url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

  parts = [{"text": prompt_text}]

  # Gestione dell'immagine se presente (Zero-Trace: caricamento in memoria e invio)
  if image_path and os.path.exists(image_path):
    try:
      with open(image_path, "rb") as img_file:
        img_bytes = img_file.read()
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")
        parts.append(
            {
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": img_base64,
                }
            }
        )
    except Exception as e:
      print(f"Errore nella lettura dell'immagine temporanea: {e}")

  payload = {"contents": [{"parts": parts}]}

  data = json.dumps(payload).encode("utf-8")
  req = urllib.request.Request(
      url, data=data, headers={"Content-Type": "application/json"}, method="POST"
  )

  try:
    with urllib.request.urlopen(req) as response:
      res_data = json.loads(response.read().decode("utf-8"))
      # Estrae il testo della risposta generata dall'IA
      return (
          res_data.get("candidates", [{}])[0]
          .get("content", {})
          .get("parts", [{}])[0]
          .get("text", "Nessuna risposta generata dall'analisi.")
      )
  except urllib.error.HTTPError as e:
    error_body = e.read().decode("utf-8")
    print(f"Errore API Gemini ({e.code}): {error_body}")
    return f"⚠️ Errore di connessione (404/API): Endpoint o modello non trovato. Verifica la configurazione su Render."
  except Exception as e:
    print(f"Errore imprevisto durante la chiamata a Gemini: {e}")
    return "⚠️ Si è verificato un errore imprevisto durante l'elaborazione dell'analisi."


def send_telegram_message(chat_id, text):
  """Invia il messaggio di risposta al client Telegram"""
  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
  payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
  data = json.dumps(payload).encode("utf-8")
  req = urllib.request.Request(
      url, data=data, headers={"Content-Type": "application/json"}, method="POST"
  )
  try:
    with urllib.request.urlopen(req) as response:
      return response.read()
  except Exception as e:
    print(f"Errore nell'invio del messaggio Telegram: {e}")


class SimpleWebhookHandler(BaseHTTPRequestHandler):
  """Gestore HTTP leggero per ricevere i webhook da Telegram e gestire la dashboard web"""

  def do_GET(self):
    if self.path == "/" or self.path == "/health":
      self.send_response(200)
      self.send_header("Content-type", "text/plain; charset=utf-8")
      self.end_headers()
      self.wfile.write(
          b"==> NonCiCascoMai Service is running on port 10000 (Zero-Trace active)"
      )
    else:
      self.send_response(404)
      self.end_headers()

  def do_POST(self):
    if self.path == "/telegram" or self.path == "/webhook":
      content_length = int(self.headers.get("Content-Length", 0))
      post_data = self.rfile.read(content_length)

      try:
        update = json.loads(post_data.decode("utf-8"))

        # Estrazione dati dal messaggio Telegram
        if "message" in update:
          message = update["message"]
          chat_id = message["chat"]["id"]
          text_content = message.get("text", message.get("caption", ""))

          # Prompt di sistema strutturato per l'analisi anti-truffa
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

          # Gestione immagini inviate tramite Telegram (se presenti)
          temp_file_path = None
          if "photo" in message:
            # Prende la foto a risoluzione maggiore
            photo_file_id = message["photo"][-1]["file_id"]
            # Ottiene il path del file da Telegram
            file_info_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={photo_file_id}"
            with urllib.request.urlopen(file_info_url) as f_info:
              file_data = json.loads(f_info.read().decode("utf-8"))
              if file_data.get("ok"):
                file_path_tg = file_data["result"]["file_path"]
                download_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path_tg}"

                # Salvataggio temporaneo locale per l'analisi
                temp_file_path = f"/tmp/img_{chat_id}.jpg"
                urllib.request.urlretrieve(download_url, temp_file_path)

          # Esecuzione dell'analisi tramite IA
          analysis_result = analyze_with_gemini(prompt_base, temp_file_path)

          # Protocollo Zero-Trace: eliminazione immediata del file temporaneo
          if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            print(f"[PRIVACY ZERO-TRACE] File {temp_file_path} eliminato definitivamente.")

          # Invio della risposta all'utente su Telegram
          send_telegram_message(chat_id, analysis_result)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

      except Exception as e:
        print(f"Errore nell'elaborazione della richiesta POST: {e}")
        self.send_response(500)
        self.end_headers()
    else:
      self.send_response(404)
      self.end_headers()


def run_server():
  port = int(os.environ.get("PORT", 10000))
  server_address = ("", port)
  httpd = HTTPServer(server_address, SimpleWebhookHandler)
  print(f"==> Detected service running on port {port}")
  httpd.serve_forever()


if __name__ == "__main__":
  run_server()
