# arduino_bridge.py
import os, time, sys, requests
try:
    import serial
except Exception as e:
    serial = None
    print("[bridge] pyserial missing:", e)
# Candidate URLs to try if FLASK_STATUS_URL not set
env_url = os.environ.get("FLASK_STATUS_URL", "").strip()
CANDIDATES = []
if env_url:
    CANDIDATES.append(env_url)
CANDIDATES += [
    "http://127.0.0.1:5000/status",
    "http://localhost:5000/status",
    "http://127.0.0.1:8000/status",
    "http://localhost:8000/status",
]
ARDUINO_PORT = os.environ.get("ARDUINO_PORT","COM5")
ARDUINO_BAUD = int(os.environ.get("ARDUINO_BAUD","9600"))
ARDUINO_UNLOCK_BYTE = os.environ.get("ARDUINO_UNLOCK_BYTE","a").encode('utf-8')[:1]
POLL_INTERVAL = float(os.environ.get("POLL_INTERVAL","0.6"))
DEBOUNCE_SECONDS = float(os.environ.get("DEBOUNCE_SECONDS","1.0"))
REQUEST_TIMEOUT = float(os.environ.get("REQUEST_TIMEOUT","1.0"))
serial_obj = None
last_state = None
last_send = 0

def find_working_url():
    for u in CANDIDATES:
        try:
            r = requests.get(u, timeout=REQUEST_TIMEOUT)
            if r.status_code == 200:
                try:
                    j = r.json()
                    if isinstance(j, dict) and 'door_locked' in j:
                        print(f"[bridge] using status URL: {u}")
                        return u
                except Exception:
                    pass
            print(f"[bridge] tried {u} -> {r.status_code}")
        except Exception as e:
            print(f"[bridge] tried {u} -> error: {e}")
    return None

def try_open():
    global serial_obj
    if serial is None:
        return False
    if serial_obj:
        return True
    try:
        serial_obj = serial.Serial(ARDUINO_PORT, ARDUINO_BAUD, timeout=1)
        time.sleep(2)
        print(f"[bridge] opened {ARDUINO_PORT} @ {ARDUINO_BAUD}")
        return True
    except Exception as e:
        serial_obj = None
        print(f"[bridge] cannot open serial {ARDUINO_PORT}: {e}")
        return False

def send_unlock():
    global last_send, serial_obj
    now = time.time()
    if now - last_send < DEBOUNCE_SECONDS:
        print("[bridge] debounced")
        return False
    if not try_open():
        print("[bridge] serial not available")
        return False
    try:
        serial_obj.write(ARDUINO_UNLOCK_BYTE)
        try:
            serial_obj.flush()
        except:
            pass
        last_send = now
        print("[bridge] sent unlock byte")
        return True
    except Exception as e:
        print("[bridge] write failed:", e)
        try:
            if serial_obj:
                serial_obj.close()
        except:
            pass
        serial_obj = None
        return False

def fetch_status(url):
    try:
        r = requests.get(url, timeout=REQUEST_TIMEOUT)
        return r
    except Exception as e:
        #print("[bridge] status err:", e)
        return None

def main():
    global last_state
    print("[bridge] Starting bridge. Probing Flask status endpoint...")
    status_url = find_working_url()
    if not status_url:
        print("[bridge] Could not find a working /status endpoint. Exiting.")
        sys.exit(1)
    print("[bridge] polling", status_url)
    try_open()
    while True:
        r = fetch_status(status_url)
        if r is None:
            time.sleep(POLL_INTERVAL)
            continue
        if r.status_code != 200:
            print(f"[bridge] Status endpoint returned {r.status_code}")
            time.sleep(POLL_INTERVAL)
            continue
        try:
            st = r.json()
        except Exception:
            time.sleep(POLL_INTERVAL)
            continue
        locked = st.get('door_locked', True)
        if last_state is None:
            last_state = locked
        else:
            if last_state == True and locked == False:
                print("[bridge] detected locked->unlocked")
                send_unlock()
            last_state = locked
        time.sleep(POLL_INTERVAL)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("[bridge] exiting")
        try:
            if serial_obj:
                serial_obj.close()
        except:
            pass
        sys.exit(0)
