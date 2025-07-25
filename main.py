from flask import Flask, send_from_directory, redirect, jsonify, request, session
import subprocess
import threading
import time
import os
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)

# Configuración
CONTAINER_NAME = "frigate"
FRIGATE_URL = "http://frigate.gabo.ar"
CHECK_INTERVAL = 300  # cada 5 min se evalúa la actividad
INACTIVIDAD_MINUTOS = 10
LOG_FILE = "log.txt"

# Credenciales de acceso
LOGIN_USER = "taller"
LOGIN_PASS = "gabo5248"

app.secret_key = "9fda2798cf2ae321s1fdu888od9sddw68qa68d03f"
monitor_activo = False
inicio_monitor = 0.0

# Configurar registro de eventos con rotación
logger = logging.getLogger("activador")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(LOG_FILE, maxBytes=3 * 1024 * 1024, backupCount=1)
handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s'))
logger.addHandler(handler)



def log_event(mensaje):
    logger.info(mensaje)


def container_running(name=CONTAINER_NAME):
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={name}", "--format", "{{.Names}}"],
            capture_output=True, text=True
        )
        return name in result.stdout.splitlines()
    except FileNotFoundError:
        log_event("Comando 'docker' no encontrado al verificar contenedores")
        return False


def start_frigate():
    global monitor_activo, inicio_monitor
    if not container_running():
        log_event("Iniciando contenedor Frigate")
        try:
            subprocess.run(["docker", "start", CONTAINER_NAME], check=True)
        except FileNotFoundError:
            log_event("Comando 'docker' no encontrado al intentar iniciar Frigate")
            return
        inicio_monitor = time.time()
        if not monitor_activo:
            threading.Thread(target=monitor_usage, daemon=True).start()
            monitor_activo = True


def stop_frigate():
    global monitor_activo, inicio_monitor
    log_event("Deteniendo contenedor Frigate por inactividad")
    try:
        subprocess.run(["docker", "stop", CONTAINER_NAME], check=True)
    except FileNotFoundError:
        log_event("Comando 'docker' no encontrado al intentar detener Frigate")
        return
    monitor_activo = False
    inicio_monitor = 0.0


def container_ready():
    try:
        output = subprocess.check_output([
            "docker", "inspect", "--format",
            "{{.State.Health.Status}}", CONTAINER_NAME
        ], text=True).strip()
        return output == "healthy"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def usuario_activo_en_logs():
    try:
        logs = subprocess.check_output([
            "docker",
            "logs",
            "--since",
            f"{INACTIVIDAD_MINUTOS}m",
            CONTAINER_NAME,
        ], text=True)
    except Exception as e:
        log_event(f"Error leyendo logs del contenedor: {e}")
        return False

    for linea in reversed(logs.splitlines()):
        if "GET" in linea:
            return True

    return False


def monitor_usage():
    global inicio_monitor
    while container_running():
        time.sleep(CHECK_INTERVAL)

        # Esperar al menos INACTIVIDAD_MINUTOS antes de evaluar la actividad
        if time.time() - inicio_monitor < INACTIVIDAD_MINUTOS * 60:
            continue

        if not container_ready():
            continue

        if not usuario_activo_en_logs():
            stop_frigate()
            break


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username")
        pw = request.form.get("password")
        if user == LOGIN_USER and pw == LOGIN_PASS:
            session["logged_in"] = True
            return redirect("/activar")
        return redirect("/?error=1")

    if session.get("logged_in"):
        return redirect("/activar")

    return send_from_directory(".", "login.html")


@app.route("/activar")
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
