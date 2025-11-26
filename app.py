# app.py
from flask import Flask, render_template, jsonify, request
import time, hmac, hashlib, struct, os
from threading import Timer, Lock

app = Flask(__name__, static_folder="static", template_folder="templates")

# OTP helpers
def secret_to_int(secret: str) -> int:
    return sum(secret.encode())

def generate_otp(secret: str, for_time: float | None = None, step: int = 15, digits: int = 4) -> str:
    if for_time is None:
        for_time = time.time()
    counter = int(for_time // step)
    secret_int = secret_to_int(secret)
    combined_value = (secret_int ^ counter) & 0xFFFFFFFFFFFFFFFF
    msg = struct.pack(">Q", combined_value)
    key = secret.encode("utf-8")
    digest = hmac.new(key, msg, hashlib.sha256).digest()
    offset = digest[-1] & 0x0F
    code_int = struct.unpack(">I", digest[offset:offset+4])[0] & 0x7FFFFFFF
    otp = code_int % (10 ** digits)
    return str(otp).zfill(digits)

def verify_otp(candidate: str, secret: str, step: int = 15, digits: int = 4, window: int = 3):
    now = time.time()
    for offset in range(-window, window + 1):
        t = now + (offset * step)
        expected = generate_otp(secret, for_time=t, step=step, digits=digits)
        if hmac.compare_digest(expected, candidate):
            return True, offset
    return False, None

# Shared state
STATE_LOCK = Lock()
shared_secret = os.environ.get("SMARTLOCK_SHARED_SECRET", "your_secret_here")
bluetooth_enabled = True
door_locked = True
relock_timer = None
RELOCK_SECONDS = int(os.environ.get("RELOCK_SECONDS", "5"))

def start_relock_timer(seconds: int = RELOCK_SECONDS):
    global relock_timer
    def relock():
        global door_locked
        with STATE_LOCK:
            door_locked = True
        print("locked")
    if relock_timer is not None:
        try:
            relock_timer.cancel()
        except Exception:
            pass
    relock_timer = Timer(seconds, relock)
    relock_timer.daemon = True
    relock_timer.start()

# Routes
@app.route("/")
def index():
    with STATE_LOCK:
        return render_template("index.html", bluetooth_enabled=bluetooth_enabled, door_locked=door_locked)

@app.route("/enter-otp")
def enter_otp_page():
    with STATE_LOCK:
        return render_template("enter_otp.html", door_locked=door_locked)

@app.route("/get_otp")
def get_otp():
    now = time.time()
    step = 15
    elapsed = now % step
    remaining = int(step - elapsed)
    otp = generate_otp(shared_secret, for_time=now, step=step, digits=4)
    return jsonify({"otp": otp, "remaining": remaining, "step": step})

@app.route("/verify_otp", methods=["POST"])
def verify_otp_route():
    # Accept JSON or form-encoded data. Extract 'otp' robustly.
    data = {}
    try:
        js = request.get_json(silent=True)
        if isinstance(js, dict):
            data = js
        else:
            data = request.form or {}
    except Exception:
        data = request.form or {}
    candidate = data.get("otp", "") if hasattr(data, "get") else ""

    ok, offset = verify_otp(candidate, shared_secret, window=3)
    if ok:
        with STATE_LOCK:
            global door_locked
            door_locked = False
        print("unlocked (OTP, offset=" + str(offset) + ")")
        start_relock_timer(RELOCK_SECONDS)
        return jsonify({"ok": True, "message": f"Unlocked (will relock in {RELOCK_SECONDS}s)", "offset": offset})
    return jsonify({"ok": False, "message": "Wrong OTP"}), 401

@app.route("/unlock_bt", methods=["POST"])
def unlock_bt():
    global door_locked
    with STATE_LOCK:
        if not bluetooth_enabled:
            return jsonify({"ok": False, "message": "Bluetooth disabled"}), 403
        door_locked = False
    print("unlocked (button)")
    start_relock_timer(RELOCK_SECONDS)
    return jsonify({"ok": True})

@app.route("/toggle_bt", methods=["POST"])
def toggle_bt():
    global bluetooth_enabled
    with STATE_LOCK:
        bluetooth_enabled = not bluetooth_enabled
    print("Bluetooth enabled =", bluetooth_enabled)
    return jsonify({"bluetooth_enabled": bluetooth_enabled})

@app.route("/media_unlock", methods=["POST"])
def media_unlock():
    global door_locked
    with STATE_LOCK:
        door_locked = False
    print("unlocked (media key)")
    start_relock_timer(RELOCK_SECONDS)
    return jsonify({"ok": True, "message": "Unlocked (media key)"}), 200

@app.route("/status")
def status():
    with STATE_LOCK:
        return jsonify({"bluetooth_enabled": bluetooth_enabled, "door_locked": door_locked})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
