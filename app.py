from fastapi import FastAPI, Request, Response
from pydantic import BaseModel
import os

app = FastAPI()

# Token segreto per la verifica di Meta (puoi cambiarlo con quello che preferisci)
VERIFY_TOKEN = "antiscam_token_segreto_123"

@app.get("/")
def read_root():
    return {"status": "Antiscam Bot is live!"}

# 1. Rotta GET per la verifica iniziale del webhook da parte di Meta
@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            # Restituisce la challenge come intero/stringa richiesta da Meta
            return Response(content=challenge, media_type="text/plain")
        else:
            return Response(content="Token non valido", status_code=403)
    return Response(content="Parametri mancanti", status_code=400)

# 2. Rotta POST per ricevere i messaggi veri e propri da WhatsApp
@app.post("/webhook")
async def receive_webhook(request: Request):
    body = await request.json()
    
    # Qui puoi stampare o elaborare il messaggio in arrivo
    print("Messaggio ricevuto da WhatsApp:", body)
    
    # Risposta obbligatoria per confermare a Meta la ricezione
    return {"status": "EVENT_RECEIVED"}
