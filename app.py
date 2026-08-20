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
    if not testo:
        return ""
    testo = re.sub(r'[A-Z]{2}\d{2}[A-Z0-9]{10,30}', '[IBAN_OSCURATO]', testo)
    testo = re.sub(r'\b(?:\+39)?\s?3\d{2}\s?\d{6,7}\b', '[NUMERO_OSCURATO]', testo)
    testo = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '[CARTA_OSCURATA]', testo)
    return testo

def estrai_url(testo):
    if not testo:
        return []
    url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
    return re.findall(url_pattern, testo)

def analizza_con_ia(testo="", image_base64=None):
    link_trovati = estrai_url(testo) if testo else []
    link_str = ", ".join(link_trovati) if link_trovati else "Nessun link esplicito nel testo"

    system_prompt = (
        "Sei un esperto di cybersecurity in Italia specializzato in phishing, truffe online e marketplace. "
        "Analizza il contenuto, fai molta attenzione ai link presenti (controllando domini contraffatti, "
        "typosquatting, o siti e-commerce falsi) e ai segnali di truffa nei pagamenti (es. ricariche non tracciabili). "
        "Rispondi in modo chiaro e diretto con questa struttura:\n"
        "⚠️ RISCHIO: [Basso / Sospetto / Alto]\n"
        "🔗 ANALISI LINK: Valutazione specifica del dominio o dei link trovati.\n"
        "📋 SPIEGAZIONE: Breve spiegazione dei pericoli.\n"
        "💡 COSA FARE: Azione concreta per l'utente."
    )
    
    user_content = []
    text_prompt = f"Analizza questo contenuto anti-truffa.\nLink rilevati nel testo: {link_str}"
    
    if testo and str(testo).strip():
        testo_pulito = maschera_dati_sensibili(testo)
        text_prompt += f"\nTesto completo: {testo_pulito}"
        
    user_content.append({"type": "text", "text": text_prompt})
    
    if image_base64:
        user_content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
        })

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
    )
    return response.choices[0].message.content

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analizza', methods=['POST'])
def analizza():
    try:
        dati = request.get_json() or {}
        testo = dati.get('testo', '') or ''
        image_base64 = dati.get('image', None)
        
        if not str(testo).strip() and not image_base64:
            return jsonify({'errore': 'Inserisci un messaggio o carica uno screenshot.'}), 400

        risultato = analizza_con_ia(testo=testo, image_base64=image_base64)
        return jsonify({'risultato': risultato})
    except Exception as e:
        return jsonify({'errore': f"Errore tecnico: {str(e)}"}), 500

@app.route('/telegram', methods=['POST'])
def telegram_bot():
    try:
        data = request.get_json()
        if data and "message" in data:
            msg = data["message"]
            chat_id = msg["chat"]["id"]
            
            if "text" in msg:
                testo_utente = msg["text"]
                
                if testo_utente.startswith('/start'):
                    risposta = "Ciao! Sono il tuo assistente anti-truffa. Incolla un testo o inviami uno screenshot di un messaggio sospetto.\n\nDigita /menu per vedere cosa posso controllare!"
                elif testo_utente.startswith('/menu'):
                    risposta = (
                        "🚨 **Assistente Anti-Truffa - Menu** 🚨\n\n"
                        "Invia un testo o uno screenshot per analizzare:\n\n"
                        "📱 **Phishing & Messaggi**\n"
                        "- SMS finti corrieri / pacchi\n"
                        "- Finti blocchi conto bancario\n"
                        "- Tentativi di phishing email/SMS\n\n"
                        "🛒 **Marketplace & Vendite**\n"
                        "- Finti venditori su Facebook/Subito\n"
                        "- Siti e-commerce sospetti\n"
                        "- Richieste di pagamenti non tracciabili"
                    )
                else:
                    risposta = analizza_con_ia(testo=testo_utente)
                
                requests.post(TELEGRAM_API_URL, json={"chat_id": chat_id, "text": risposta, "parse_mode": "Markdown"})
                
            elif "photo" in msg:
                file_id = msg["photo"][-1]["file_id"]
                file_info = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}").json()
                file_path = file_info["result"]["file_path"]
                
                photo_bytes = requests.get(f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}").content
                image_base64 = base64.b64encode(photo_bytes).decode('utf-8')
                
                risposta = analizza_con_ia(image_base64=image_base64)
                requests.post(TELEGRAM_API_URL, json={"chat_id": chat_id, "text": risposta})
    except Exception as e:
        print(f"Errore Telegram: {str(e)}")

    return "OK", 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
