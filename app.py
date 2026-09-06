# 'Non Ci Casco Mai' - Backend FastAPI Blindato Anti-Bot
import os
import json
import urllib.request
import urllib.parse
import base64
import time
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from PIL import Image

# Importiamo slowapi per il Rate Limiting (protezione anti-bot e anti-flood)
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Inizializziamo il limitatore basato sull'IP del client
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# Limiti di sicurezza per prevenire attacchi DoS tramite payload enormi
MAX_TEXT_LENGTH = 5000  # Massimo 5000 caratteri per il testo
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # Massimo 10 MB per i file immagine

SYSTEM_PROMPT = """
Sei 'Non Ci Casco Mai', un esperto di cybersecurity e analista antifrode.
Analizza il messaggio o l'immagine e rispondi con 4 sezioni:
1. VERDETTO: [🔴 TRUFFA / 🟡 SOSPETTO / 🟢 SICURO]
2. PERCHÉ È UNA TRUFFA
3. LEVA PSICOLOGICA USATA
4. COSA FARE ORA
"""

def call_gemini_api_native(prompt, image_path=None):
    if not GEMINI_API_KEY:
        return "⚠️ Errore: GEMINI_API_KEY non configurata."
    
    models_to_try = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash"
    ]
    
    parts = [{"text": prompt}]
    if image_path and os.path.exists(image_path):
        try:
            if os.path.getsize(image_path) > MAX_IMAGE_SIZE_BYTES:
                return "⚠️ Errore: L'immagine è troppo pesante (massimo 10MB)."
                
            img = Image.open(image_path)
            img.thumbnail((1024, 1024))
            compressed_path = image_path + "_comp.jpg"
            img.convert("RGB").save(compressed_path, "JPEG", quality=80)
            
            with open(compressed_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            parts.append({"inline_data": {"mime_type": "image/jpeg", "data": encoded_string}})
            
            if os.path.exists(compressed_path):
                os.remove(compressed_path)
        except Exception as e:
            return f"⚠️ Errore elaborazione immagine: {e}"
            
    payload = {"contents": [{"parts": parts}]}
    data_bytes = json.dumps(payload).encode('utf-8')
    
    last_error = ""
    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        req = urllib.request.Request(url, data=data_bytes, headers={'Content-Type': 'application/json'})
        
        for attempt in range(2):
            try:
                with urllib.request.urlopen(req, timeout=45) as response:
                    result = json.loads(response.read().decode())
                    return result["candidates"][0]["content"]["parts"][0]["text"]
            except urllib.error.HTTPError as e:
                error_body = e.read().decode()
                last_error = f"HTTP {e.code}: {error_body}"
                if e.code in (503, 429):
                    time.sleep(2)
                    continue
                elif e.code == 404:
                    break
                return f"⚠️ Errore API Gemini: {last_error}"
            except Exception as e:
                last_error = str(e)
                time.sleep(1)
                continue
            
    return f"⚠️ Errore API Gemini (Tutti i modelli sono temporaneamente occupati): {last_error}"

def perform_core_analysis(text_content=None, file_path=None):
    try:
        prompt_to_send = SYSTEM_PROMPT
        if text_content:
            if len(text_content) > MAX_TEXT_LENGTH:
                text_content = text_content[:MAX_TEXT_LENGTH]
            prompt_to_send += f"\n\nMessaggio o URL fornito: {text_content}"
        if file_path:
            prompt_to_send += "\n\nAnalizza questo screenshot per truffe o phishing."
        return call_gemini_api_native(prompt_to_send, file_path)
    finally:
        if file_path and os.path.exists(file_path):
            try: os.remove(file_path)
            except: pass

def send_telegram_message(chat_id, text):
    if not BOT_TOKEN: return
    try:
        tg_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        req = urllib.request.Request(tg_url, data=json.dumps({"chat_id": chat_id, "text": text}).encode('utf-8'), headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Errore Telegram: {e}")

@app.get("/", response_class=HTMLResponse)
@limiter.limit("30/minute")
def read_root(request: Request):
    try:
        with open("templates/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"<h1>Errore caricamento template: {e}</h1>"

@app.get("/privacy", response_class=HTMLResponse)
@limiter.limit("30/minute")
def privacy_page(request: Request):
    try:
        with open("templates/privacy.html", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"<h1>Errore caricamento privacy policy: {e}</h1>"

@app.post("/analizza")
@limiter.limit("5/minute")  # BLINDATURA CRITICA: Massimo 5 richieste di analisi al minuto per IP
async def web_analizza(request: Request):
    try:
        data = await request.json()
        text = data.get("testo")
        image_base64 = data.get("image")
        temp_path = None
        
        if image_base64:
            temp_path = "/tmp/upload_img.jpg"
            with open(temp_path, "wb") as fh:
                fh.write(base64.b64decode(image_base64))
                
        res = perform_core_analysis(text_content=text, file_path=temp_path)
        return JSONResponse({"risultato": res})
    except Exception as e:
        return JSONResponse({"errore": "Si è verificato un errore durante l'elaborazione della richiesta."}, status_code=500)

@app.post("/telegram")
@limiter.limit("30/minute")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        if "message" not in data: return {"status": "ok"}
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        if "text" in msg:
            send_telegram_message(chat_id, perform_core_analysis(text_content=msg["text"]))
        elif "photo" in msg:
            send_telegram_message(chat_id, "Ricevuto! Analisi in corso...")
            photo = msg["photo"][-1]
            file_info_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={photo['file_id']}"
            file_info = json.loads(urllib.request.urlopen(file_info_url).read().decode())
            down_path = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info['result']['file_path']}"
            temp_path = f"/tmp/{photo['file_id']}.jpg"
            urllib.request.urlretrieve(down_path, temp_path)
            send_telegram_message(chat_id, perform_core_analysis(file_path=temp_path))
    except Exception as e:
        print(f"Errore Telegram: {e}")
    return {"status": "ok"}
