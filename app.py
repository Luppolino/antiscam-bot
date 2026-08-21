from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

# Token segreto per la verifica di Meta (WhatsApp)
VERIFY_TOKEN = "antiscam_token_segreto_123"

# 1. Pagina principale grafica in HTML con interfaccia di analisi
@app.get("/", response_class=HTMLResponse)
def read_root():
    html_content = """
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NonCiCascoMai - Antiscam Bot</title>
        <style>
            :root {
                --bg-color: #0f172a;
                --card-bg: #1e293b;
                --text-color: #f8fafc;
                --text-muted: #94a3b8;
                --accent: #38bdf8;
                --accent-hover: #0ea5e9;
                --border: #334155;
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
                margin-top: 20px;
            }
            .card {
                background-color: var(--card-bg);
                padding: 30px;
                border-radius: 16px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.5);
                border: 1px solid var(--border);
            }
            h1 {
                color: var(--accent);
                margin-top: 0;
                font-size: 24px;
                text-align: center;
            }
            p.subtitle {
                color: var(--text-muted);
                text-align: center;
                margin-bottom: 25px;
                font-size: 14px;
            }
            .input-group {
                margin-bottom: 20px;
            }
            label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                font-size: 14px;
            }
            textarea {
                width: 100%;
                height: 120px;
                padding: 12px;
                border-radius: 8px;
                border: 1px solid var(--border);
                background-color: #0f172a;
                color: var(--text-color);
                resize: vertical;
                font-size: 14px;
                box-sizing: border-box;
            }
            textarea:focus {
                outline: none;
                border-color: var(--accent);
            }
            button {
                width: 100%;
                background-color: var(--accent);
                color: #0f172a;
                border: none;
                padding: 14px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 16px;
                cursor: pointer;
                transition: background-color 0.2s;
            }
            button:hover {
                background-color: var(--accent-hover);
            }
            .status {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                background-color: rgba(34, 197, 94, 0.1);
                color: #22c55e;
                padding: 8px 14px;
                border-radius: 20px;
                font-size: 13px;
                margin-bottom: 20px;
                border: 1px solid rgba(34, 197, 94, 0.2);
                font-weight: 600;
            }
            .dot {
                height: 8px;
                width: 8px;
                background-color: #22c55e;
                border-radius: 50%;
                display: inline-block;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <div class="status">
                    <span class="dot"></span> Sistema Operativo e Online
                </div>
                <h1>NonCiCascoMai</h1>
                <p class="subtitle">Il tuo scudo personale contro truffe, phishing e raggiri online.</p>
                
                <div class="input-group">
                    <label for="scamText">Incolla qui il testo del messaggio sospetto:</label>
                    <textarea id="scamText" placeholder="Es. Ciao! Poste Italiane: il tuo conto è bloccato, clicca qui per sbloccarlo..."></textarea>
                </div>
                
                <button onclick="alert('Funzione di analisi pronta! Collegheremo presto l\\'intelligenza artificiale.')">Analizza Contenuto</button>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

# 2. Webhook WhatsApp (GET per la verifica di Meta)
@app.get("/webhook")
async def verify_whatsapp(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return Response(content=challenge, media_type="text/plain")
        else:
            return Response(content="Token non valido", status_code=403)
    return Response(content="Parametri mancanti", status_code=400)

# 3. Webhook WhatsApp (POST per ricevere i messaggi)
@app.post("/webhook")
async def receive_whatsapp(request: Request):
    body = await request.json()
    print("Messaggio WhatsApp ricevuto:", body)
    return {"status": "EVENT_RECEIVED"}

# 4. Webhook Telegram (POST per ricevere i messaggi dal bot Telegram)
@app.post("/telegram-webhook")
async def receive_telegram(request: Request):
    body = await request.json()
    print("Messaggio Telegram ricevuto:", body)
    return {"status": "TELEGRAM_RECEIVED"}

# Avvio del server per Render sulla porta 10000
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=10000)
