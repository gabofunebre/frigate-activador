# main.py
from flask import Flask
from rutas import registrar_rutas
from funciones import (
    load_session_version,
    save_session_version,
    iniciar_monitor_inactividad,
    configurar_logging,
    SESSION_VERSION
)
from datetime import timedelta

# -------------------------------
# Configuración general
# -------------------------------
CONTAINER_NAME = "frigate"
FRIGATE_URL = "http://frigate.gabo.ar"
CHECK_INTERVAL = 300           # Intervalo para revisar actividad (segundos)
INACTIVIDAD_MINUTOS = 10       # Tiempo sin actividad para apagar el contenedor
LOG_FILE = "log.txt"
SESSION_FILE = "session_version.txt"
ACTIVITY_FLAG = "GET /api"     # Patrón para detectar actividad en logs

LOGIN_USER = "taller"
LOGIN_PASS = "gabo5248"

# -------------------------------
# Inicialización
# -------------------------------
app = Flask(__name__)
app.secret_key = "9fda2798cf2ae321s1fdu888od9sddw68qa68d03f"
app.permanent_session_lifetime = timedelta(hours=3)

configurar_logging(LOG_FILE)
load_session_version(SESSION_FILE)
iniciar_monitor_inactividad(
    container_name=CONTAINER_NAME,
    check_interval=CHECK_INTERVAL,
    inactividad_minutos=INACTIVIDAD_MINUTOS,
    activity_flag=ACTIVITY_FLAG,
    session_file=SESSION_FILE,
)

# -------------------------------
# Registro de rutas y arranque
# -------------------------------
registrar_rutas(
    app,
    container_name=CONTAINER_NAME,
    frigate_url=FRIGATE_URL,
    login_user=LOGIN_USER,
    login_pass=LOGIN_PASS,
    session_file=SESSION_FILE,
    log_file=LOG_FILE
)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5544)
