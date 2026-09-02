import os
import json
import urllib.request
import urllib.parse
import base64
import time
from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from PIL import Image

app = FastAPI()

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

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
        "gemini-3.6-flash",
        "gemini-3.7-flash",
        "gemini-3.5-flash"
    ]
    
    parts = [{"text": prompt}]
    if image_path and os.path.exists(image_path):
        try:
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
def read_root():
    return """<!DOCTYPE html>
<html lang="it">
<head>
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-H698KT76PV"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-H698KT76PV');
    </script>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Non Ci Casco Mai | Verifica Truffe SMS, Pacco Nexi e Poste Info</title>
    <meta name="description" content="Verifica gratis truffe SMS, finti pacchi Nexi, allerte Poste Info e phishing online con Non Ci Casco Mai. Incolla il testo o l'immagine per scoprire se è una frode.">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #f4f7f6;
            color: #333;
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
        }
        .container {
            max-width: 650px;
            width: 100%;
            background: #ffffff;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            margin-top: 20px;
            box-sizing: border-box;
        }
        h1 { font-size: 26px; color: #1a1a1a; margin-bottom: 5px; text-align: center; }
        h2 { font-size: 18px; color: #333; border-bottom: 2px solid #007bff; padding-bottom: 8px; margin-top: 0; }
        h3.category-title { font-size: 15px; color: #555; margin: 20px 0 10px 0; text-transform: uppercase; letter-spacing: 0.5px; }
        p.subtitle { text-align: center; color: #666; font-size: 14px; margin-bottom: 25px; }
        textarea {
            width: 100%; height: 100px; padding: 12px; border: 1px solid #ccc;
            border-radius: 8px; font-size: 15px; resize: vertical; box-sizing: border-box; margin-bottom: 15px;
        }
        .file-upload {
            margin-bottom: 15px; font-size: 14px; color: #007bff; text-align: left;
        }
        input[type="file"] {
            display: block; margin-top: 5px; font-size: 14px; color: #333;
        }
        button {
            width: 100%; background-color: #007bff; color: white; border: none;
            padding: 12px; font-size: 16px; border-radius: 8px; cursor: pointer; font-weight: bold;
            transition: background 0.2s;
        }
        button:hover { background-color: #0056b3; }
        .spinner {
            border: 4px solid #f3f3f3; border-top: 4px solid #007bff; border-radius: 50%;
            width: 32px; height: 32px; animation: spin 1s linear infinite; margin: 15px auto;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        #risultato {
            margin-top: 25px; padding: 15px; border-radius: 8px; background: #f9f9f9;
            border: 1px solid #e0e0e0; display: none; white-space: pre-line; font-size: 15px; line-height: 1.5;
        }
        .alert-card {
            background: #fff8f8;
            border-left: 4px solid #dc3545;
            padding: 12px 15px;
            margin-bottom: 12px;
            border-radius: 0 8px 8px 0;
            font-size: 14px;
        }
        .alert-card h4 { margin: 0 0 5px 0; color: #dc3545; font-size: 15px; }
        .alert-card p { margin: 0; color: #555; line-height: 1.4; }
        .category-grid { display: flex; gap: 10px; margin-bottom: 20px; justify-content: center; flex-wrap: wrap; }
        .cat-item { background: #e7f1ff; color: #007bff; padding: 5px 15px; border-radius: 20px; font-size: 12px; font-weight: bold; }
        .seo-section {
            margin-top: 30px; font-size: 13px; color: #777; text-align: center; border-top: 1px solid #eee; padding-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ Non Ci Casco Mai</h1>
        <p class="subtitle">Incolla un testo, una chat o carica uno screenshot per analizzare subito qualsiasi rischio di frode.</p>
        
        <textarea id="testoMessaggio" placeholder="Incolla il testo del messaggio, l'annuncio o la chat con il venditore..."></textarea>
        
        <div class="file-upload">
            <label for="imageInput">📸 Oppure carica uno screenshot (chat o SMS):</label>
            <input type="file" id="imageInput" accept="image/*">
        </div>

        <button onclick="analizzaMessaggio()">Analizza Contenuto</button>

        <div id="risultato"></div>
    </div>

    <div class="container">
        <h2>🚨 Truffe del Momento in Italia</h2>
        <p class="subtitle">Le allerte più segnalate per riconoscere phishing e raggiri commerciali.</p>

        <div class="category-grid">
            <div class="cat-item">📱 Phishing & Messaggi</div>
            <div class="cat-item">🛒 Marketplace & Vendite</div>
            <div class="cat-item">💰 Investimenti</div>
        </div>

        <h3 class="category-title">📱 Phishing & Messaggi Ingannevoli</h3>

        <div class="alert-card">
            <h4>📦 La Truffa del Finto Pacco Nexi</h4>
            <p>SMS fraudolenti che segnalano un pacco bloccato o in giacenza a nome Nexi, con link che imitano i canali ufficiali e puntano a svuotare la carta di credito.</p>
        </div>

        <div class="alert-card">
            <h4>✉️ Finti SMS "Poste Info"</h4>
            <p>Messaggi ingannevoli camuffati da comunicazioni ufficiali Poste Info o BancoPosta, che parlano di transazioni sospette o blocchi temporanei del conto.</p>
        </div>

        <div class="alert-card">
            <h4>📦 La Truffa del Finto Corriere</h4>
            <p>SMS che annunciano *"Pacco in giacenza, clicca sul link per aggiornare l'indirizzo"*, chiedendo un piccolo micro-pagamento con carta per sbloccarlo.</p>
        </div>

        <div class="alert-card">
            <h4>🏦 Il Blocco del Conto Bancario o Postale</h4>
            <p>Finti allarmi sulla sicurezza del conto che invitano a cliccare su link contraffatti per inserire le credenziali di accesso.</p>
        </div>

        <h3 class="category-title">🛒 Finti Annunci & Marketplace</h3>

        <div class="alert-card">
            <h4>🏷️ Il Finto Venditore su Marketplace / Social</h4>
            <p>Oggetti in vendita a prezzi molto vantaggiosi. Il venditore insiste per spostare la chat fuori dalla piattaforma o chiede pagamenti non tracciabili.</p>
        </div>
    </div>

    <div class="container seo-section">
        <h3>Protezione digitale a 360 gradi con Non Ci Casco Mai</h3>
        <p>Usa il nostro <strong>verificatore phishing online</strong> per bloccare tentativi di frode e comprare in totale sicurezza.</p>
    </div>

    <script>
        async function analizzaMessaggio() {
            const testo = document.getElementById('testoMessaggio').value;
            const imageInput = document.getElementById('imageInput').files[0];
            const divRisultato = document.getElementById('risultato');
            
            if (!testo.trim() && !imageInput) {
                alert('Inserisci un messaggio o seleziona uno screenshot.');
                return;
            }

            divRisultato.style.display = 'block';
            divRisultato.innerHTML = `
                <div style="text-align: center;">
                    <div class="spinner"></div>
                    <p style="color: #555; font-size: 14px; margin: 0;">Analisi in corso con Non Ci Casco Mai...</p>
                </div>
            `;

            let base64Image = null;

            if (imageInput) {
                const reader = new FileReader();
                reader.readAsDataURL(imageInput);
                reader.onload = async function () {
                    base64Image = reader.result.split(',')[1];
                    inviaRichiesta(testo, base64Image);
                };
            } else {
                inviaRichiesta(testo, null);
            }
        }

        async function inviaRichiesta(testo, image) {
            const divRisultato = document.getElementById('risultato');
            try {
                const response = await fetch('/analizza', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ testo: testo, image: image })
                });
                
                const data = await response.json();
                if (data.errore) {
                    divRisultato.innerHTML = '<span style="color: red;">Errore: ' + data.errore + '</span>';
                } else {
                    divRisultato.innerHTML = data.risultato;
                }
            } catch (error) {
                divRisultato.innerHTML = '<span style="color: red;">Errore di connessione al server.</span>';
            }
        }
    </script>
</body>
</html>"""

@app.post("/analizza")
async def web_analizza(data: dict):
    try:
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
        return JSONResponse({"errore": str(e)})

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
            down_path = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info['result']['file_path']}]"
            temp_path = f"/tmp/{photo['file_id']}.jpg"
            urllib.request.urlretrieve(down_path, temp_path)
            send_telegram_message(chat_id, perform_core_analysis(file_path=temp_path))
    except Exception as e:
        print(f"Errore Telegram: {e}")
    return {"status": "ok"}
