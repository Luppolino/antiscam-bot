import os
import json
import urllib.request
import urllib.parse
import base64
from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse

app = FastAPI()

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# File di salvataggio dinamico della bacheca
BOARD_FILE = "scams_board.json"

# Inizializziamo la bacheca con dati di default se il file non esiste
DEFAULT_SCAMS = [
    {
        "risk": "🔴",
        "title": "Finto SMS Poste / Corriere",
        "desc": "Messaggio con link anomalo che avvisa di un pacco bloccato in giacenza per sbloccare il quale vengono chiesti dati bancari o pagamenti di piccoli importi."
    },
    {
        "risk": "🟡",
        "title": "Finto rimborso INPS / Agenzia Entrate",
        "desc": "Comunicazione urgente via mail o SMS che promette un rimborso fiscale immediato invitando a inserire le credenziali SPID o bancarie su portali civetta."
    },
    {
        "risk": "🔴",
        "title": "Phishing Account Streaming / Servizi",
        "desc": "Avviso di blocco imminente dell'abbonamento per problemi di pagamento con link diretto a una pagina clone identica all'originale."
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
    except Exception as e:
        print(f"Errore nel salvataggio della bacheca: {e}")

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

def call_gemini_api_native(prompt, image_path=None):
    if not GEMINI_API_KEY:
        return "⚠️ Analisi IA non disponibile: GEMINI_API_KEY non configurata nelle variabili d'ambiente di Render."
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_API_KEY}"
    parts = [{"text": prompt}]
    
    if image_path and os.path.exists(image_path):
        try:
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            parts.append({
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": encoded_string
                }
            })
        except Exception as e:
            return f"Errore nella lettura dell'immagine: {e}"
        
    payload = {"contents": [{"parts": parts}]}
    data_encoded = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data_encoded, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            if "candidates" in result and len(result["candidates"]) > 0:
                return result["candidates"][0]["content"]["parts"][0]["text"]
            return "⚠️ Risposta vuota ricevuta da Google Gemini."
    except urllib.error.HTTPError as he:
        error_body = he.read().decode('utf-8', errors='ignore')
        print(f"Gemini HTTP Error {he.code}: {error_body}")
        if he.code == 404:
            return "⚠️ Errore di connessione (404): Endpoint o modello non trovato."
        elif he.code == 429 or he.code == 503:
            return "⚠️ I server di Google sono momentaneamente sovraccarichi. Riprova tra qualche istante!"
        return f"⚠️ Errore API Gemini ({he.code}): {he.reason}"
    except Exception as e:
        return f"⚠️ Errore di comunicazione con Google Gemini: {str(e)}"

def perform_core_analysis(text_content=None, file_path=None):
    try:
        domain_warning = ""
        prompt_to_send = SYSTEM_PROMPT
        
        if text_content:
            domain_warning = analyze_domain_safety(text_content)
            prompt_to_send += f"\n\nMessaggio o URL fornito dall'utente: {text_content}"
            if domain_warning:
                prompt_to_send += f"\n\n[Nota tecnica preventiva: {domain_warning}]"

        if file_path:
            prompt_to_send += "\n\nAnalizza questo screenshot per individuare eventuali truffe o tentativi di phishing."

        response_text = call_gemini_api_native(prompt_to_send, file_path)
        
        if domain_warning and ("⚠️" in response_text or "Errore" in response_text):
            return f"{domain_warning}\n\n{response_text}"
            
        return response_text

    except Exception as e:
        return f"Si è verificato un errore durante l'elaborazione: {str(e)}"
        
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"[PRIVACY ZERO-TRACE] File {file_path} eliminato definitivamente.")
            except Exception as cleanup_error:
                print(f"Impossibile rimuovere il file temporaneo: {cleanup_error}")

def send_telegram_message(chat_id, text):
    if not BOT_TOKEN:
        print("Errore: TELEGRAM_BOT_TOKEN mancante!")
        return
    try:
        tg_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        data_encoded = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(tg_url, data=data_encoded, headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Errore invio messaggio Telegram: {e}")

def generate_html_with_dynamic_board(result_html=""):
    scams = load_scams_board()
    cards_html = ""
    for scam in scams:
        cards_html += f"""
            <div class="scam-card">
                <h3>{scam.get('risk', '🔴')} {scam.get('title', 'Segnalazione')}</h3>
                <p>{scam.get('desc', '')}</p>
            </div>
        """

    display_style = "block;" if result_html else "none;"

    html_content = f"""
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Non Ci Casco Mai - Analizzatore Antifrode & Bacheca</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f4f7f6; color: #333; margin: 0; padding: 20px; display: flex; justify-content: center; }}
        .container {{ max-width: 700px; width: 100%; background: #fff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
        h1 {{ color: #1a365d; font-size: 24px; text-align: center; margin-bottom: 5px; }}
        p.subtitle {{ text-align: center; color: #666; font-size: 14px; margin-bottom: 25px; }}
        label {{ font-weight: bold; display: block; margin-bottom: 8px; color: #2d3748; }}
        textarea, input[type="file"] {{ width: 100%; padding: 12px; border: 1px solid #cbd5e0; border-radius: 8px; margin-bottom: 20px; font-size: 14px; box-sizing: border-box; }}
        textarea {{ height: 100px; resize: vertical; }}
        button {{ background: #3182ce; color: white; border: none; padding: 12px 20px; width: 100%; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; transition: background 0.2s; }}
        button:hover {{ background: #2b6cb0; }}
        .result-box {{ margin-top: 25px; background: #edf2f7; padding: 20px; border-radius: 8px; white-space: pre-wrap; line-height: 1.5; font-size: 14px; border-left: 5px solid #3182ce; display:{display_style}; }}
        
        /* Bacheca Truffe */
        .board-section {{ margin-top: 40px; border-top: 2px solid #e2e8f0; padding-top: 25px; }}
        .board-title {{ font-size: 18px; color: #2d3748; margin-bottom: 15px; font-weight: bold; display: flex; align-items: center; gap: 8px; }}
        .scam-card {{ background: #fff5f5; border: 1px solid #feb2b2; border-left: 5px solid #e53e3e; padding: 15px; border-radius: 8px; margin-bottom: 15px; }}
        .scam-card h3 {{ margin: 0 0 5px 0; color: #c53030; font-size: 16px; }}
        .scam-card p {{ margin: 0; font-size: 13px; color: #4a5568; line-height: 1.4; }}
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
            <span>{result_html}</span>
        </div>

        <!-- BACHECA DINAMICA AGGIORNATA IN TEMPO REALE -->
        <div class="board-section">
            <div class="board-title">🚨 Bacheca Ultime Truffe Segnalate</div>
            {cards_html}
        </div>
    </div>
</body>
</html>
"""
    return html_content

@app.get("/", response_class=HTMLResponse)
def read_root():
    return generate_html_with_dynamic_board("")

@app.post("/analyze", response_class=HTMLResponse)
async def web_analyze(text: str = Form(None), file: UploadFile = File(None)):
    temp_file_path = None
    try:
        if file and file.filename:
            temp_file_path = f"/tmp/{file.filename}"
            with open(temp_file_path, "wb") as buffer:
                buffer.write(await file.read())

        analysis_result = perform_core_analysis(text_content=text, file_path=temp_file_path)
        return generate_html_with_dynamic_board(analysis_result)

    except Exception as e:
        return generate_html_with_dynamic_board(f"Errore durante l'elaborazione web: {str(e)}")

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
