def call_gemini_api_native(prompt, image_path=None):
    if not GEMINI_API_KEY:
        return "⚠️ Errore: GEMINI_API_KEY non configurata."
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.7-flash:generateContent?key={GEMINI_API_KEY}"
    parts = [{"text": prompt}]
    
    if image_path and os.path.exists(image_path):
        try:
            img = Image.open(image_path)
            img.thumbnail((1024, 1024))
            compressed_path = image_path + "_comp.jpg"
            img.convert("RGB").save(compressed_path, "JPEG", quality=80)
            
            with open(compressed_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            parts.append({"inline_data": {"mime_type": "image/jpeg", "data": encoded_string}})
            
            if os.path.exists(compressed_path):
                os.remove(compressed_path)
        except Exception as e:
            return f"⚠️ Errore elaborazione immagine: {e}"
            
    payload = {"contents": [{"parts": parts}]}
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
    
    try:
        # Timeout aumentato a 45 secondi per consentire l'analisi visiva
        with urllib.request.urlopen(req, timeout=45) as response:
            result = json.loads(response.read().decode())
            return result["candidates"][0]["content"]["parts"][0]["text"]
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        return f"⚠️ Errore API Gemini (HTTP {e.code}): {error_body}"
    except Exception as e:
        return f"⚠️ Errore API Gemini: {str(e)}"
