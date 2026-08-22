import os
from urllib.parse import urlparse

# ==========================================
# 1. CONFIGURAZIONE DEL SISTEMA & PROMPT IA
# ==========================================
SYSTEM_PROMPT = """
Sei 'Non Ci Casco Mai', un esperto di cybersecurity di altissimo livello e un analista antifrode.
Analizza il messaggio o l'immagine fornita dall'utente e rispondi SEMPRE con una struttura chiara, divisa in queste 4 sezioni:

1. VERDETTO: 
   [🔴 TRUFFA / 🟡 SOSPETTO / 🟢 SICURO] con una frase d'impatto.

2. PERCHÉ È UNA TRUFFA (Analisi dei pericoli):
   Elenca i dettagli tecnici o logici che non tornano (es. errori di ortografia, link civetta, mittente mascherato).

3. LEVA PSICOLOGICA USATA:
   Spiega quale emozione o pressione i truffatori stanno sfruttando (es. urgenza artificiale, paura della chiusura del conto, falsa golosità per un premio).

4. COSA FARE ORA (Piano di emergenza):
   Dai istruzioni immediate all'utente su come comportarsi (es. non cliccare, bloccare il mittente, e se ha già inserito dati, cosa fare subito).

Tieni il tono autorevole ma rassicurante, chiaro e diretto.
"""

# ==========================================
# 2. FILTRO ANTI-TYPOSQUATTING & DOMINI CIVETTA
# ==========================================
SUSPICIOUS_KEYWORDS = ['login', 'secure', 'verifica', 'aggiorna', 'account', 'sblocca', 'conferma', 'web-client']
SENSITIVE_BRANDS = ['poste', 'inps', 'agenziaentrate', 'intesasanpaolo', 'unicredit', 'paypal', 'amazon', 'netflix', 'dhl', 'bartolini']

def analyze_domain_safety(url_string):
    """
    Analizza l'URL per smascherare tentativi di phishing tramite typosquatting 
    o parole chiave sospette prima di interpellare l'IA.
    """
    try:
        if not url_string.startswith('http'):
            url_string = 'http://' + url_string
            
        parsed = urlparse(url_string)
        domain = parsed.netloc.lower()
        
        if domain.startswith('www.'):
            domain = domain[4:]
            
        # Controllo imitazione marchi (Typosquatting)
        for brand in SENSITIVE_BRANDS:
            if brand in domain:
                official_domains = [f"{brand}.it", f"{brand}.com", f"{brand}.net", f"{brand}.es", f"{brand}.fr"]
                if not any(domain.endswith(od) for od in official_domains):
                    return f"🔴 ALLARME TYPOSQUATTING: Il dominio `{domain}` sembra imitare falsamente il marchio **{brand}** usando un indirizzo civetta non ufficiale!"

        # Controllo parole chiave sospette nell'URL
        for word in SUSPICIOUS_KEYWORDS:
            if word in domain:
                return f"🟡 ATTENZIONE URL: Il dominio contiene la parola chiave sospetta `{word}`, tipica delle pagine di phishing."
                
        return "🟢 URL privo di schemi noti di typosquatting."
        
    except Exception as e:
        return "Impossibile analizzare l'URL inserito."

# ==========================================
# 3. GESTIONE PRIVACY ZERO-TRACE & ERRORI API
# ==========================================
def process_content_safely(content_input, file_path=None):
    """
    Gestisce l'analisi e intercetta eventuali sovraccarichi dei server di Google,
    garantendo la pulizia automatica Zero-Trace dei file temporanei.
    """
    try:
        # Esempio di chiamata a Gemini (sostituisci con la tua logica di generazione effettiva)
        # response = model.generate_content([SYSTEM_PROMPT, content_input])
        # risultato = response.text
        
        risultato = "Analisi completata con successo."
        return risultato

    except Exception as e:
        error_message = str(e)
        if "high demand" in error_message or "ResourceExhausted" in error_message:
            return "⚠️ I server di Google sono momentaneamente sovraccarichi a causa di un picco di traffico. Riprova tra qualche istante!"
        return f"Si è verificato un errore durante l'elaborazione: {error_message}"
        
    finally:
        # CANCELLAZIONE ISTANTANEA OBBLIGATORIA (Zero-Trace) se c'è un file temporaneo
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"[PRIVACY ZERO-TRACE] File {file_path} eliminato definitivamente.")
            except Exception as cleanup_error:
                print(f"Impossibile rimuovere il file temporaneo: {cleanup_error}")

# ==========================================
# 4. AVVIO APPLICAZIONE
# ==========================================
if __name__ == "__main__":
    print("Core di 'Non Ci Casco Mai' avviato con gestione errori e protezioni attive.")
