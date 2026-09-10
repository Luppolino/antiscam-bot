import os
import json
import urllib.request
import urllib.parse
import base64
import time
import uuid
import xml.etree.ElementTree as ET
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from PIL import Image

# Importiamo slowapi per il Rate Limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
BOT_USERNAME = "antiscam_italia_bot"
TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "").strip()
NEWSLETTER_SECRET = os.environ.get("NEWSLETTER_SECRET", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "").strip()
WHATSAPP_VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "").strip()
WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "").strip()

MAX_TEXT_LENGTH = 5000
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024

# Database in memoria
famiglie_db = {}        # Telegram: chat_id_genitore -> chat_id_figlio
famiglie_wa_db = {}     # WhatsApp: phone_genitore -> phone_figlio
sentinella_tokens = {}  # Token app Android -> {"platform": telegram/whatsapp, "target": id}

RSS_SOURCES = [
    "https://www.cybersecurity360.it/feed/",
    "https://www.redhotcyber.com/feed/",
    "https://www.commissariatodips.it/notizie/feed/",
    "https://www.acn.gov.it/notizie/feed"
]

SYSTEM_PROMPT = """
Sei 'Non Ci Casco Mai', un esperto di cybersecurity e analista antifrode.
Analizza il messaggio o l'immagine fornita e rispondi con questa struttura d'impatto, usando rigorosamente le emoji per evidenziare le sezioni:

🚨 VERDETTO: [🔴 TRUFFA / 🟡 SOSPETTO / 🟢 SICURO]

🔍 PERCHÉ È UNA TRUFFA:
(Spiega in modo chiaro e diretto il pericolo)

🧠 LEVA PSICOLOGICA USATA:
(Es. urgenza, paura, autorità, falsa convenienza)

🛡️ COSA FARE ORA:
(Istruzioni pratiche immediate per l'utente)
"""

def call_gemini_api_native(prompt, image_path=None):
    if not GEMINI_API_KEY:
        return "⚠️ Errore: GEMINI_API_KEY non configurata."
    
    models_to_try = [
        "gemini-3.6-flash",
        "gemini-3.7-flash",
        "gemini-3.5-flash"
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
        req = urllib.request.Request(tg_url, data=json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}).encode('utf-8'), headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Errore Telegram: {e}")

def send_telegram_channel_message(text):
    if not BOT_TOKEN or not TELEGRAM_CHANNEL_ID: return False
    try:
        tg_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHANNEL_ID, "text": text}
        req = urllib.request.Request(tg_url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        print(f"Errore invio canale Telegram: {e}")
        return False

def send_whatsapp_message(to_phone, text):
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_NUMBER_ID: return
    try:
        wa_url = f"https://graph.facebook.com/v21.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "text": {"body": text}
        }
        req = urllib.request.Request(wa_url, data=json.dumps(payload).encode('utf-8'), headers=headers, method="POST")
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Errore WhatsApp: {e}")

