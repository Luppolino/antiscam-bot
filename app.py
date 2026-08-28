import os
import json
import urllib.request
import urllib.parse
import base64
import time
from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse

app = FastAPI()

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

BOARD_FILE = "scams_board.json"
LAST_UPDATE_FILE = "last_update.txt"
UPDATE_INTERVAL = 3600

DEFAULT_SCAMS = [
    {
        "risk": "🔴",
        "title": "Finto SMS Poste / Corriere",
        "desc": "Messaggio con link anomalo che avvisa di un finto pacco bloccato in giacenza."
    },
    {
        "risk": "🟡",
        "title": "Finto rimborso INPS / Agenzia Entrate",
        "desc": "Comunicazione urgente che promette un rimborso fiscale immediato."
    },
    {
        "risk": "🔴",
        "title": "Phishing Account Streaming",
        "desc": "Avviso di blocco imminente dell'abbonamento per problemi di pagamento."
    }
]

def load_scams_board():
    if not os.path.exists(BOARD_FILE):
        save_scams_board(DEFAULT_SCAMS)
    try:
        with open(BOARD_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_SCAMS

def save_scams_board(scams_list):
    try:
        with open(BOARD_FILE, "w", encoding="utf-8") as f:
            json.dump(scams_list, f, ensure_ascii=False, indent=4)
        with open(LAST_UPDATE_FILE, "w", encoding="utf-8") as f:
            f.write(str(time.time()))
    except Exception as e:
        print(f"Errore bacheca: {e}")

def check_and_auto_update_radar():
    should_update = False
    if not os.path.exists(LAST_UPDATE_FILE) or not os.path.exists(BOARD_FILE):
        should_update = True
    else:
        try:
            with open(LAST_UPDATE_FILE, "r", encoding="utf-8") as f:
                if time.time() - float(f.read().strip()) > UPDATE_INTERVAL:
                    should_update = True
        except Exception:
            should_update = True

    if should_update:
        try:
            prompt = 'Genera una lista di 3 truffe informatiche o phishing molto diffuse in Italia di recente. Restituisci SOLO un JSON puro (senza markdown) come lista di oggetti con chiavi: "risk" (🔴 o 🟡), "title" e "desc".'
            ai_response = call_gemini_api_native(prompt)
            clean_json = ai_response.strip()
            if clean_json.startswith("```json"): clean_json = clean_json[7:]
            if clean_json.endswith("```"): clean_json = clean_json[:-3]
            new_scams = json.loads(clean_json.strip())
            if isinstance(new_scams, list) and len(new_scams) > 0:
                save_scams_board(new_scams)
        except Exception as e:
            print(f"Errore update automatico: {e}")

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
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_API_KEY}"
    parts = [{"text": prompt}]
    if image_path and os.path.exists(image_path):
        try:
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            parts.append({"inline_data": {"mime_type": "image/jpeg", "data": encoded_string}})
        except Exception as e:
            return f"Errore immagine: {e}"
    payload = {"contents": [{"parts": parts}]}
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"⚠️ Errore API Gemini: {str(e)}"

def perform_core_analysis(text_content=None, file_path=None):
    try:
        prompt_to_send = SYSTEM_PROMPT
        if text_content:
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
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Errore Telegram: {e}")

