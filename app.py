from urllib.parse import urlparse

# Parole chiave e marchi caldi spesso clonati dai truffatori
SUSPICIOUS_KEYWORDS = ['login', 'secure', 'verifica', 'aggiorna', 'account', 'sblocca', 'conferma', 'web-client']
SENSITIVE_BRANDS = ['poste', 'inps', 'agenziaentrate', 'intesasanpaolo', 'unicredit', 'paypal', 'amazon', 'netflix', 'dhl', 'bartolini']

def analyze_domain_safety(url_string):
    try:
        # Normalizza l'URL
        if not url_string.startswith('http'):
            url_string = 'http://' + url_string
            
        parsed = urlparse(url_string)
        domain = parsed.netloc.lower()
        
        # Rimuove 'www.' per pulire l'analisi
        if domain.startswith('www.'):
            domain = domain[4:]
            
        # 1. Controllo imitazione marchi (Typosquatting)
        for brand in SENSITIVE_BRANDS:
            if brand in domain:
                # Se il nome del brand è dentro il dominio ma non è il dominio ufficiale esatto
                official_domains = [f"{brand}.it", f"{brand}.com", f"{brand}.net", f"{brand}.es", f"{brand}.fr"]
                if not any(domain.endswith(od) for od in official_domains):
                    return f"🔴 ALLARME TYPOSQUATTING: Il dominio `{domain}` sembra imitare falsamente il marchio **{brand}** usando un indirizzo civetta non ufficiale!"

        # 2. Controllo parole chiave sospette nell'URL
        for word in SUSPICIOUS_KEYWORDS:
            if word in domain:
                return f"🟡 ATTENZIONE URL: Il dominio contiene la parola chiave sospetta `{word}`, tipica delle pagine di phishing."
                
        return "🟢 URL privo di schemi noti di typosquatting."
        
    except Exception as e:
        return "Impossibile analizzare l'URL inserito."
