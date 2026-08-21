from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import os

app = FastAPI(title="NonCiCascoMai - Anti-Phishing Assistant")

# Modello dati per l'analisi tramite interfaccia web
class MessageRequest(BaseModel):
    message: str

def analyze_text(text: str) -> dict:
    """
    Logica di analisi euristica e simulazione controllo frodi.
    Qui puoi integrare la chiamata al modello LLM o le regole di pattern matching.
    """
    text_lower = text.lower()
    risk_score = 0
    warnings = []

    # Esempi di keyword sospette
    scam_keywords = ["agenzia delle entrate", "INPS", "pacco in giacenza", "vinto", "urgente", "clicca qui", "banca", "aggiorna i dati", "verifica il conto"]
    
    for kw in scam_keywords:
        if kw in text_lower:
            risk_score += 25
            warnings.append(f"Rilevata parola chiave sospetta: '{kw}'")

    if "http://" in text_lower or "https://" in text_lower:
        risk_score += 20
        warnings.append("Presente un link esterno (verificare attentamente il dominio).")

    if risk_score > 70:
        level = "ALTO RISCHIO - Possibile Tentativo di Truffa!"
    elif risk_score > 30:
        level = "RISCHIO MODERATO - Prestare attenzione."
    else:
        level = "Basso rischio apparente."

    return {
        "risk_score": min(risk_score, 100),
        "risk_level": level,
        "warnings": warnings if warnings else ["Nessuna minaccia evidente rilevata dai pattern di base."]
    }

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Interfaccia grafica web locale per testare i messaggi."""
    html_content = """
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NonCiCascoMai - Anti-Phishing Assistant</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #f4f7f6; color: #333; margin: 0; padding: 20px; display: flex; justify-content: center; }
            .container { width: 100%; max-width: 600px; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
            h1 { color: #2c3e50; font-size: 24px; margin-bottom: 5px; }
            .status { display: inline-block; width: 10px; height: 10px; background-color: #2ecc71; border-radius: 50%; margin-right: 5px; }
            .subtitle { color: #7f8c8d; font-size: 14px; margin-bottom: 25px; }
            textarea { width: 100%; height: 120px; padding: 12px; border: 1px solid #dcdde1; border-radius: 8px; font-size: 14px; resize: vertical; box-sizing: border-box; }
            button { background-color: #3498db; color: white; border: none; padding: 12px 20px; font-size: 16px; border-radius: 8px; cursor: pointer; width: 100%; margin-top: 15px; transition: background 0.2s; }
            button:hover { background-color: #2980b9; }
            #result { margin-top: 25px; padding: 15px; border-radius: 8px; background: #f8f9fa; border-left: 5px solid #bdc3c7; display: none; }
            .high-risk { border-left-color: #e74c3c !important; background: #fdeaea !important; }
            .med-risk { border-left-color: #f39c12 !important; background: #fef5e7 !important; }
            .low-risk { border-left-color: #2ecc71 !important; background: #eafaf1 !important; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛡️ NonCiCascoMai</h1>
            <div class="subtitle"><span class="status"></span>Sistema attivo e operativo</div>
            
            <label for="msg">Incolla qui il messaggio sospetto (SMS, WhatsApp, Email):</label>
            <textarea id="msg" placeholder="Es: Poste Italiane: accesso non autorizzato rilevato, clicca qui per sbloccare il conto..."></textarea>
            
            <button onclick="checkMessage()">Analizza Messaggio</button>
            
            <div id="result">
                <h3 id="res-title">Risultato</h3>
                <p id="res-level"><strong>Livello:</strong> <span></span></p>
                <ul id="res-warnings"></ul>
            </div>
        </div>

        <script>
            async function checkMessage() {
                const text = document.getElementById('msg').value;
                if (!text.trim()) {
                    alert('Inserisci un testo da analizzare.');
                    return;
                }

                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });

                const data = await response.json();
                const resultDiv = document.getElementById('result');
                const resLevel = document.getElementById('res-level').querySelector('span');
                const resWarnings = document.getElementById('res-warnings');
                
                resWarnings.innerHTML = '';
                data.warnings.forEach(w => {
                    const li = document.createElement('li');
                    li.textContent = w;
                    resWarnings.appendChild(li);
                });

                resLevel.textContent = data.risk_level;
                resultDiv.style.display = 'block';

                resultDiv.className = '';
                if (data.risk_score > 70) {
                    resultDiv.classList.add('high-risk');
                } else if (data.risk_score > 30) {
                    resultDiv.classList.add_('med-risk'); // Nota: fixato classe css pulita
                } else {
                    resultDiv.classList.add('low-risk');
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/analyze")
async def analyze_endpoint(payload: MessageRequest):
    """API endpoint per l'analisi dei messaggi."""
    result = analyze_text(payload.message)
    return JSONResponse(content=result)

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """Webhook predisposto per ricevere i messaggi da WhatsApp (Meta for Developers)."""
    body = await request.json()
    # Logica di estrazione messaggio da payload WhatsApp da implementare in base al formato Meta
    return {"status": "received"}

@app.get("/webhook/whatsapp")
async def verify_whatsapp(request: Request):
    """Verifica iniziale del webhook per la configurazione Meta."""
    params = request.query_params
    hub_mode = params.get("hub.mode")
    hub_challenge = params.get("hub.challenge")
    hub_verify_token = params.get("hub.verify_token")
    
    # Sostituisci "il_tuo_token_segreto" con quello impostato su Meta
    if hub_mode == "subscribe" and hub_verify_token == "il_tuo_token_segreto":
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Token di verifica non valido")
