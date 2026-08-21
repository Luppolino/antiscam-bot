from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

# Token segreto per la verifica di Meta (WhatsApp)
VERIFY_TOKEN = "antiscam_token_segreto_123"

# 1. Pagina principale grafica con Interfaccia di Analisi (Testo + Screenshot OCR) e Bacheca
@app.get("/", response_class=HTMLResponse)
def read_root():
    html_content = """
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NonCiCascoMai - Il tuo scudo anti-truffa</title>
        <style>
            :root {
                --bg-color: #0f172a;
                --card-bg: #1e293b;
                --text-color: #f8fafc;
                --text-muted: #94a3b8;
                --accent: #38bdf8;
                --accent-hover: #0ea5e9;
                --border: #334155;
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
                max-width: 650px;
                margin-top: 10px;
                margin-bottom: 40px;
            }
            .card {
                background-color: var(--card-bg);
                padding: 30px;
                border-radius: 16px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.5);
                border: 1px solid var(--border);
                margin-bottom: 25px;
            }
            h1 {
                color: var(--accent);
                margin-top: 0;
                font-size: 26px;
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
                height: 100px;
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
            .file-upload {
                border: 2px dashed var(--border);
                padding: 15px;
                border-radius: 8px;
                text-align: center;
                background-color: #0f172a;
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
            /* Bacheca delle truffe */
            .board-title {
                font-size: 18px;
                color: var(--accent);
                margin-bottom: 15px;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .scam-alert {
                background-color: rgba(239, 68, 68, 0.1);
                border-left: 4px solid var(--danger);
                padding: 12px 15px;
                border-radius: 0 8px 8px 0;
                margin-bottom: 12px;
                font-size: 13px;
            }
            .scam-alert h4 {
                margin: 0 0 5px 0;
                color: #fca5a5;
                font-size: 14px;
            }
            .scam-alert p {
                margin: 0;
                color: var(--text-muted);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Box Principale Analisi (Testo + OCR Screenshot) -->
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

                <div class="input-group">
                    <label>Oppure carica uno screenshot (Riconoscimento OCR):</label>
                    <div class="file-upload" onclick="document.getElementById('screenshotFile').click()">
                        <label for="screenshotFile">📷 Clicca qui per selezionare un'immagine o uno screenshot</label>
                        <input type="file" id="screenshotFile" accept="image/*">
                    </div>
                </div>
                
                <button onclick="alert('Funzione di analisi (Testo + OCR) pronta!')">Analizza Contenuto</button>
            </div>

            <!-- Bacheca Ultime Truffe -->
            <div class="card">
                <div class="board-title">🚨 Bacheca Allerte & Ultime Truffe</div>
                
                <div class="scam-alert">
                    <h4>Finto SMS Poste / Corriere (Pacco in giacenza)</h4>
                    <p>Messaggi che invitano a pagare 1,99€ per sbloccare una spedizione o aggiornare i dati del conto. Non cliccare mai sui link abbreviati.</p>
                </div>

                <div class="scam-alert">
                    <h4>Campagna Phishing Agenzia delle Entrate</h4>
                    <p>False comunicazioni su presunte anomalie o scadenze per cripto-asset e dichiarazioni. Ricorda che l'Agenzia non invia mai link diretti via SMS.</p>
                </div>

                <div class="scam-alert">
                    <h4>Truffe su Marketplace (Subito, Vinted, FB)</h4>
                    <p>Venditori o acquirenti che chiedono di spostare la chat su WhatsApp o mandano link di pagamento falsi (es. finto escrow).</p>
                </div>
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
