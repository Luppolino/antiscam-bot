import base64
import os
import re
from flask import Flask, jsonify, render_template, request
from openai import OpenAI
import requests
import json

app = Flask(__name__)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# Funzione per inviare messaggi con tasti
def invia_messaggio_con_tasti(chat_id, testo, tasti=None):
    payload = {"chat_id": chat_id, "text": testo, "parse_mode": "Markdown"}
    if tasti:
        payload["reply_markup"] = json.dumps({"inline_keyboard": tasti})
    requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload)

# ... (Funzioni maschera_dati_sensibili, estrai_url, analizza_con_ia restano identiche) ...
def maschera_dati_sensibili(testo):
    if not testo: return ""
    testo = re.sub(r'[A-Z]{2}\d{2}[A-Z0-9]{10,30}', '[IBAN_OSCURATO]', testo)
    testo = re.sub(r'\b(?:\+39)?\s?3\d{2}\s?\d{6,7}\b', '[NUMERO_OSCURATO]', testo)
    testo = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '[CARTA_OSCURATA]', testo)
    return testo

def estrai_url(testo):
    if not testo: return []
    return re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', testo)

def analizza_con_ia(testo="", image_base64=None):
    link_trovati = estrai_url(testo) if testo else []
    link_str = ", ".join(link_trovati) if link_trovati else "Nessuno"
    system_prompt = (
        "Sei un esperto di cybersecurity. Categorizza in: 'Phishing e Messaggi', 'Marketplace e Vendite', 'Truffe Finanziarie'. "
        "Struttura: 🏷️ CATEGORIA, ⚠️ RISCHIO, 🔗 ANALISI LINK, 📋 SPIEGAZIONE, 💡 COSA FARE."
    )
    user_content = [{"type": "text", "text": f"Analizza:\nLink: {link_str}\nTesto: {maschera_dati_sensibili(testo)}"}]
    if image_base64: user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}})
    
    response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_content}])
    return response.choices[0].message.content

@app.route('/')
def home(): return render_template('index.html')

@app.route('/analizza', methods=['POST'])
def analizza():
    dati = request.get_json() or {}
    risultato = analizza_con_ia(testo=dati.get('testo', ''), image_base64=dati.get('image'))
    return jsonify({'risultato': risultato})

@app.route('/telegram', methods=['POST'])
def telegram_bot():
    data = request.get_json()
    
    # Gestione tasti cliccati (Callback)
    if "callback_query" in data:
        chat_id = data["callback_query"]["message"]["chat"]["id"]
        data_tasto = data["callback_query"]["data"]
        if data_tasto == "menu":
            testo = "🚨 *Menu Anti-Truffa*\n\n📱 Phishing (SMS/Email)\n🛒 Marketplace (Subito/Vinted)\n💰 Investimenti"
            invia_messaggio_con_tasti(chat_id, testo, [[{"text": "🔄 Verifica un altro", "callback_data": "start"}]])
        elif data_tasto == "start":
            invia_messaggio_con_tasti(chat_id, "Incolla un testo o invia uno screenshot!")
        return "OK", 200

    # Gestione messaggi normali
    if "message" in data:
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        tasti = [[{"text": "🔄 Verifica altro", "callback_data": "start"}, {"text": "🚨 Menu", "callback_data": "menu"}]]
        
        if "text" in msg:
            if msg["text"].startswith('/start'):
                invia_messaggio_con_tasti(chat_id, "Ciao! Sono il tuo assistente anti-truffa.", tasti)
            else:
                invia_messaggio_con_tasti(chat_id, analizza_con_ia(testo=msg["text"]), tasti)
        elif "photo" in msg:
            file_id = msg["photo"][-1]["file_id"]
            file_info = requests.get(f"{TELEGRAM_API_URL}/getFile?file_id={file_id}").json()
            file_path = file_info["result"]["file_path"]
            img_bytes = requests.get(f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}").content
            img_b64 = base64.b64encode(img_bytes).decode('utf-8')
            invia_messaggio_con_tasti(chat_id, analizza_con_ia(image_base64=img_b64), tasti)
            
    return "OK", 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
