import os
import httpx
from fastapi import FastAPI, Request, Response, UploadFile, File, Form
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

# Configurazioni e chiavi
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
VERIFY_TOKEN = "antiscam_token_segreto_123"

# Funzione blindata per interrogare Gemini via HTTP con il modello corretto gemini-3.6-flash
async def ask_gemini(prompt_text: str):
    if not GEMINI_API_KEY:
        return "Errore: API Key di Gemini non configurata su Render."
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}]
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=25.0)
            data = response.json()
            
            if "candidates" in data and len(data["candidates"]) > 0:
                candidate = data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    return candidate["content"]["parts"][0]["text"]
            
            if "error" in data:
                return f"Errore restituito da Google: {data['error'].get('message', 'Sconosciuto')}"
                
            return "Impossibile elaborare la risposta dall'intelligenza artificiale. Riprova."
        except Exception as e:
            return f"Errore di connessione con l'IA: {str(e)}"

# 1. Pagina principale del sito web
@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NonCiCascoMai - Il tuo scudo anti-truffa</title>
        <style>
            :root {
                --bg-color: #f8fafc;
                --card-bg: #ffffff;
                --text-color: #1e293b;
                --text-muted: #64748b;
                --accent: #0284c7;
                --accent-hover: #0369a1;
                --border: #e2e8f0;
                --danger: #ef4444;
            }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: var(--bg-color);
                color: var(--text-color);
                margin: 0;
                padding: 20px;
                display: flex;
                flex-direction: column;
                align-items: center;
                min-height: 100vh;
            }
            .container {
                width: 100%;
                max-width: 600px;
                margin-top: 10px;
                margin-bottom: 40px;
            }
            .card {
                background-color: var(--card-bg);
                padding: 35px 30px;
                border-radius: 20px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.05);
                border: 1px solid var(--border);
                margin-bottom: 25px;
                text-align: center;
            }
            .logo-container {
                width: 90px;
                height: 90px;
                background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 20px auto;
                box-shadow: 0 4px 12px rgba(2, 132, 199, 0.15);
            }
            .logo-container svg {
                width: 50px;
                height: 50px;
                fill: #0284c7;
            }
            h1 {
                color: #0f172a;
                margin-top: 0;
                font-size: 26px;
                font-weight: 700;
            }
            p.subtitle {
                color: var(--text-muted);
                margin-bottom: 25px;
                font-size: 15px;
                line-height: 1.5;
            }
            .input-group {
                margin-bottom: 20px;
                text-align: left;
            }
            label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                font-size: 14px;
                color: #334155;
            }
            textarea {
                width: 100%;
                height: 110px;
                padding: 12px;
                border-radius: 10px;
                border: 1px solid var(--border);
                background-color: #f8fafc;
                color: var(--text-color);
                resize: vertical;
                font-size: 14px;
                box-sizing: border-box;
            }
            textarea:focus {
                outline: none;
                border-color: var(--accent);
                background-color: #ffffff;
            }
            .file-upload {
                border: 2px dashed #cbd5e1;
                padding: 15px;
                border-radius: 10px;
                text-align: center;
                background-color: #f8fafc;
                cursor: pointer;
                margin-bottom: 20px;
            }
            .file-upload input {
                display: none;
            }
            .file-upload label {
                cursor: pointer;
                color: var(--text-muted);
                margin: 0;
                font-size: 14px;
            }
            button.action-btn {
                width: 100%;
                background-color: var(--accent);
                color: #ffffff;
                border: none;
                padding: 14px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 16px;
                cursor: pointer;
                box-shadow: 0 4px 12px rgba(2, 132, 199, 0.2);
            }
            button.action-btn:hover {
                background-color: var(--accent-hover);
            }
            .status {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                background-color: #f0fdf4;
                color: #16a34a;
                padding: 6px 14px;
                border-radius: 20px;
                font-size: 13px;
                margin-bottom: 20px;
                border: 1px solid rgba(22, 163, 74, 0.2);
                font-weight: 600;
            }
            .dot {
                height: 8px;
                width: 8px;
                background-color: #16a34a;
                border-radius: 50%;
                display: inline-block;
            }
            #resultBox {
                margin-top: 20px;
                padding: 15px;
                border-radius: 10px;
                background-color: #f1f5f9;
                text-align: left;
                display: none;
                font-size: 14px;
                line-height: 1.5;
                border: 1px solid var(--border);
                white-space: pre-wrap;
            }
            .board-title {
                font-size: 17px;
                color: #0f172a;
                margin-bottom: 15px;
                font-weight: 700;
                text-align: left;
            }
            .scam-alert {
                background-color: #fff1f2;
                border-left: 4px solid var(--danger);
                padding: 14px 16px;
                border-radius: 0 10px 10px 0;
                margin-bottom: 12px;
                font-size: 13px;
                text-align: left;
            }
            .scam-alert h4 {
                margin: 0 0 5px 0;
                color: #991b1b;
                font-size: 14px;
                font-weight: 700;
            }
            .scam-alert p {
                margin: 0;
                color: #475569;
                line-height: 1.4;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <div class="status"><span class="dot"></span> Sistema Operativo e Online</div>
                <div class="logo-container">
                    <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
                </div>
                <h1>NonCiCascoMai</h1>
                <p class="subtitle">Il tuo scudo personale contro truffe, phishing e raggiri online.</p>
                
                <div class="input-group">
                    <label for="scamText">Incolla qui il testo del messaggio sospetto:</label>
                    <textarea id="scamText" placeholder="Es. Ciao! Poste Italiane: il tuo conto è bloccato..."></textarea>
                </div>

                <div class="input-group">
                    <label>Oppure carica uno screenshot:</label>
                    <div class="file-upload" onclick="document.getElementById('screenshotFile').click()">
                        <label id="fileLabel" for="screenshotFile">📷 Clicca qui per selezionare un'immagine</label>
                        <input type="file" id="screenshotFile" accept="image/*" onchange="updateFileName()">
                    </div>
                </div>
                
                <button class="action-btn" onclick="analyzeContent()">Analizza Contenuto</button>
                <div id="resultBox"></div>
            </div>

            <div class="card">
                <div class="board-title">🚨 Bacheca Allerte & Ultime Truffe</div>
                <div class="scam-alert">
                    <h4>Finto SMS Poste / Corriere</h4>
                    <p>Messaggi che invitano a pagare piccole somme per sbloccare spedizioni. Non cliccare mai.</p>
                </div>
            </div>
        </div>

        <script>
            function updateFileName() {
                const input = document.getElementById('screenshotFile');
                const label = document.getElementById('fileLabel');
                if (input.files && input.files[0]) {
                    label.textContent = "📎 Selezionato: " + input.files[0].name;
                }
            }

            async function analyzeContent() {
                const text = document.getElementById('scamText').value;
                const fileInput = document.getElementById('screenshotFile');
                const resultBox = document.getElementById('resultBox');

                if (!text && (!fileInput.files || fileInput.files.length === 0)) {
                    alert("Inserisci un testo o carica uno screenshot.");
                    return;
                }

                resultBox.style.display = "block";
                resultBox.textContent = "Analisi in corso con l'intelligenza artificiale...";

                const formData = new FormData();
                formData.append("text", text);
                if (fileInput.files[0]) {
                    formData.append("file", fileInput.files[0]);
                }

                try {
                    const response = await fetch('/api/analyze', { method: 'POST', body: formData });
                    const data = await response.json();
                    if (data.success) {
                        resultBox.textContent = data.result;
                    } else {
                        resultBox.textContent = "Errore: " + (data.error || "Riprova.");
                    }
                } catch (err) {
                    resultBox.textContent = "Errore di connessione al server.";
                }
            }
        </script>
    </body>
    </html>
    """

# 2. API di Analisi per il sito web
@app.post("/api/analyze")
async def analyze_api(text: str = Form(None), file: UploadFile = File(None)):
    try:
        content_to_analyze = text or ""
        if file:
            content_to_analyze += " [L'utente ha caricato uno screenshot o un'immagine nel sito]"

        prompt = (
            "Sei un assistente esperto di cybersecurity e antitruffa. Analizza il seguente contenuto "
            f"e dimmi chiaramente se si tratta di truffa o phishing: '{content_to_analyze}'. "
            "Struttura la risposta in 3 punti: 1. Verdetto, 2. Perché, 3. Cosa fare."
        )

        result_text = await ask_gemini(prompt)
        return {"success": True, "result": result_text}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Funzione comune per gestire i messaggi di Telegram
async def process_telegram_update(request: Request):
    try:
        body = await request.json()
        message = body.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text")

        if chat_id and text and TELEGRAM_TOKEN:
            prompt = (
                "Sei NonCiCascoMai, un bot assistente esperto di cybersecurity e antitruffa. "
                "Analizza questo messaggio inviato da un utente su Telegram e rispondi in modo chiaro: "
                "1. Verdetto (Sicuro / Sospetto / TRUFFA ACCERTATA) "
                "2. Perché "
                "3. Cosa fare. "
                f"Messaggio: {text}"
            )
            
            reply_text = await ask_gemini(prompt)
            
            async with httpx.AsyncClient() as http_client:
                await http_client.post(
                    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                    json={"chat_id": chat_id, "text": reply_text}
                )
    except Exception as e:
        print("Errore Telegram:", e)
    return {"status": "OK"}

# 3. Webhook Telegram
@app.post("/telegram")
async def telegram_webhook_short(request: Request):
    return await process_telegram_update(request)

@app.post("/telegram-webhook")
async def telegram_webhook_long(request: Request):
    return await process_telegram_update(request)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=10000)
