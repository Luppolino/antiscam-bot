import os
import json
import urllib.request
import urllib.parse
from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse
from PIL import Image
import google.generativeai as genai

# Inizializzazione dell'applicazione FastAPI
app = FastAPI()

# Recupera le chiavi dalle variabili d'ambiente di Render
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # Usiamo il modello stabile e ufficiale raccomandato
    model = genai.GenerativeModel('gemini-1.5-flash')

# ==========================================
# 1. CONFIGURAZIONE DEL SISTEMA & PROMPT IA
# ==========================================
SYSTEM_PROMPT = """
Sei 'Non Ci Casco Mai', un esperto di cybersecurity di altissimo livello e un analista antifrode.
Analizza il messaggio o l'immagine fornita dall'utente e rispondi SEMPRE con una struttura chiara, divisa in queste 4 sezioni:

1. VERDETTO: 
   [🔴 TRUFFA / 🟡 SOSPETTO / 🟢 SICURO] con una frase d'impatto.

2. PERCHÉ È UNA TRUFFA (Analisi dei pericoli):
   Elenca i dettagli tecnici o logici che non tornano (es. errori di ortografia, link civetta, mittente mascherato).

3. LEVA PSICOLOGICA USATA:
   Spiega quale emozione o pressione i truffatori stanno sfruttando (es. urgenza artificiale, paura della chiusura del conto, falsa golosità per un premio).

4. COSA FARE ORA (Piano di emergenza):
   Dai istruzioni immediate all'utente su come comportarsi (es. non cliccare, bloccare il mittente, e se ha già inserito dati, cosa fare subito).

Tieni il tono autorevole ma rassicurante, chiaro e diretto.
"""

# ==========================================
# 2. FILTRO ANTI-TYPOSQUATTING & DOMINI CIVETTA
# ==========================================
SUSPICIOUS_KEYWORDS = ['login', 'secure', 'verifica', 'aggiorna', 'account', 'sblocca', 'conferma', 'web-client']
SENSITIVE_BRANDS = ['poste', 'inps', 'agenziaentrate', 'intesasanpaolo', 'unicredit', 'paypal', 'amazon', 'netflix', 'dhl', 'bartolini']

def analyze_domain_safety(url_string):
    try:
        if not url_string.startswith('http'):
            url_string = 'http://' + url_string
        parsed = urllib.parse.urlparse(url_string)
        domain = parsed.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        
        for brand in SENSITIVE_BRANDS:
            if brand in domain:
                official_domains = [f"{brand}.it", f"{brand}.com", f"{brand}.net", f"{brand}.es", f"{brand}.fr"]
                if not any(domain.endswith(od) for od in official_domains):
                    return f"🔴 ALLARME TYPOSQUATTING: Il dominio `{domain}` sembra imitare falsamente il marchio **{brand}** usando un indirizzo civetta non ufficiale!"

        for word in SUSPICIOUS_KEYWORDS:
            if word in domain:
                return f"🟡 ATTENZIONE URL: Il dominio contiene la parola chiave sospetta `{word}`, tipica delle pagine di phishing."
                
        return ""
    except Exception:
        return ""

# ==========================================
# 3. MOTORE CENTRALE DI ANALISI (TELEGRAM + WEB)
# ==========================================
def perform_core_analysis(text_content=None, file_path=None):
    try:
        if not GEMINI_API_KEY:
            return "⚠️ Analisi IA non disponibile: GEMINI_API_KEY non configurata nelle variabili d'ambiente di Render."

        domain_warning = ""
        prompt_to_send = SYSTEM_PROMPT
        
        if text_content:
            domain_warning = analyze_domain_safety(text_content)
            prompt_to_send += f"\n\nMessaggio o URL fornito dall'utente: {text_content}"
            if domain_warning:
                prompt_to_send += f"\n\n[Nota tecnica preventiva: {domain_warning}]"

        content_payload = [prompt_to_send]
        
        if file_path and os.path.exists(file_path):
            img = Image.open(file_path)
            content_payload.append(img)
            content_payload.append("Analizza questo screenshot per individuare eventuali truffe o tentativi di phishing.")

        response = model.generate_content(content_payload)
        response_text = response.text

        if domain_warning and ("Errore" in response_text or "non disponibile" in response_text):
            return f"{domain_warning}\n\n{response_text}"
            
        return response_text

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "ResourceExhausted" in error_msg:
            return "⚠️ I server di Google sono momentaneamente sovraccarichi a causa di un picco di traffico. Riprova tra qualche istante!"
        return f"Si è verificato un errore durante l'elaborazione: {error_msg}"
        
    finally:
        # CANCELLAZIONE ISTANTANEA OBBLIGATORIA (Zero-Trace)
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"[PRIVACY ZERO-TRACE] File {file_path} eliminato definitivamente.")
            except Exception as cleanup_error:
                print(f"Impossibile rimuovere il file temporaneo: {cleanup_error}")

