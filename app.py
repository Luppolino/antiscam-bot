from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

# Token segreto per la verifica di Meta (WhatsApp)
VERIFY_TOKEN = "antiscam_token_segreto_123"

# 1. Pagina principale grafica in HTML
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
            body {
                font-family: Arial, sans-serif;
                background-color: #0f172a;
                color: #f8fafc;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
            }
            .card {
                background-color: #1e293b;
                padding: 40px;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.5);
                text-align: center;
                max-width: 500px;
            }
            h1 { color: #38bdf8; margin-bottom: 10px; }
            p { color: #94a3b8; }
            .status {
                display: inline-block;
                background-color: #22c55e;
                color: white;
                padding: 6px 14px;
                border-radius: 20px;
                font-size: 14px;
                margin-top: 20px;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>NonCiCascoMai</h1>
            <p>Il tuo assistente intelligente anti-truffa per Telegram e WhatsApp.</p>
            <div class="status">● Sistema Operativo e Online</div>
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