def generate_html_page(result_html=""):
    check_and_auto_update_radar()
    scams = load_scams_board()
    cards = "".join([f'<div class="scam-card"><h3>{s.get("risk","🔴")} {s.get("title","")}</h3><p>{s.get("desc","")}</p></div>' for s in scams])
    disp = "block;" if result_html else "none;"
    
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-H698KT76PV"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());

      gtag('config', 'G-H698KT76PV');
    </script>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Non Ci Casco Mai</title>
    <style>
    body {{ font-family: sans-serif; background: #f4f7f6; margin: 0; padding: 20px; display: flex; justify-content: center; }}
    .container {{ max-width: 700px; width: 100%; background: #fff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
    h1 {{ color: #1a365d; text-align: center; }}
    textarea, input[file] {{ width: 100%; padding: 10px; margin-bottom: 15px; box-sizing: border-box; border-radius: 6px; border: 1px solid #ccc; }}
    textarea {{ height: 90px; }}
    button {{ background: #3182ce; color: white; border: none; padding: 12px; width: 100%; border-radius: 6px; font-weight: bold; cursor: pointer; }}
    .result {{ margin-top: 20px; background: #edf2f7; padding: 15px; border-radius: 6px; white-space: pre-wrap; display: {disp}; border-left: 5px solid #3182ce; }}
    .board {{ margin-top: 30px; border-top: 2px solid #eee; padding-top: 20px; }}
    .scam-card {{ background: #fff5f5; border: 1px solid #feb2b2; border-left: 5px solid #e53e3e; padding: 12px; border-radius: 6px; margin-bottom: 10px; }}
    .scam-card h3 {{ margin: 0 0 5px 0; color: #c53030; font-size: 15px; }}
    .scam-card p {{ margin: 0; font-size: 13px; color: #4a5568; }}
    .btn-up {{ background: #38a169; width: auto; padding: 6px 12px; font-size: 13px; }}
    </style>
</head>
<body>
<div class="container">
<h1>Non Ci Casco Mai 🛡️</h1>
<form action="/analyze" method="post" enctype="multipart/form-data">
<label>Incolla messaggio o link:</label>
<textarea name="text" placeholder="Es. Pacco bloccato..."></textarea>
<label>Oppure carica screenshot:</label>
<input type="file" name="file" accept="image/*">
<button type="submit">Analizza con IA</button>
</form>
<div class="result"><strong>Risultato:</strong><br><br>{result_html}</div>
<div class="board">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
<h3 style="margin:0;">🚨 Ultime Truffe</h3>
<form action="/update-radar" method="get" style="margin:0;"><button type="submit" class="btn-up">🔄 Aggiorna</button></form>
</div>
{cards}
</div>
</div>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
def read_root():
    return generate_html_page("")

@app.post("/analyze", response_class=HTMLResponse)
async def web_analyze(text: str = Form(None), file: UploadFile = File(None)):
    temp_path = None
    try:
        if file and file.filename:
            temp_path = f"/tmp/{file.filename}"
            with open(temp_path, "wb") as buffer:
                buffer.write(await file.read())
        res = perform_core_analysis(text_content=text, file_path=temp_path)
        return generate_html_page(res)
    except Exception as e:
        return generate_html_page(f"Errore: {e}")

@app.get("/update-radar", response_class=HTMLResponse)
def update_radar():
    try:
        prompt = 'Genera una lista di 3 truffe informatiche o phishing molto diffuse in Italia di recente. Restituisci SOLO un JSON puro (senza markdown) come lista di oggetti con chiavi: "risk" (🔴 o 🟡), "title" e "desc".'
        res = call_gemini_api_native(prompt)
        clean_json = res.strip()
        if clean_json.startswith("```json"): clean_json = clean_json[7:]
        if clean_json.endswith("```"): clean_json = clean_json[:-3]
        new_scams = json.loads(clean_json.strip())
        if isinstance(new_scams, list) and len(new_scams) > 0:
            save_scams_board(new_scams)
    except Exception as e:
        print(f"Errore aggiornamento: {e}")
    return generate_html_page("✅ Radar aggiornato con successo!")

@app.post("/telegram")
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
            file_info = json.loads(urllib.request.urlopen(f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={photo['file_id']}").read().decode())
            down_path = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info['result']['file_path']}"
            temp_path = f"/tmp/{photo['file_id']}.jpg"
            urllib.request.urlretrieve(down_path, temp_path)
            send_telegram_message(chat_id, perform_core_analysis(file_path=temp_path))
    except Exception as e:
        print(f"Errore Telegram: {e}")
    return {"status": "ok"}
