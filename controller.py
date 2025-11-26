# controller.py
import subprocess, sys, time, os
from pathlib import Path
from threading import Thread

BASE = Path(__file__).resolve().parent
PY = sys.executable

procs = []

def stream(proc, name):
    for line in proc.stdout:
        try:
            print(f"[{name}] {line.decode().rstrip()}")
        except Exception:
            print(f"[{name}]", line)

def start(name, script):
    path = str(BASE / script)
    env = os.environ.copy()
    # ensure FLASK_STATUS_URL env is set for bridge and listener
    env.setdefault('FLASK_STATUS_URL', 'http://127.0.0.1:5000/status')
    p = subprocess.Popen([PY, path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=str(BASE), env=env)
    t = Thread(target=stream, args=(p, name), daemon=True)
    t.start()
    procs.append(p)
    print(f"[controller] started {name}")

def main():
    start('FLASK-APP','app.py')
    time.sleep(1)
    start('LISTENER','listener.py')
    time.sleep(0.5)
    start('BRIDGE','arduino_bridge.py')
    print('All processes started. Press Ctrl+C to stop.')
    try:
        while True:
            time.sleep(0.5)
            # if any proc exited, break
            if any(p.poll() is not None for p in procs):
                print('One of the child processes exited. Stopping controller.')
                break
    except KeyboardInterrupt:
        print('Controller received Ctrl+C. Terminating children...')
    finally:
        for p in procs:
            try:
                p.terminate()
            except:
                pass
        time.sleep(0.6)
        for p in procs:
            try:
                if p.poll() is None:
                    p.kill()
            except:
                pass
        print('Controller exiting.')

if __name__ == '__main__':
    main()
