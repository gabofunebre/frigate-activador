from flask import Flask, send_from_directory, redirect, jsonify
import subprocess
import threading
import time
import json
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# Configuración
CONTAINER_NAME = "frigate"
FRIGATE_URL = "http://frigate.gabo.ar"
CHECK_INTERVAL = 60  # cada 1 min se evalúa la actividad
INACTIVIDAD_MINUTOS = 10
LOG_FILE = "activador.log"
monitor_activo = False


def log_event(mensaje):
    timestamp = datetime.now().isoformat()
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {mensaje}\n")


def container_running(name=CONTAINER_NAME):
    result = subprocess.run(
        ["docker", "ps", "--filter", f"name={name}", "--format", "{{.Names}}"],
        capture_output=True, text=True
    )
    return name in result.stdout.splitlines()


def start_frigate():
    global monitor_activo
    if not container_running():
        log_event("Iniciando contenedor Frigate")
        subprocess.run(["docker", "start", CONTAINER_NAME], check=True)
        if not monitor_activo:
            threading.Thread(target=monitor_usage, daemon=True).start()
            monitor_activo = True


def stop_frigate():
    global monitor_activo
    log_event("Deteniendo contenedor Frigate por inactividad")
    subprocess.run(["docker", "stop", CONTAINER_NAME], check=True)
    monitor_activo = False


def container_ready():
    try:
        output = subprocess.check_output([
            "docker", "inspect", "--format",
            "{{.State.Health.Status}}", CONTAINER_NAME
        ], text=True).strip()
        return output == "healthy"
    except subprocess.CalledProcessError as e:
        return False


def usuario_activo_en_logs():
    try:
        logs = subprocess.check_output(["docker", "logs", "--tail", "200", CONTAINER_NAME], text=True)
    except Exception as e:
        log_event(f"Error leyendo logs del contenedor: {e}")
        return False

    umbral = datetime.utcnow() - timedelta(minutes=INACTIVIDAD_MINUTOS)

    for linea in reversed(logs.splitlines()):
        if "GET" in linea:
            try:
                timestamp_str = " ".join(linea.split()[0:2])
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
                if timestamp > umbral:
                    return True
            except Exception:
                continue

    return False


def monitor_usage():
    while container_running():
        time.sleep(CHECK_INTERVAL)

        if not container_ready():
            continue

        if not usuario_activo_en_logs():
            stop_frigate()
            break


@app.route("/")
def activar():
    def iniciar_y_esperar():
        try:
            log_event("Solicitud de activación recibida")
            start_frigate()
            while not container_ready():
                time.sleep(1)
        except Exception as e:
            log_event(f"Error al iniciar Frigate: {e}")

    threading.Thread(target=iniciar_y_esperar).start()
    return send_from_directory(".", "loading.html")


@app.route("/redirigir")
def redirigir():
    return redirect(FRIGATE_URL, code=302)


@app.route("/estado")
def estado():
    ready = container_ready()
    error = None
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE) as f:
            lineas = f.readlines()
            ultimos = [l for l in reversed(lineas) if "Error" in l]
            error = ultimos[0].strip() if ultimos else None
    return jsonify({"ready": ready, "error": error})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5544)
