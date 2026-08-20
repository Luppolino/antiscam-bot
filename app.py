import base64
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

def analizza_con_ia(testo=None, image_base64=None):
    system_prompt = """
    Sei un assistente esperto in cybersecurity e prevenzione delle truffe digitali in Italia.
    Analizza il testo o l'immagine ricevuta e rispondi in modo chiaro e diretto con questa struttura:
    ⚠️ RISCHIO: [Basso / Sospetto / Alto]
    📋 SPIEGAZIONE: Breve spiegazione dei pericoli.
    💡 COSA FARE: Azione concreta per l'utente.
    """
    
    content = [{"type": "text", "text": "Analizza questo contenuto per individuare eventuali truffe o tentativi di phishing:"}]
    
    if testo:
        testo_pulito = maschera_dati_sensibili(testo)
        content[0]["text"] += f"\nTesto: {testo_pulito}"
        
    if image_base64:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
        })

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ]
    )
    return response.choices[0].message.content

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analizza', methods=['POST'])
def analizza():
    dati = request.get_json()
    testo = dati.get('testo', '')
    image_base64 = dati.get('image', None)
    
    if not testo.strip() and not image_base64:
        return jsonify({'errore': 'Inserisci un messaggio o carica uno screenshot.'}), 400

    try:
        risultato = analizza_con_ia(testo=testo, image_base64=image_base64)
        return jsonify({'risultato': risultato})
    except Exception as e:
        return jsonify({'errore': 'Errore durante l\'analisi.'}), 500

@app.route('/telegram', methods=['POST'])
def telegram_bot():
    data = request.get_json()
    if data and "message" in data:
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        
        # Gestione Testo
        if "text" in msg:
            testo_utente = msg["text"]
            if testo_utente.startswith('/start'):
                risposta = "Ciao! Sono il tuo assistente anti-truffa. Incolla un testo o inviami uno screenshot di un messaggio sospetto!"
            else:
                risposta = analizza_con_ia(testo=testo_utente)
            requests.post(TELEGRAM_API_URL, json={"chat_id": chat_id, "text": risposta})
            
        # Gestione Foto / Screenshot
        elif "photo" in msg:
            try:
                # Prende la foto a risoluzione più alta
                file_id = msg["photo"][-1]["file_id"]
                file_info = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}").json()
                file_path = file_info["result"]["file_path"]
                
                # Scarica l'immagine dai server di Telegram
                photo_bytes = requests.get(f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}").content
                image_base64 = base64.b64encode(photo_bytes).decode('utf-8')
                
                # Analizza con l'IA
                risposta = analizza_con_ia(image_base64=image_base64)
                requests.post(TELEGRAM_API_URL, json={"chat_id": chat_id, "text": risposta})
            except Exception as e:
                requests.post(TELEGRAM_API_URL, json={"chat_id": chat_id, "text": "Errore durante la lettura dello screenshot."})

    return "OK", 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
