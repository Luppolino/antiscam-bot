<!DOCTYPE html>
<html lang="it">
<head>
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-H698KT76PV"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());

      gtag('config', 'G-H698KT76PV');
    </script>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Non Ci Casco Mai</title>
    <style>
    body { font-family: sans-serif; background: #f4f7f6; margin: 0; padding: 20px; display: flex; justify-content: center; }
    .container { max-width: 700px; width: 100%; background: #fff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    h1 { color: #1a365d; text-align: center; }
    textarea, input[file] { width: 100%; padding: 10px; margin-bottom: 15px; box-sizing: border-box; border-radius: 6px; border: 1px solid #ccc; }
    textarea { height: 90px; }
    button { background: #3182ce; color: white; border: none; padding: 12px; width: 100%; border-radius: 6px; font-weight: bold; cursor: pointer; }
    .result { margin-top: 20px; background: #edf2f7; padding: 15px; border-radius: 6px; white-space: pre-wrap; display: {disp}; border-left: 5px solid #3182ce; }
    .board { margin-top: 30px; border-top: 2px solid #eee; padding-top: 20px; }
    .scam-card { background: #fff5f5; border: 1px solid #feb2b2; border-left: 5px solid #e53e3e; padding: 12px; border-radius: 6px; margin-bottom: 10px; }
    .scam-card h3 { margin: 0 0 5px 0; color: #c53030; font-size: 15px; }
    .scam-card p { margin: 0; font-size: 13px; color: #4a5568; }
    .btn-up { background: #38a169; width: auto; padding: 6px 12px; font-size: 13px; }
    </style>
</head>
<body>
<div class="container">
<h1>Non Ci Casco Mai 🛡️</h1>
<form action="/analyze" method="post" enctype="multipart/form-data">
<label>Incolla messaggio o link:</label>
<textarea name="text" placeholder="Es. Pacco bloccato..."></textarea>
<label>Oppure carica screenshot:</label>
<input type="file" name="file" accept="image/*">
<button type="submit">Analizza con IA</button>
</form>
<div class="result"><strong>Risultato:</strong><br><br>{result_html}</div>
<div class="board">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
<h3 style="margin:0;">🚨 Ultime Truffe</h3>
<form action="/update-radar" method="get" style="margin:0;"><button type="submit" class="btn-up">🔄 Aggiorna</button></form>
</div>
{cards}
</div>
</div>
</body>
</html>
