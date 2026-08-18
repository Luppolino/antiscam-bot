import os
import re
from flask import Flask, jsonify, render_template, request
from openai import OpenAI
import requests

app = Flask(__name__)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

def maschera_dati_sensibili(testo):
    testo = re.sub(r'[A-Z]{2}\d{2}[A-Z0-9]{10,30}', '[IBAN_OSCURATO]', testo)
    testo = re.sub(r'\b(?:\+39)?\s?3\d{2}\s?\d{6,7}\b', '[NUMERO_OSCURATO]', testo)
    testo = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '[CARTA_OSCURATA]', testo)
    return testo

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analizza', methods=['POST'])
def analizza():
    dati = request.get_json()
    testo_utente = dati.get('testo', '')
    
    if not testo_utente.strip():
        return jsonify({'errore': 'Inserisci un messaggio da analizzare.'}), 400

    testo_pulito = maschera_dati_sensibili(testo_utente)

    system_prompt = """
    Sei un assistente esperto in cybersecurity e prevenzione delle truffe digitali in Italia.
    Analizza il messaggio ricevuto e rispondi ESCLUSIVAMENTE in formato JSON con questa struttura esatta:
    {
      "livello_rischio": "Basso" o "Sospetto" o "Alto",
      "spiegazione": "Breve spiegazione in 2 frasi dei segnali di pericolo riscontrati.",
      "azione_consigliata": "Cosa deve fare concretamente l'utente."
    }
    Non aggiungere altro testo fuori dal formato JSON.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": testo_pulito}
            ],
            response_format={ "type": "json_object" }
        )
        return response.choices[0].message.content
    except Exception as e:
        return jsonify({'errore': 'Errore durante l\'analisi del messaggio.'}), 500

@app.route('/telegram', methods=['POST'])
def telegram_bot():
    data = request.get_json()
    if data and "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        testo_utente = data["message"]["text"]
        
        if testo_utente.startswith('/start'):
            risposta = "Ciao! Sono il tuo assistente anti-truffa. Incolla qui qualsiasi SMS, email o messaggio sospetto e ti dirò subito se è sicuro o un tentativo di phishing."
        else:
            testo_pulito = maschera_dati_sensibili(testo_utente)
            system_prompt = """
            Sei un assistente esperto in cybersecurity e prevenzione delle truffe digitali in Italia.
            Analizza il messaggio ricevuto e rispondi in modo chiaro e diretto per Telegram con questa struttura:
            ⚠️ RISCHIO: [Basso / Sospetto / Alto]
            📋 SPIEGAZIONE: Breve spiegazione dei pericoli.
            💡 COSA FARE: Azione concreta per l'utente.
            """
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": testo_pulito}
                    ]
                )
                risposta = response.choices[0].message.content
            except Exception as e:
                risposta = "Errore tecnico durante l'analisi del messaggio."
        
        if TELEGRAM_TOKEN:
            requests.post(TELEGRAM_API_URL, json={"chat_id": chat_id, "text": risposta})
            
    return "OK", 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
