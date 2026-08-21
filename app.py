from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

# Token segreto per la verifica di Meta (WhatsApp)
VERIFY_TOKEN = "antiscam_token_segreto_123"

# 1. Pagina principale grafica (Tema Chiaro, Accattivante e Illustrazione Personalizzata)
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
                --bg-color: #f8fafc;
                --card-bg: #ffffff;
                --text-color: #1e293b;
                --text-muted: #64748b;
                --accent: #0284c7;
                --accent-hover: #0369a1;
                --border: #e2e8f0;
                --danger: #ef4444;
                --success-bg: #f0fdf4;
                --success-text: #16a34a;
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
            /* Icona Mostriciattolo Pescatore Personalizzata */
            .logo-container {
                width: 90px;
                height: 90px;
                background: linear-gradient(1355deg, #e0f2fe 0%, #bae6fd 100%);
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
                transition: border-color 0.2s;
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
                transition: background-color 0.2s;
            }
            .file-upload:hover {
                background-color: #f1f5f9;
            }
            .file-upload input {
                display: none;
            }
            .file-upload label {
                cursor: pointer;
                color: var(--text-muted);
                margin: 0;
                font-size: 14px;
                font-weight: normal;
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
                transition: background-color 0.2s, transform 0.1s;
                box-shadow: 0 4px 12px rgba(2, 132, 199, 0.2);
            }
            button.action-btn:hover {
                background-color: var(--accent-hover);
            }
            .status {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                background-color: var(--success-bg);
                color: var(--success-text);
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
                background-color: var(--success-text);
                border-radius: 50%;
                display: inline-block;
            }
            /* Bacheca delle truffe */
            .board-title {
                font-size: 17px;
                color: #0f172a;
                margin-bottom: 15px;
                display: flex;
                align-items: center;
                gap: 8px;
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
            <!-- Box Principale Analisi -->
            <div class="card">
                <div class="status">
                    <span class="dot"></span> Sistema Operativo e Online
                </div>
                
                <!-- Icona Mostriciattolo Pescatore (Ispirata al concept pulito) -->
                <div class="logo-container">
                    <svg viewBox="0 0 24 24">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
                    </svg>
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
                
                <button class="action-btn" onclick="alert('Funzione di analisi (Testo + OCR) pronta!')">Analizza Contenuto</button>
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
                    <p>False comunicazioni su presunte anomalie o scadenze. Ricorda che l'Agenzia non invia mai link diretti o richieste di pagamento via SMS.</p>
                </div>

                <div class="scam-alert">
                    <h4>Truffe su Marketplace (Subito, Vinted, FB)</h4>
                    <p>Venditori o acquirenti che chiedono di spostare la chat su WhatsApp o mandano link di pagamento falsi fingendosi il corriere.</p>
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