def send_telegram_message(chat_id, text):
    if not BOT_TOKEN:
        return
    try:
        tg_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        data_encoded = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(tg_url, data=data_encoded, headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Errore invio messaggio Telegram: {e}")

# ==========================================
# 4. INTERFACCIA WEB (SITO UFFICIALE)
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Non Ci Casco Mai - Analizzatore Antifrode</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f4f7f6; color: #333; margin: 0; padding: 20px; display: flex; justify-content: center; }
        .container { max-width: 600px; width: 100%; background: #fff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
        h1 { color: #1a365d; font-size: 24px; text-align: center; margin-bottom: 5px; }
        p.subtitle { text-align: center; color: #666; font-size: 14px; margin-bottom: 25px; }
        label { font-weight: bold; display: block; margin-bottom: 8px; color: #2d3748; }
        textarea, input[type="file"] { width: 100%; padding: 12px; border: 1px solid #cbd5e0; border-radius: 8px; margin-bottom: 20px; font-size: 14px; box-sizing: border-box; }
        textarea { height: 100px; resize: vertical; }
        button { background: #3182ce; color: white; border: none; padding: 12px 20px; width: 100%; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; transition: background 0.2s; }
        button:hover { background: #2b6cb0; }
        .result-box { margin-top: 25px; background: #edf2f7; padding: 20px; border-radius: 8px; white-space: pre-wrap; line-height: 1.5; font-size: 14px; border-left: 5px solid #3182ce; display:none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Non Ci Casco Mai 🛡️</h1>
        <p class="subtitle">Verifica subito se un messaggio, un link o uno screenshot è una truffa.</p>
        
        <form action="/analyze" method="post" enctype="multipart/form-data">
            <label for="text">Incolla qui il messaggio o il link sospetto:</label>
            <textarea name="text" placeholder="Es. Il tuo pacco è bloccato, clicca qui..."></textarea>
            
            <label for="file">Oppure carica uno screenshot:</label>
            <input type="file" name="file" accept="image/*">
            
            <button type="submit">Analizza con IA</button>
        </form>

        <div class="result-box" id="resultBox">
            <strong>Risultato dell'analisi:</strong><br><br>
            <span id="resultText">__RESULT_PLACEHOLDER__</span>
        </div>
    </div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def read_root():
    return HTML_TEMPLATE.replace("__RESULT_PLACEHOLDER__", "")

@app.post("/analyze", response_class=HTMLResponse)
async def web_analyze(text: str = Form(None), file: UploadFile = File(None)):
    temp_file_path = None
    try:
        if file and file.filename:
            temp_file_path = f"/tmp/{file.filename}"
            with open(temp_file_path, "wb") as buffer:
                buffer.write(await file.read())

        analysis_result = perform_core_analysis(text_content=text, file_path=temp_file_path)
        
        rendered_html = HTML_TEMPLATE.replace("__RESULT_PLACEHOLDER__", analysis_result)
        rendered_html = rendered_html.replace('class="result-box" id="resultBox">', 'class="result-box" id="resultBox" style="display:block;">')
        return rendered_html

    except Exception as e:
        rendered_html = HTML_TEMPLATE.replace("__RESULT_PLACEHOLDER__", f"Errore durante l'elaborazione web: {str(e)}")
        rendered_html = rendered_html.replace('class="result-box" id="resultBox">', 'class="result-box" id="resultBox" style="display:block;">')
        return rendered_html

# ==========================================
# 5. WEBHOOK TELEGRAM
# ==========================================
@app.post("/telegram")
async def telegram_webhook(request: Request):
    temp_file_path = None
    try:
        data = await request.json()
        if "message" not in data:
            return {"status": "ok"}
            
        message = data["message"]
        chat_id = message["chat"]["id"]
        
        if "text" in message:
            text = message["text"]
            reply_text = perform_core_analysis(text_content=text)
            send_telegram_message(chat_id, reply_text)

        elif "photo" in message:
            if not BOT_TOKEN:
                return {"status": "ok"}
            send_telegram_message(chat_id, "Ricevuto! Analisi dello screenshot in corso...")
            photo = message["photo"][-1]
            file_id = photo["file_id"]
            
            get_file_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}"
            with urllib.request.urlopen(get_file_url) as response_file:
                file_info = json.loads(response_file.read().decode())
                telegram_file_path = file_info["result"]["file_path"]
            
            download_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{telegram_file_path}"
            temp_file_path = f"/tmp/{file_id}.jpg"
            urllib.request.urlretrieve(download_url, temp_file_path)
            
            reply_text = perform_core_analysis(file_path=temp_file_path)
            send_telegram_message(chat_id, reply_text)

    except Exception as e:
        print(f"Errore nel webhook Telegram: {e}")
        
    return {"status": "ok"}
