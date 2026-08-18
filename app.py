import os
import re
from flask import Flask, jsonify, render_template, request
from openai import OpenAI

app = Flask(__name__)

# Legge la chiave API in modo sicuro dalle variabili d'ambiente (Render / Cloud)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def maschera_dati_sensibili(testo):
  """Filtro di Privacy: oscura IBAN, numeri di telefono e carte prima di inviare all'AI"""
  testo = re.sub(r"[A-Z]{2}\d{2}[A-Z0-9]{10,30}", "[IBAN_OSCURATO]", testo)
  testo = re.sub(r"\b(?:\+39)?\s?3\d{2}\s?\d{6,7}\b", "[NUMERO_OSCURATO]", testo)
  testo = re.sub(
      r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b", "[CARTA_OSCURATA]", testo
  )
  return testo


@app.route("/")
def home():
  return render_template("index.html")


@app.route("/analizza", methods=["POST"])
def analizza():
  dati = request.get_json()
  testo_utente = dati.get("testo", "")

  if not testo_utente.strip():
    return jsonify({"errore": "Inserisci un messaggio da analizzare."}), 400

  # Applica il filtro privacy
  testo_pulito = maschera_dati_sensibili(testo_utente)

  system_prompt = """
    Sei un assistente esperto in cybersecurity e prevenzione delle truffe digitali in Italia.
    Analizza il messaggio ricevuto e rispondi ESCLUSIVAMENTE in formato JSON con questa struttura esatta:
    {
      "livello_rischio": "Basso" o "Sospetto" o "Alto",
      "spiegazione": "Breve spiegazione in 2 frasi dei segnali di pericolo riscontrati.",
      "azione_consigliata": "Cosa deve fare concretamente l'utente."
    }
    Non aggiungere altro testo fuori dal formato JSON.
    """

  try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": testo_pulito},
        ],
        response_format={"type": "json_object"},
    )

    risultato_ai = response.choices[0].message.content
    return risultato_ai

  except Exception as e:
    return jsonify({"errore": "Errore durante l'analisi del messaggio."}), 500


if __name__ == "__main__":
  app.run(debug=True, port=5000)