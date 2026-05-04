from flask import Flask, render_template_string, redirect, url_for
import os
import json

app = Flask(__name__)
STATE_FILE = "power_state.json"

def get_states():
    if not os.path.exists(STATE_FILE):
        default = {"power": "ON", "magnet": "ON"}
        with open(STATE_FILE, "w") as f:
            json.dump(default, f)
        return default
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {"power": "ON", "magnet": "ON"}

def set_state(key, value):
    states = get_states()
    states[key] = value
    with open(STATE_FILE, "w") as f:
        json.dump(states, f)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Smart Meter Remote Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; text-align: center; padding: 20px; background-color: #f0f2f5; }
        .card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); display: inline-block; width: 90%; max-width: 400px; }
        h1 { color: #333; font-size: 20px; }
        .status-box { margin: 15px 0; padding: 10px; border-radius: 8px; background: #f9f9f9; }
        .status { font-size: 18px; font-weight: bold; margin: 5px 0; }
        .status.ON { color: #4CAF50; }
        .status.OFF { color: #f44336; }
        .status.STABLE { color: #2196F3; }
        .btn-group { display: flex; flex-direction: column; gap: 10px; }
        .btn { padding: 15px; font-size: 16px; border: none; border-radius: 8px; cursor: pointer; color: white; transition: 0.3s; width: 100%; font-weight: bold; }
        .btn-power { background-color: #f44336; }
        .btn-power.OFF { background-color: #4CAF50; }
        .btn-stable { background-color: #2196F3; }
        .btn-magnet { background-color: #9C27B0; }
        .btn-magnet.OFF { background-color: #4CAF50; }
        .footer { margin-top: 20px; font-size: 11px; color: #777; }
        hr { border: 0; border-top: 1px solid #eee; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="card">
        <h1>Remote Control Panel</h1>
        
        <div class="status-box">
            <div class="status {{ states.power }}">V/I Power: {{ states.power }}</div>
            <div class="status {{ states.magnet }}">Magnet Sensor: {{ states.magnet }}</div>
        </div>

        <div class="btn-group">
            <form action="/toggle_power" method="post">
                <button type="submit" class="btn btn-power {{ states.power }}">
                    {{ 'CUT V/I POWER' if states.power != 'OFF' else 'RESTORE V/I POWER' }}
                </button>
            </form>
            
            <form action="/set_stable" method="post">
                <button type="submit" class="btn btn-stable">
                    {{ 'SET STABLE MODE' if states.power != 'STABLE' else 'NORMAL V/I MODE' }}
                </button>
            </form>

            <hr>

            <form action="/toggle_magnet" method="post">
                <button type="submit" class="btn btn-magnet {{ states.magnet }}">
                    {{ 'CUT MAGNET SENSOR' if states.magnet == 'ON' else 'RESTORE MAGNET SENSOR' }}
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
    states = get_states()
    return render_template_string(HTML_TEMPLATE, states=states)

@app.route("/toggle_power", methods=["POST"])
def toggle_power():
    states = get_states()
    new_status = "OFF" if states['power'] != "OFF" else "ON"
    set_state('power', new_status)
    return redirect(url_for("index"))

@app.route("/set_stable", methods=["POST"])
def set_stable():
    states = get_states()
    new_status = "STABLE" if states['power'] != "STABLE" else "ON"
    set_state('power', new_status)
    return redirect(url_for("index"))

@app.route("/toggle_magnet", methods=["POST"])
def toggle_magnet():
    states = get_states()
    new_status = "OFF" if states['magnet'] == "ON" else "ON"
    set_state('magnet', new_status)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
