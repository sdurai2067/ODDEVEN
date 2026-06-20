import os
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# ── HTML_PAGE ─────────────────────────────────────────────────────────────────
# Served at your Railway public URL e.g. https://odd-even.up.railway.app/
# fetch() uses relative URL '/check' — works on localhost AND Railway
# with zero code changes between environments.
HTML_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Odd or Even?</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
      margin: 0;
      background: #f0f0f0;
    }
    .card {
      background: white;
      padding: 2rem 3rem;
      border-radius: 12px;
      box-shadow: 0 2px 12px rgba(0,0,0,0.1);
      text-align: center;
    }
    input[type="number"] {
      padding: 10px;
      font-size: 1.2rem;
      width: 180px;
      border: 1px solid #ccc;
      border-radius: 8px;
      text-align: center;
      margin-bottom: 0.5rem;
    }
    button {
      display: block;
      margin: 0.75rem auto 0;
      padding: 10px 28px;
      font-size: 1rem;
      background: #4CAF50;
      color: white;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      transition: background 0.2s;
    }
    button:hover  { background: #45a049; }
    button:active { background: #3d8b40; }
    #result {
      margin-top: 1.25rem;
      font-size: 1.5rem;
      font-weight: bold;
      min-height: 2rem;
    }
    #result.error { color: #e53935; }

    /* ── Credit line ──────────────────────────────────────────────────────── */
    .credit {
      margin-top: 2rem;
      font-size: 0.75rem;
      color: #aaa;
      letter-spacing: 0.03em;
    }
  </style>
</head>
<body>
  <div class="card">
    <h2>Odd or Even?</h2>

    <!-- Enter key also triggers the check -->
    <input
      type="number"
      id="numberInput"
      placeholder="Enter a number"
      onkeydown="if(event.key==='Enter') checkNumber()"
    />

    <button onclick="checkNumber()">Check</button>

    <!-- Result injected here by JS -->
    <div id="result"></div>

    <!-- Credit line -->
    <p class="credit">Created by DURAIARASU SIVARASU</p>
  </div>

  <script>
    async function checkNumber() {
      const input     = document.getElementById('numberInput');
      const resultDiv = document.getElementById('result');

      // Guard: empty input
      if (input.value === '') {
        resultDiv.className   = 'error';
        resultDiv.textContent = 'Please enter a number.';
        return;
      }

      const num = parseInt(input.value, 10);

      try {
        // Relative URL — no hardcoded localhost
        // works on local AND Railway without any change
        const response = await fetch('/check', {
          method:  'POST',
          headers: { 'Content-Type': 'application/json' },
          body:    JSON.stringify({ number: num }),
        });

        if (!response.ok) throw new Error(`Server error: ${response.status}`);

        const data = await response.json();
        resultDiv.className   = '';
        resultDiv.style.color = data.result === 'Even' ? 'green' : 'orange';
        resultDiv.textContent = `${data.number} is ${data.result}`;

      } catch (err) {
        resultDiv.className   = 'error';
        resultDiv.textContent = 'Could not reach the server.';
        console.error(err);
      }
    }
  </script>
</body>
</html>
'''


# ── CORS ──────────────────────────────────────────────────────────────────────
# Allows standalone index.html (file://) to POST to this server.
@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"]  = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return response


# ── Helper: identify request origin from Referer header ───────────────────────
# file://       → standalone index.html opened from disk
# 127.0.0.1     → local Flask server
# railway.app   → live Railway deployment
# (blank)       → direct call via Postman / curl
def get_source_label():
    referer = request.headers.get("Referer", "")
    if referer.startswith("file://"):
        return "index.html request"
    elif "127.0.0.1" in referer or "localhost" in referer:
        return "local ip"
    elif referer.startswith("https://"):
        return "railway"
    return "direct"


# ── Route: GET / ──────────────────────────────────────────────────────────────
# Returns the full HTML page — works on localhost AND Railway URL.
@app.route("/")
def home():
    return render_template_string(HTML_PAGE)


# ── Route: POST /check ────────────────────────────────────────────────────────
# ① Receives : { "number": <int> }
# ② Computes : Even if divisible by 2 AND not zero, else Odd
# ③ Logs     : number, result, source of request
# ④ Returns  : { "number": <int>, "result": "Even" | "Odd" }
@app.route("/check", methods=["POST", "OPTIONS"])
def check_odd_even():

    # Pre-flight OPTIONS — browser sends before every cross-origin POST
    if request.method == "OPTIONS":
        return "", 204

    # Parse JSON body — silent=True returns None instead of raising on bad JSON
    data = request.get_json(silent=True)
    if not data or "number" not in data:
        return jsonify({"error": "Missing 'number' field"}), 400

    # Even/Odd logic (unchanged):
    #   number % 2 == 0 AND number != 0  →  Even
    #   everything else (including 0)    →  Odd
    number = int(data["number"])
    result = "Even" if number % 2 == 0 and number != 0 else "Odd"

    # Log with source label
    source = get_source_label()
    print(f"  └── Input: '{number}' → Result: {number} is {result}  ({source})")

    return jsonify({"result": result, "number": number})


# ── Entry point ───────────────────────────────────────────────────────────────
# Railway injects $PORT — must read it or deployment crashes.
# Locally $PORT is not set, falls back to 5000.
# host="0.0.0.0" makes the app reachable from outside (required on Railway).
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
