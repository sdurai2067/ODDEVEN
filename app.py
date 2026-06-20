from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# ── HTML_PAGE ─────────────────────────────────────────────────────────────────
# Served at http://127.0.0.1:5000/
# Identical design to index.html — same card, same button, same result colours.
# fetch uses a relative URL ('/check') so the Referer header reads "http://..."
# which Flask logs as (local ip).
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
  </style>
</head>
<body>
  <div class="card">
    <h2>Odd or Even?</h2>

    <!-- Enter key also triggers check -->
    <input
      type="number"
      id="numberInput"
      placeholder="Enter a number"
      onkeydown="if(event.key==='Enter') checkNumber()"
    />

    <button onclick="checkNumber()">Check</button>

    <!-- Result text injected here -->
    <div id="result"></div>
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
        // Relative URL — Referer will be "http://127.0.0.1:5000/"
        // Flask reads this and logs it as (local ip)
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
        resultDiv.textContent = 'Could not reach the server. Is Flask running?';
        console.error(err);
      }
    }
  </script>
</body>
</html>
'''


# ── CORS ──────────────────────────────────────────────────────────────────────
# Allows index.html opened via file:// to POST to this server.
# Without this header, browsers block cross-origin requests from file:// pages.
@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"]  = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return response


# ── Helper: identify request origin from Referer header ───────────────────────
# Browser sets Referer automatically on every fetch() call:
#   file:///C:/Users/.../index.html  →  "index.html request"
#   http://127.0.0.1:5000/           →  "local ip"
#   no Referer (curl, Postman, etc.) →  "direct"
def get_source_label():
    referer = request.headers.get("Referer", "")
    if referer.startswith("file://"):
        return "HTML REQUEST"
    elif referer.startswith("http://"):
        return "LOCAL IP"
    return "DIRECT"


# ── Route: GET / ──────────────────────────────────────────────────────────────
# Renders HTML_PAGE when the browser visits http://127.0.0.1:5000/
# render_template_string keeps everything in one file — no templates/ folder needed.
@app.route("/")
def home():
    return render_template_string(HTML_PAGE)


# ── Route: POST /check ────────────────────────────────────────────────────────
# ① Receives : { "number": <int> }
# ② Computes : Even if divisible by 2 AND not zero, else Odd
# ③ Logs     : number, result, and which client sent the request
# ④ Returns  : { "number": <int>, "result": "Even" | "Odd" }
@app.route("/check", methods=["POST", "OPTIONS"])
def check_odd_even():

    # ① Pre-flight OPTIONS — browser sends this before every cross-origin POST.
    #    Return 204 No Content to confirm CORS is allowed, then browser sends the real POST.
    if request.method == "OPTIONS":
        return "", 204

    # ② Parse JSON body — silent=True returns None instead of raising on bad JSON
    data = request.get_json(silent=True)
    if not data or "number" not in data:
        return jsonify({"error": "Missing 'number' field"}), 400

    # ③ Compute Even / Odd
    #    Logic: number % 2 == 0 AND number != 0  →  Even
    #           everything else (including 0)    →  Odd
    number = int(data["number"])
    result = "Even" if number % 2 == 0 and number != 0 else "Odd"

    # ④ Read Referer to label the log line
    source = get_source_label()

    # ⑤ Print enhanced log — appears directly below Flask's own access log line
    print(f"  └── Input: '{number}' → Result: {number} is {result}  ({source})")

    # ⑥ Send JSON response back to the browser
    return jsonify({"result": result, "number": number})


# ── Entry point ───────────────────────────────────────────────────────────────
# debug=True  → auto-reloads on file save, shows full tracebacks in browser
# port=5000   → http://127.0.0.1:5000/
if __name__ == "__main__":
    app.run(debug=True, port=5000)
