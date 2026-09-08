async def process_whatsapp_background(from_phone, msg):
    try:
        msg_type = msg.get("type")
        if msg_type == "text":
            text_body = msg.get("text", {}).get("body", "")
            if text_body:
                analysis_res = perform_core_analysis(text_content=text_body)
                send_whatsapp_message(from_phone, analysis_res)
        elif msg_type in ["image", "document"]:
            send_whatsapp_message(from_phone, "Ricevuto l'allegato! Analisi in corso...")
            media_data = msg.get(msg_type, {})
            media_id = media_data.get("id")
            
            if not media_id:
                send_whatsapp_message(from_phone, "⚠️ Errore: Impossibile leggere l'ID del file allegato.")
                return
                
            media_url_meta = f"https://graph.facebook.com/v21.0/{media_id}"
            headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
            req_media = urllib.request.Request(media_url_meta, headers=headers)
            
            with urllib.request.urlopen(req_media, timeout=10) as resp:
                media_info = json.loads(resp.read().decode())
                download_url = media_info.get("url")
            
            if download_url:
                req_dl = urllib.request.Request(download_url, headers=headers)
                temp_path = f"/tmp/wa_{media_id}.jpg"
                with urllib.request.urlopen(req_dl, timeout=15) as dl_resp, open(temp_path, "wb") as f_out:
                    f_out.write(dl_resp.read())
                
                analysis_res = perform_core_analysis(file_path=temp_path)
                send_whatsapp_message(from_phone, analysis_res)
            else:
                send_whatsapp_message(from_phone, "⚠️ Errore: Impossibile ottenere l'URL di download da Meta.")
    except Exception as e:
        print(f"Errore background task WhatsApp: {e}")
        send_whatsapp_message(from_phone, "⚠️ Si è verificato un errore imprevisto durante l'analisi del file.")
