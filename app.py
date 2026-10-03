from flask import Flask, jsonify, request, render_template
from werkzeug.exceptions import HTTPException

app = Flask(__name__)

# ============================================================
# SENSOR DATA
# ============================================================

sensor_data = {
    "ldr": 1,
    "pir": 0
}

system_state = {
    "light_condition": "DAY",
    "motion_detected": False,
    "street_light": "OFF",
    "mode": "AUTO"
}


# ============================================================
# STREET LIGHT LOGIC
# ============================================================

def update_system():
    """
    Automatic street-light logic:

    DAY + any motion      -> OFF
    NIGHT + no motion     -> OFF
    NIGHT + motion        -> ON
    """

    if sensor_data["ldr"] == 0:
        system_state["light_condition"] = "NIGHT"
    else:
        system_state["light_condition"] = "DAY"

    system_state["motion_detected"] = sensor_data["pir"] == 1

    if system_state["mode"] == "AUTO":
        if (
            system_state["light_condition"] == "NIGHT"
            and system_state["motion_detected"]
        ):
            system_state["street_light"] = "ON"
        else:
            system_state["street_light"] = "OFF"


def get_status():
    update_system()

    return {
        "light_condition": system_state["light_condition"],
        "motion_detected": system_state["motion_detected"],
        "street_light": system_state["street_light"],
        "mode": system_state["mode"],
        "ldr": sensor_data["ldr"],
        "pir": sensor_data["pir"]
    }


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")


# ============================================================
# STATUS API
# ============================================================

@app.route("/api/status", methods=["GET"])
def api_status():
    return jsonify(get_status())


# ============================================================
# RASPBERRY PI SENSOR API
# ============================================================

@app.route("/api/sensor", methods=["POST"])
def receive_sensor_data():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "error": "JSON data required"
        }), 400

    ldr = data.get("ldr")
    pir = data.get("pir")

    if ldr not in (0, 1):
        return jsonify({
            "success": False,
            "error": "ldr must be 0 or 1"
        }), 400

    if pir not in (0, 1):
        return jsonify({
            "success": False,
            "error": "pir must be 0 or 1"
        }), 400

    sensor_data["ldr"] = ldr
    sensor_data["pir"] = pir

    update_system()

    return jsonify({
        "success": True,
        "message": "Sensor data received",
        "ldr": sensor_data["ldr"],
        "pir": sensor_data["pir"],
        "light_condition": system_state["light_condition"],
        "motion_detected": system_state["motion_detected"],
        "street_light": system_state["street_light"],
        "mode": system_state["mode"]
    })


# ============================================================
# MODE API
# ============================================================

@app.route("/api/mode", methods=["POST"])
def api_mode():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "error": "JSON data required"
        }), 400

    mode = data.get("mode")

    if mode not in ("AUTO", "MANUAL"):
        return jsonify({
            "success": False,
            "error": "Mode must be AUTO or MANUAL"
        }), 400

    system_state["mode"] = mode

    update_system()

    return jsonify({
        "success": True,
        "message": "Mode changed",
        "status": get_status()
    })


# ============================================================
# MANUAL LIGHT ON
# ============================================================

@app.route("/api/light/on", methods=["POST"])
def light_on():

    if system_state["mode"] != "MANUAL":
        return jsonify({
            "success": False,
            "error": "Switch to MANUAL mode first"
        }), 409

    system_state["street_light"] = "ON"

    return jsonify({
        "success": True,
        "message": "Street light turned ON",
        "status": get_status()
    })


# ============================================================
# MANUAL LIGHT OFF
# ============================================================

@app.route("/api/light/off", methods=["POST"])
def light_off():

    if system_state["mode"] != "MANUAL":
        return jsonify({
            "success": False,
            "error": "Switch to MANUAL mode first"
        }), 409

    system_state["street_light"] = "OFF"

    return jsonify({
        "success": True,
        "message": "Street light turned OFF",
        "status": get_status()
    })


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(HTTPException)
def handle_http_error(error):

    return jsonify({
        "success": False,
        "error": error.description
    }), error.code


@app.errorhandler(Exception)
def handle_unexpected_error(error):

    print("ERROR:", error)

    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
