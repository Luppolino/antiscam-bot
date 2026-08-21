import os
from fastapi import FastAPI, Request, Response

app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "segreto123")

@app.get("/")
def home():
    return {"status": "Antiscam Bot is live!"}

# Rotta di verifica per Meta (Metodo GET)
@app.get("/webhook")
async def verify_webhook(request: Request):
    query_params = request.query_params
    mode = query_params.get("hub.mode")
    token = query_params.get("hub.verify_token")
    challenge = query_params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("Webhook verificato con successo!")
            return Response(content=challenge, media_type="text/plain")
        else:
            return Response(content="Token non valido", status_code=403)
    
    return Response(content="Parametri mancanti", status_code=400)

# Rotta per ricevere i messaggi (Metodo POST)
@app.post("/webhook")
async def receive_message(request: Request):
    body = await request.json()
    print("Messaggio ricevuto:", body)
    return {"status": "EVENT_RECEIVED"}
