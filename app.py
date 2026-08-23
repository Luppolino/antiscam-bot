import base64
import os
import json
import urllib.request
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def analyze_with_gemini(prompt_text, image_path=None):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        contents = [prompt_text]

        if image_path and os.path.exists(image_path):
            with open(image_path, "rb") as img_file:
                image_bytes = img_file.read()
                image_part = {
                    "mime_type": "image/jpeg",
                    "data": image_bytes
                }
                contents.append(image_part)

        response = model.generate_content(contents)
        return response.text
        
    except Exception as e:
        # Fallback automatico se il flash standard richiede un aggiornamento
        try:
            model_fallback = genai.GenerativeModel('gemini-2.0-flash')
            response = model_fallback.generate_content(contents)
            return response.text
        except Exception as e2:
            return f"⚠️ Errore di connessione con l'IA: {str(e2)}"


def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Errore invio Telegram: {e}")


# Rotta per il Sito Web (Carica la pagina HTML da templates/index.html)
@app.route('/')
def home():
    return render_template('index.html')


# Rotta per le richieste di analisi provenienti dal Sito Web
@app.route('/analizza', methods=['POST'])
def analizza_web():
    try:
        data = request.get_json()
        testo = data.get('testo', '')
        image_base64 = data.get('image', None)

        if not testo and not image_base64:
            return jsonify({'errore': 'Inserisci un messaggio o seleziona uno screenshot.'}), 400

        prompt_base = (
            "Sei NonCiCascoMai, un assistente di sicurezza digitale esperto in "
            "anti-phishing e prevenzione frodi. Analizza il seguente contenuto "
            "fornendo una valutazione del rischio strutturata in 4 parti: "
            "1. Livello di rischio (Basso/Medio/Alto), "
            "2. Indicatori di allerta rilevati (red flags), "
            "3. Motivazione dettagliata, "
            "4. Consigli pratici su cosa fare.\n\nContenuto da analizzare: "
            + testo
        )

        contents = [prompt_base]
        temp_file_path = None

        if image_base64:
            image_bytes = base64.b64decode(image_base64)
            temp_file_path = "/tmp/web_img.jpg"
            with open(temp_file_path, "wb") as f:
                f.write(image_bytes)
            
            contents.append({
                "mime_type": "image/jpeg",
                "data": image_bytes
            })

        analysis_result = analyze_with_gemini(contents[0], temp_file_path if image_base64 else None)

        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        # Formattazione per la visualizzazione HTML pulita
        risultato_formattato = analysis_result.replace('\n', '<br>')
        return jsonify({'risultato': risultato_formattato})

    except Exception as e:
        return jsonify({'errore': f"Errore interno: {str(e)}"}), 500


# Rotta per il Bot Telegram (Webhook)
@app.route('/telegram', methods=['POST'])
def telegram_webhook():
    try:
        update = request.get_json()
        if "message" in update:
            message = update["message"]
            chat_id = message["chat"]["id"]
            text_content = message.get("text", message.get("caption", ""))

            prompt_base = (
                "Sei NonCiCascoMai, un assistente di sicurezza digitale esperto in "
                "anti-phishing e prevenzione frodi. Analizza il seguente contenuto "
                "fornendo una valutazione del rischio strutturata in 4 parti: "
                "1. Livello di rischio (Basso/Medio/Alto), "
                "2. Indicatori di allerta rilevati (red flags), "
                "3. Motivazione dettagliata, "
                "4. Consigli pratici su cosa fare.\n\nContenuto da analizzare: "
                + text_content
            )

            temp_file_path = None
            if "photo" in message:
                photo_file_id = message["photo"][-1]["file_id"]
                file_info_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={photo_file_id}"
                with urllib.request.urlopen(file_info_url) as f_info:
                    file_data = json.loads(f_info.read().decode("utf-8"))
                    if file_data.get("ok"):
                        file_path_tg = file_data["result"]["file_path"]
                        download_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path_tg}"
                        temp_file_path = f"/tmp/img_{chat_id}.jpg"
                        urllib.request.urlretrieve(download_url, temp_file_path)

            analysis_result = analyze_with_gemini(prompt_base, temp_file_path)

            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)

            send_telegram_message(chat_id, analysis_result)

        return jsonify({"status": "ok"})
    except Exception as e:
        print(f"Errore webhook telegram: {e}")
        return jsonify({"status": "error"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
