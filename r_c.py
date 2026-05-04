from flask import Flask, render_template_string, redirect, url_for
import os

app = Flask(__name__)
STATE_FILE = "power_state.txt"

def get_power_status():
    if not os.path.exists(STATE_FILE):
        with open(STATE_FILE, "w") as f:
            f.write("ON")
        return "ON"
    with open(STATE_FILE, "r") as f:
        return f.read().strip()

def set_power_status(status):
    with open(STATE_FILE, "w") as f:
        f.write(status)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Smart Meter Remote Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; text-align: center; padding: 50px; background-color: #f0f2f5; }
        .card { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); display: inline-block; }
        h1 { color: #333; }
        .status { font-size: 24px; font-weight: bold; margin: 20px 0; }
        .status.ON { color: #4CAF50; }
        .status.OFF { color: #f44336; }
        .status.STABLE { color: #2196F3; }
        .btn-group { display: flex; flex-direction: column; gap: 10px; }
        .btn { padding: 15px 30px; font-size: 18px; border: none; border-radius: 8px; cursor: pointer; color: white; transition: 0.3s; width: 100%; }
        .btn-toggle { background-color: #f44336; }
        .btn-toggle.ON { background-color: #f44336; }
        .btn-toggle.OFF { background-color: #4CAF50; }
        .btn-stable { background-color: #2196F3; }
        .btn-stable:hover { background-color: #1976D2; }
        .footer { margin-top: 20px; font-size: 12px; color: #777; }
    </style>
</head>
<body>
    <div class="card">
        <h1>Remote Power Control</h1>
        <div class="status {{ status }}">Power Status: {{ status }}</div>
        <div class="btn-group">
            <form action="/toggle_power" method="post">
                <button type="submit" class="btn btn-toggle {{ status }}">
                    {{ 'CUT POWER' if status != 'OFF' else 'RESTORE POWER' }}
                </button>
            </form>
            <form action="/set_stable" method="post">
                <button type="submit" class="btn btn-stable">
                    {{ 'SET STABLE MODE' if status != 'STABLE' else 'NORMAL MODE' }}
                </button>
            </form>
        </div>
        <div class="footer">Smart Meter Tamper Detection System</div>
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    status = get_power_status()
    return render_template_string(HTML_TEMPLATE, status=status)

@app.route("/toggle_power", methods=["POST"])
def toggle_power():
    current = get_power_status()
    new_status = "OFF" if current != "OFF" else "ON"
    set_power_status(new_status)
    return redirect(url_for("index"))

@app.route("/set_stable", methods=["POST"])
def set_stable():
    current = get_power_status()
    new_status = "STABLE" if current != "STABLE" else "ON"
    set_power_status(new_status)
    return redirect(url_for("index"))

if __name__ == "__main__":
    # Start on port 5000 and bind to all interfaces so phone can access it
    app.run(host="0.0.0.0", port=5000)
