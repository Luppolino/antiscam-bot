import os
import json
import urllib.request
import urllib.parse
import base64
import time
from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse

app = FastAPI()

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# File e controllo temporale per l'aggiornamento automatico
BOARD_FILE = "scams_board.json"
LAST_UPDATE_FILE = "last_update.txt"
UPDATE_INTERVAL = 3600  # Aggiorna automaticamente al massimo una volta ogni ora (in secondi)

DEFAULT_SCAMS = [
    {
        "risk": "🔴",
        "title": "Finto SMS Poste / Corriere",
        "desc": "Messaggio con link anomalo che avvisa di un pacco bloccato in giacenza per sbloccare il quale vengono chiesti dati bancari o pagamenti di piccoli importi."
    },
    {
        "risk": "🟡",
        "title": "Finto rimborso INPS / Agenzia Entrate",
        "desc": "Comunicazione urgente via mail o SMS che promette un rimborso fiscale immediato invitando a inserire le credenziali SPID o bancarie su portali civetta."
    },
    {
        "risk": "🔴",
        "title": "Phishing Account Streaming / Servizi",
        "desc": "Avviso di blocco imminente dell'abbonamento per problemi di pagamento con link diretto a una pagina clone identica all'originale."
    }
]

def load_scams_board():
    if not os.path.exists(BOARD_FILE):
        save_scams_board(DEFAULT_SCAMS)
    try:
        with open(BOARD_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_SCAMS

def save_scams_board(scams_list):
    try:
        with open(BOARD_FILE, "w", encoding="utf-8") as f:
            json.dump(scams_list, f, ensure_ascii=False, indent=4)
        with open(LAST_UPDATE_FILE, "w", encoding="utf-8") as f:
            f.write(str(time.time()))
    except Exception as e:
        print(f"Errore nel salvataggio della bacheca: {e}")

def check_and_auto_update_radar():
    """Verifica se è tempo di aggiornare la bacheca in automatico tramite IA"""
    should_update = False
    if not os.path.exists(LAST_UPDATE_FILE) or not os.path.exists(BOARD_FILE):
        should_update = True
    else:
        try:
            with open(LAST_UPDATE_FILE, "r", encoding="utf-8") as f:
                last_time = float(f.read().strip())
                if time.time() - last_time > UPDATE_INTERVAL:
                    should_update = True
        except Exception:
            should_update = True

    if should_update:
        try:
            prompt = """
            Genera una lista di 3 truffe informatiche o phishing molto diffuse in Italia di recente.
            Restituisci la risposta ESCLUSIVAMENTE in formato JSON puro (senza blocchi di codice markdown o altri commenti), 
            come una lista di oggetti con chiavi: "risk" (che deve essere "🔴" o "🟡"), "title" (titolo breve della truffa) e "desc" (descrizione sintetica del pericolo).
            """
            ai_response = call_gemini_api_native(prompt)
            clean_json = ai_response.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json[7:]
            if clean_json.endswith("
