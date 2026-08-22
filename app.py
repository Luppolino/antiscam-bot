import os
import json
import urllib.request
import urllib.parse
from fastapi import FastAPI, Request
from PIL import Image
import google.generativeai as genai

# Inizializzazione dell'applicazione FastAPI
app = FastAPI()

# Recupera le chiavi dalle variabili d'ambiente di Render
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
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
# 3. ROTTE FASTAPI (WEBHOOK TELEGRAM & ROOT)
# ==========================================
@app.get("/")
def read_root():
    return {"status": "Non Ci Casco Mai bot is online"}

@app.post("/telegram")
async def telegram_webhook(request: Request):
    temp_file_path = None
    try:
        data = await request.json()
        if "message" not in data:
            return {"status": "ok"}
            
        message = data["message"]
        chat_id = message["chat"]["id"]
        
        # A. GESTIONE TESTO
        if "text" in message:
            text = message["text"]
            domain_warning = analyze_domain_safety(text)
            
            prompt_to_send = SYSTEM_PROMPT + f"\n\nMessaggio dell'utente da analizzare: {text}"
            if domain_warning:
                prompt_to_send += f"\n\n[Nota tecnica preventiva: {domain_warning}]"
            
            if GEMINI_API_KEY:
                response = model.generate_content(prompt_to_send)
                reply_text = response.text
            else:
                reply_text = f"{domain_warning}\n\nAnalisi completata (chiave Gemini non configurata)."
                
            send_telegram_message(chat_id, reply_text)

        # B. GESTIONE FOTO / SCREENSHOT (con Zero-Trace)
        elif "photo" in message:
            send_telegram_message(chat_id, "Ricevuto! Analisi dello screenshot in corso...")
            photo = message["photo"][-1]
            file_id = photo["file_id"]
            
            # Scarica il percorso del file da Telegram
            get_file_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}"
            with urllib.request.urlopen(get_file_url) as response_file:
                file_info = json.loads(response_file.read().decode())
                telegram_file_path = file_info["result"]["file_path"]
            
            # Scarica l'immagine fisicamente sul server in modo temporaneo
            download_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{telegram_file_path}"
            temp_file_path = f"/tmp/{file_id}.jpg"
            urllib.request.urlretrieve(download_url, temp_file_path)
            
            try:
                img = Image.open(temp_file_path)
                if GEMINI_API_KEY:
                    response = model.generate_content([SYSTEM_PROMPT, "Analizza questo screenshot per individuare eventuali truffe o tentativi di phishing.", img])
                    reply_text = response.text
                else:
                    reply_text = "Immagine ricevuta, ma chiave Gemini non configurata."
                send_telegram_message(chat_id, reply_text)
            except Exception as e:
                send_telegram_message(chat_id, f"Errore nell'analisi dell'immagine: {str(e)}")
            finally:
                # CANCELLAZIONE ISTANTANEA OBBLIGATORIA (Zero-Trace)
                if temp_file_path and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                    print(f"[PRIVACY ZERO-TRACE] File {temp_file_path} eliminato definitivamente.")

    except Exception as e:
        print(f"Errore nel webhook: {e}")
        
    return {"status": "ok"}
