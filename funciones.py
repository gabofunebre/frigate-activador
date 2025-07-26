# funciones.py
import subprocess
import threading
import logging
import time
import os
from datetime import timedelta
from logging.handlers import RotatingFileHandler

# -------------------------------
# Variables globales
# -------------------------------
SESSION_VERSION = 0
_session_lock = threading.Lock()
monitor_activo = False
inicio_monitor = 0.0
logger = logging.getLogger("activador")

# -------------------------------
# Logging
# -------------------------------
def configurar_logging(log_file):
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(log_file, maxBytes=3 * 1024 * 1024, backupCount=1)
    handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s'))
    logger.addHandler(handler)

def log_event(mensaje):
    logger.info(mensaje)

# -------------------------------
# Control de sesión
# -------------------------------
def load_session_version(session_file):
    global SESSION_VERSION
    try:
        with open(session_file) as f:
            SESSION_VERSION = int(f.read().strip())
    except:
        SESSION_VERSION = 0

def save_session_version(session_file):
    with open(session_file, "w") as f:
        f.write(str(SESSION_VERSION))

# -------------------------------
# Control del contenedor
# -------------------------------
def container_running(container_name):
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
            capture_output=True, text=True
        )
        return container_name in result.stdout.splitlines()
    except FileNotFoundError:
        log_event("Comando 'docker' no encontrado al verificar contenedores")
        return False

def container_ready(container_name):
    try:
        output = subprocess.check_output([
            "docker", "inspect", "--format",
            "{{.State.Health.Status}}", container_name
        ], text=True).strip()
        return output == "healthy"
    except:
        return False

def start_frigate(container_name):
    global monitor_activo, inicio_monitor
    if not container_running(container_name):
        log_event("Iniciando contenedor Frigate")
        try:
            subprocess.run(["docker", "start", container_name], check=True)
        except subprocess.CalledProcessError as e:
            log_event(f"Error al iniciar Frigate: {e}")
            return
        except FileNotFoundError:
            log_event("Comando 'docker' no encontrado al intentar iniciar Frigate")
            return
    inicio_monitor = time.time()
    if not monitor_activo:
        threading.Thread(
            target=monitor_usage,
            args=(container_name, ),
            daemon=True
        ).start()
        monitor_activo = True

def stop_frigate(container_name, session_file):
    global monitor_activo, inicio_monitor, SESSION_VERSION
    log_event("Deteniendo contenedor Frigate por inactividad")
    try:
        subprocess.run(["docker", "stop", container_name], check=True)
    except FileNotFoundError:
        log_event("Comando 'docker' no encontrado al intentar detener Frigate")
        return
    monitor_activo = False
    inicio_monitor = 0.0
    with _session_lock:
        SESSION_VERSION += 1
        save_session_version(session_file)

# -------------------------------
# Monitor de inactividad
# -------------------------------
def usuario_activo_en_logs(container_name, activity_flag, minutos):
    try:
        logs = subprocess.check_output([
            "docker", "logs", "--since", f"{minutos}m", container_name
        ], text=True)
    except Exception as e:
        log_event(f"Error leyendo logs del contenedor: {e}")
        return False

    for linea in reversed(logs.splitlines()):
        if activity_flag in linea:
            return True
    return False

def monitor_usage(container_name):
    global inicio_monitor
    while container_running(container_name):
        time.sleep(300)
        if time.time() - inicio_monitor < 600:
            continue
        if not container_ready(container_name):
            log_event("Contenedor no healthy, se pospone check")
            continue
        if not usuario_activo_en_logs(container_name, "GET /api", 10):
            stop_frigate(container_name, "session_version.txt")
            break

def iniciar_monitor_inactividad(container_name, check_interval, inactividad_minutos, activity_flag, session_file):
    global monitor_activo, inicio_monitor
    if not container_running(container_name):
        return
    inicio_monitor = time.time()
    if not monitor_activo:
        threading.Thread(
            target=monitor_usage,
            args=(container_name,),
            daemon=True
        ).start()
        monitor_activo = True
