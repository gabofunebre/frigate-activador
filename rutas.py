# rutas.py
from flask import request, redirect, session, send_from_directory, jsonify
import threading
import time
import os

from funciones import (
    SESSION_VERSION, _session_lock,
    log_event, container_ready,
    start_frigate, container_running
)

def registrar_rutas(app, container_name, frigate_url, login_user, login_pass, session_file, log_file):

    @app.before_request
    def validar_sesion():
        if session.get("version") != SESSION_VERSION:
            session.clear()

    @app.route("/", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            user = request.form.get("username")
            pw = request.form.get("password")
            if user == login_user and pw == login_pass:
                session["logged_in"] = True
                with _session_lock:
                    session["version"] = SESSION_VERSION
                session.permanent = True
                return redirect("/activar")

            ip = request.headers.get("X-Forwarded-For", request.remote_addr)
            log_event(f"Intento de login fallido desde {ip}")
            return redirect("/?error=1")

        if session.get("logged_in"):
            return redirect("/activar")

        return send_from_directory(".", "login.html")

    @app.route("/activar")
    def activar():
        if not session.get("logged_in"):
            return redirect("/")

        def iniciar_y_esperar():
            try:
                log_event("Solicitud de activación recibida")
                start_frigate(container_name)
                while not container_ready(container_name):
                    time.sleep(1)
            except Exception as e:
                log_event(f"Error al iniciar Frigate: {e}")

        threading.Thread(target=iniciar_y_esperar).start()
        return send_from_directory(".", "loading.html")

    @app.route("/redirigir")
    def redirigir():
        if not session.get("logged_in"):
            return redirect("/")
        return redirect(frigate_url, code=302)

    @app.route("/estado")
    def estado():
        if not session.get("logged_in"):
            return jsonify({"ready": False, "error": "Sesión expirada"})

        ready = container_ready(container_name)
        error = None

        if os.path.exists(log_file):
            try:
                with open(log_file) as f:
                    for linea in reversed(f.readlines()):
                        if "Error" in linea:
                            try:
                                timestamp_str = linea.split("]")[0].strip("[")
                                error_time = time.mktime(time.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f"))
                                if error_time > time.time() - 3600:
                                    error = linea.strip()
                                    break
                            except:
                                continue
            except Exception as e:
                error = f"Error leyendo log: {e}"

        return jsonify({"ready": ready, "error": error})
