import os
from fastapi import FastAPI, Request
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

class SegnalazioneRequest(BaseModel):
    testo: str

@app.post("/analizza")
async def analizza_messaggio(payload: SegnalazioneRequest):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Sei un assistente esperto in cybersecurity e prevenzione delle truffe digitali (phishing, smishing, "
                    "truffe finanziarie, finti corrieri). Analizza il messaggio fornito dall'utente. "
                    "Restituisci una risposta strutturata in questo modo:\n"
                    "1. **Livello di Rischio:** (Basso / Medio / Alto / CERTA TRUFFA)\n"
                    "2. **Motivazione:** Spiega in modo chiaro e semplice perché è sospetto o sicuro.\n"
                    "3. **Consiglio Pratico:** Cosa deve fare l'utente."
                )
            },
            {
                "role": "user",
                "content": payload.testo
            }
        ],
        temperature=0.2,
        max_tokens=300
    )
    
    risultato = response.choices[0].message.content
    return {"risultato_analisi": risultato}

@app.get("/")
def home():
    return {"status": "Bot Anti-Truffa attivo e operativo!"}
