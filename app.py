import os

def analyze_screenshot_safely(file_path):
    try:
        # 1. Qui avviene l'elaborazione con Gemini
        # (es. apertura con PIL o upload temporaneo)
        # image = Image.open(file_path)
        # response = model.generate_content(...)
        
        risultato = "Analisi completata con successo."
        return risultato

    except Exception as e:
        return f"Errore durante l'analisi: {str(e)}"
        
    finally:
        # 2. CANCELLAZIONE ISTANTANEA (Zero-Trace)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"[PRIVACY] File {file_path} distrutto correttamente dai server.")
            except Exception as cleanup_error:
                print(f"Impossibile rimuovere il file: {cleanup_error}")