async def process_telegram_background(chat_id, msg):
    try:
        if "text" in msg:
            text_content = msg["text"]
            
            # 0. GENERAZIONE TOKEN SENTINELLA ANDROID (TELEGRAM)
            if text_content.startswith("/sentinella"):
                token = str(uuid.uuid4())[:8].upper()
                sentinella_tokens[token] = {"platform": "telegram", "target": chat_id}
                risposta = (
                    "🛡️ *Attivazione Sentinella Android*\n\n"
                    f"Il tuo Codice di Sicurezza (Token) personale è:\n`{token}`\n\n"
                    "👉 Copia questo codice e incollalo nell'app Android *Non Ci Casco Mai Sentinella* per collegare il tuo telefono!"
                )
                send_telegram_message(chat_id, risposta)
                return

            # 1. GENERAZIONE LINK MAGICO TELEGRAM
            if text_content.startswith("/proteggi"):
                link_magico = f"https://t.me/{BOT_USERNAME}?start=figlio_{chat_id}"
                risposta = (
                    "🛡️ *Family Guard Attivo (Telegram)*\n\n"
                    "Ecco il tuo *Link Magico* personale:\n"
                    f"{link_magico}\n\n"
                    "👉 *Inoltra questo link a tuo padre o a tua madre.* "
                    "Appena ci cliccheranno, si collegheranno in un tap alla tua linea protetta!"
                )
                send_telegram_message(chat_id, risposta)
                return

            # 2. AGGANCIO TRAMITE LINK MAGICO
            elif text_content.startswith("/start figlio_"):
                try:
                    figlio_id = text_content.split("_")[1]
                    famiglie_db[chat_id] = figlio_id
                    
                    msg_genitore = (
                        "✅ *Protezione Familiare Attivata con Successo!*\n\n"
                        "Da questo momento in poi, se ricevi messaggi strani o SMS sospetti, ti basta inoltrarli qui."
                    )
                    send_telegram_message(chat_id, msg_genitore)
                    
                    msg_figlio = "🎉 *Ottime notizie!* Un tuo familiare si è collegato alla tua linea protetta su Telegram."
                    send_telegram_message(int(figlio_id), msg_figlio)
                    return
                except Exception as e:
                    print(f"Errore associazione Telegram: {e}")

            # 3. GESTIONE LINEA PROTETTA TELEGRAM
            if chat_id in famiglie_db:
                figlio_id = famiglie_db[chat_id]
                res = perform_core_analysis(text_content=text_content)
                send_telegram_message(chat_id, res)
                
                avviso_figlio = (
                    "🚨 *ALLARME FAMILY GUARD* 🚨\n\n"
                    f"Il genitore protetto ha inviato questo contenuto:\n> \"{text_content}\"\n\n"
                    f"*Esito Analisi IA:*\n{res}"
                )
                send_telegram_message(int(figlio_id), avviso_figlio)
                return

            # 4. FLUSSO STANDARD
            res = perform_core_analysis(text_content=text_content)
            send_telegram_message(chat_id, res)
            
        elif "photo" in msg:
            send_telegram_message(chat_id, "Ricevuto! Analisi in corso...")
            photo = msg["photo"][-1]
            file_info = json.loads(urllib.request.urlopen(f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={photo['file_id']}").read().decode())
            down_path = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info['result']['file_path']}"
            temp_path = f"/tmp/{photo['file_id']}.jpg"
            urllib.request.urlretrieve(down_path, temp_path)
            res = perform_core_analysis(file_path=temp_path)
            
            if chat_id in famiglie_db:
                figlio_id = famiglie_db[chat_id]
                avviso_figlio = (
                    "🚨 *ALLARME FAMILY GUARD (SCREENSHOT)* 🚨\n\n"
                    "Il genitore protetto ha inviato uno screenshot.\n\n"
                    f"*Esito Analisi IA:*\n{res}"
                )
                send_telegram_message(int(figlio_id), avviso_figlio)
                
            send_telegram_message(chat_id, res)
    except Exception as e:
        print(f"Errore background task Telegram: {e}")

async def process_whatsapp_background(from_phone, msg):
    try:
        msg_type = msg.get("type")
        if msg_type == "text":
            text_body = msg.get("text", {}).get("body", "").strip()
            if text_body:
                
                # 0. ATTIVAZIONE SENTINELLA ANDROID (WHATSAPP)
                if text_body.lower() in ["sentinella", "/sentinella"]:
                    token = str(uuid.uuid4())[:8].upper()
                    sentinella_tokens[token] = {"platform": "whatsapp", "target": from_phone}
                    risposta_wa = (
                        "🛡️ *Attivazione Sentinella Android (WhatsApp)*\n\n"
                        f"Il tuo Codice di Sicurezza (Token) personale è:\n`{token}`\n\n"
                        "👉 Copia questo codice e incollalo nell'app Android *Non Ci Casco Mai Sentinella* per collegare il tuo telefono!"
                    )
                    send_whatsapp_message(from_phone, risposta_wa)
                    return

                # 1. ATTIVAZIONE FAMILY GUARD WHATSAPP
                if text_body.lower() == "proteggi":
                    istruzione = f"collega_{from_phone}"
                    risposta_wa = (
                        "🛡️ *Family Guard Attivo (WhatsApp)*\n\n"
                        "Per collegare un tuo familiare a questo numero protetto, fagli inviare esattamente questo messaggio:\n"
                        f"`{istruzione}`"
                    )
                    send_whatsapp_message(from_phone, risposta_wa)
                    return

                # 2. AGGANCIO DEL GENITORE TRAMITE CODICE
                elif text_body.startswith("collega_"):
                    try:
                        figlio_phone = text_body.split("_")[1].strip()
                        famiglie_wa_db[from_phone] = figlio_phone
                        
                        msg_genitore = (
                            "✅ *Protezione Familiare WhatsApp Attivata!*\n\n"
                            "Da questo momento in poi, se ricevi messaggi o link sospetti, inoltrarli qui e la tua famiglia verrà avvisata."
                        )
                        send_whatsapp_message(from_phone, msg_genitore)
                        
                        msg_figlio = "🎉 *Ottime notizie!* Un tuo familiare ha attivato la protezione collegandosi al tuo WhatsApp."
                        send_whatsapp_message(figlio_phone, msg_figlio)
                        return
                    except Exception as e:
                        print(f"Errore associazione WhatsApp: {e}")

                # 3. GESTIONE MESSAGGI DA LINEA PROTETTA WHATSAPP
                if from_phone in famiglie_wa_db:
                    figlio_phone = famiglie_wa_db[from_phone]
                    analysis_res = perform_core_analysis(text_content=text_body)
                    
                    send_whatsapp_message(from_phone, analysis_res)
                    
                    avviso_figlio = (
                        "🚨 *ALLARME FAMILY GUARD (WHATSAPP)* 🚨\n\n"
                        f"Il genitore protetto ha inviato questo contenuto:\n> \"{text_body}\"\n\n"
                        f"*Esito Analisi IA:*\n{analysis_res}"
                    )
                    send_whatsapp_message(figlio_phone, avviso_figlio)
                    return

                # 4. FLUSSO STANDARD WHATSAPP
                analysis_res = perform_core_analysis(text_content=text_body)
                send_whatsapp_message(from_phone, analysis_res)

        elif msg_type in ["image", "document"]:
            send_whatsapp_message(from_phone, "Ricevuto l'allegato! Analisi in corso...")
            media_data = msg.get(msg_type, {})
            media_id = media_data.get("id")
            
            if not media_id:
                send_whatsapp_message(from_phone, "⚠️ Errore: Impossibile leggere l'ID del file allegato.")
                return
                
            media_url_meta = f"https://graph.facebook.com/v21.0/{media_id}"
            headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
            req_media = urllib.request.Request(media_url_meta, headers=headers)
            
            with urllib.request.urlopen(req_media, timeout=10) as resp:
                media_info = json.loads(resp.read().decode())
                download_url = media_info.get("url")
            
            if download_url:
                req_dl = urllib.request.Request(download_url, headers=headers)
                temp_path = f"/tmp/wa_{media_id}.jpg"
                with urllib.request.urlopen(req_dl, timeout=15) as dl_resp, open(temp_path, "wb") as f_out:
                    f_out.write(dl_resp.read())
                
                analysis_res = perform_core_analysis(file_path=temp_path)
                
                if from_phone in famiglie_wa_db:
                    figlio_phone = famiglie_wa_db[from_phone]
                    avviso_figlio = (
                        "🚨 *ALLARME FAMILY GUARD (WHATSAPP - SCREENSHOT)* 🚨\n\n"
                        "Il genitore protetto ha inviato uno screenshot.\n\n"
                        f"*Esito Analisi IA:*\n{analysis_res}"
                    )
                    send_whatsapp_message(figlio_phone, avviso_figlio)
                    
                send_whatsapp_message(from_phone, analysis_res)
            else:
                send_whatsapp_message(from_phone, "⚠️ Errore: Impossibile ottenere l'URL di download da Meta.")
    except Exception as e:
        print(f"Errore background task WhatsApp: {e}")
        send_whatsapp_message(from_phone, "⚠️ Si è verificato un errore imprevisto durante l'analisi del file.")

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

# --- ROTTA UNIFICATA PER RICEVERE LE NOTIFICHE DALLA SENTINELLA ANDROID ---
@app.post("/api/sentinella")
@limiter.limit("30/minute")
async def api_sentinella(request: Request):
    try:
        data = await request.json()
        token = data.get("token", "").strip()
        notif_text = data.get("text", "").strip()
        app_name = data.get("package", "Notifica Android")
        
        if not token or not notif_text:
            return JSONResponse({"error": "Token o testo mancanti"}, status_code=400)
            
        target_info = sentinella_tokens.get(token)
        
        # Analisi IA della notifica intercettata
        analysis = perform_core_analysis(text_content=f"Notifica intercettata da {app_name}: {notif_text}")
        
        if target_info:
            platform = target_info.get("platform")
            target = target_info.get("target")
            
            if platform == "telegram":
                send_telegram_message(target, f"🚨 *ALLARME SENTINELLA ANDROID* 🚨\n\n{analysis}")
            elif platform == "whatsapp":
                send_whatsapp_message(target, f"🚨 *ALLARME SENTINELLA ANDROID (WHATSAPP)* 🚨\n\n{analysis}")
            
        return JSONResponse({"status": "success", "analisi": analysis})
    except Exception as e:
        return JSONResponse({"errore": str(e)}, status_code=500)

@app.get("/trigger-newsletter")
@limiter.limit("5/minute")
def trigger_newsletter(request: Request, token: str = ""):
    if NEWSLETTER_SECRET and token != NEWSLETTER_SECRET:
        return JSONResponse({"error": "Unauthorized"}, status_code=403)
        
    newsletter_prompt = """
    Sei 'Non Ci Casco Mai', un esperto di cybersecurity e analista antifrode. 
    Scrivi una pillola di sicurezza / bollettino antifrode inedito e di grande valore per il nostro canale Telegram. 
    Scegli una delle truffe più diffuse del momento in Italia (es. smishing dei corrieri, finto operatore bancario, phishing con QR code o falsi investimenti).
    La struttura deve essere:
    - Un titolo accattivante ed esplicativo con emoji (es. 🚨 ALLerta TRUFFA: ...)
    - Come agiscono i truffatori (il tranello)
    - I segnali d'allarme da cogliere al volo
    - La regola d'oro per difendersi
    Tono: Professionale, chiaro, d'impatto ma rassicurante. Lunghezza: compresa tra 800 e 1200 caratteri.
    """
    
    content = call_gemini_api_native(newsletter_prompt)
    if "⚠️" in content:
        return JSONResponse({"status": "error", "message": content}, status_code=500)
        
    success = send_telegram_channel_message(content)
    if success:
        return {"status": "success", "message": "Newsletter pubblicata sul canale con successo!"}
    else:
        return JSONResponse({"status": "error", "message": "Impossibile inviare il messaggio al canale Telegram. Verifica che il bot sia amministratore del canale."}, status_code=500)

@app.get("/check-rss")
@limiter.limit("5/minute")
def check_rss_feeds(request: Request, token: str = ""):
    if NEWSLETTER_SECRET and token != NEWSLETTER_SECRET:
        return JSONResponse({"error": "Unauthorized"}, status_code=403)
        
    published_count = 0
    for rss_url in RSS_SOURCES:
        try:
            req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                xml_data = response.read()
                
            root = ET.fromstring(xml_data)
            items = root.findall('.//item')[:3]
            
            for item in items:
                title = item.find('title').text if item.find('title') is not None else ""
                description = item.find('description').text if item.find('description') is not None else ""
                link = item.find('link').text if item.find('link') is not None else ""
                
                news_text = f"Titolo: {title}\nContenuto: {description}\nLink: {link}"
                
                filter_prompt = f"""
                Sei un esperto di cybersecurity e contrasto alle truffe digitali per il canale Telegram "Non Ci Casco Mai".
                Analizza questa notizia:
                {news_text}

                REGOLE:
                1. SCARTA COMPLETAMENTE la notizia se riguarda vulnerabilità software aziendali, patch di server, bug tecnici complessi o corporate governance non sfruttabili direttamente per truffe agli utenti comuni.
                2. ACCETTA solo se riguarda phishing, truffe telefoniche, frodi bancarie, furti d'identità, e-commerce truffaldini o allerte di pubblica utilità (Polizia Postale/ACN).
                Se la accetti, trasformala in un post per il canale Telegram strutturato così:
                - Titolo forte con emoji (es. 🚨 ATTENZIONE: ...)
                - Il meccanismo della truffa (2-3 frasi semplici)
                - Cosa fare / Consigli pratici di difesa
                Se non è pertinente, rispondi unicamente con la parola: SCARTA.
                """
                
                ai_response = call_gemini_api_native(filter_prompt)
                
                if ai_response and "SCARTA" not in ai_response and "⚠️" not in ai_response:
                    success = send_telegram_channel_message(ai_response)
                    if success:
                        published_count += 1
                    time.sleep(1)
        except Exception as e:
            print(f"Errore lettura RSS {rss_url}: {e}")
            
    return {"status": "success", "articoli_pubblicati": published_count}

@app.post("/analizza")
@limiter.limit("5/minute")
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
        return JSONResponse({"errore": str(e)}, status_code=500)

@app.post("/telegram")
@limiter.limit("30/minute")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
        if "message" not in data: return {"status": "ok"}
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        background_tasks.add_task(process_telegram_background, chat_id, msg)
    except Exception as e:
        print(f"Errore Telegram Webhook: {e}")
    return {"status": "ok"}

@app.get("/whatsapp")
@limiter.limit("30/minute")
def whatsapp_verify(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
        return int(challenge) if challenge and challenge.isdigit() else challenge
    return JSONResponse({"error": "Verification failed"}, status_code=403)

@app.post("/whatsapp")
@limiter.limit("30/minute")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
        entry = data.get("entry", [])
        for ent in entry:
            changes = ent.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                messages = value.get("messages", [])
                for msg in messages:
                    from_phone = msg.get("from")
                    background_tasks.add_task(process_whatsapp_background, from_phone, msg)
    except Exception as e:
        print(f"Errore WhatsApp Webhook: {e}")
    return {"status": "ok"}
