# listener.py
from pynput import keyboard
import requests, time, os, sys
FLASK_URL = os.environ.get("SMARTLOCK_FLASK_URL","http://127.0.0.1:5000/media_unlock")
DEBOUNCE = float(os.environ.get("LISTENER_DEBOUNCE","1.0"))
last = 0
def notify():
    try:
        r = requests.post(FLASK_URL, timeout=2)
        print(f"[listener] server: {r.status_code} {r.text}")
    except Exception as e:
        print(f"[listener] error: {e}")
def on_press(key):
    global last
    try:
        if key == keyboard.Key.media_play_pause:
            now = time.time()
            if now - last < DEBOUNCE:
                return
            last = now
            print("[listener] Media key detected. Unlocking...")
            notify()
    except Exception as e:
        print('[listener] exception', e)
def main():
    print("[listener] Running. Press Play/Pause key to unlock.")
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()
if __name__ == '__main__':
    main()
