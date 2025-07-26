# FRIGATE ACTIVADOR - DOCUMENTACIÓN Y USO

Este servicio permite iniciar el contenedor Docker de Frigate **bajo demanda** cuando un usuario accede al sitio. Muestra una pantalla de espera (`loading.html`) hasta que el contenedor esté listo (`healthy`), y luego redirige automáticamente al sitio real.

También:

- Presenta una pantalla de login al acceder a `/`
- Monitorea la actividad del usuario en los logs del contenedor
- Si pasan más de 10 minutos sin peticiones `GET`, apaga automáticamente el contenedor para ahorrar recursos

---

### 📁 UBICACIÓN DEL CÓDIGO

```
/srv/dev-disk-by-uuid-1735d6ab-2a75-4dc4-91a9-b81bb3fda73d/Servicios/CamarasTa/frigate-activador/
```

---

### ⚙️ CONFIGURACIÓN INICIAL

1. Copiar y activar el servicio systemd:
   ```bash
   sudo cp frigate-activador.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable frigate-activador.service
   sudo systemctl start frigate-activador.service
   ```

2. En Nginx (o Nginx Proxy Manager), crear un proxy que redirija `frigate.gabo.ar` a `http://127.0.0.1:5544`.

3. Asegurarse de que el puerto `5544` esté accesible desde donde corre Nginx.

---

### ▶️ USO GENERAL

- Iniciar:
  ```bash
  sudo systemctl start frigate-activador.service
  ```

- Detener:
  ```bash
  sudo systemctl stop frigate-activador.service
  ```

- Reiniciar:
  ```bash
  sudo systemctl restart frigate-activador.service
  ```

- Ver estado:
  ```bash
  systemctl status frigate-activador.service
  ```

- Ver si está activo (sólo texto):
  ```bash
  systemctl is-active frigate-activador.service
  ```

- Ver logs en tiempo real:
  ```bash
  journalctl -u frigate-activador.service -f
  ```

- Ver logs completos:
  ```bash
  journalctl -u frigate-activador.service
  ```

---

### 🛠 COMANDOS MAKE

Usá el `Makefile` incluido para facilitar la administración:

```bash
make start         # Inicia el servicio
make stop          # Detiene el servicio
make restart       # Reinicia el servicio
make status        # Estado detallado
make active        # Solo muestra si está activo
make logs          # Logs completos del servicio
make logsf         # Logs en tiempo real
make logtxt        # Tail del archivo log.txt
make logs-fri      # Logs del contenedor Frigate
make logs-fri-f    # Logs en tiempo real de Frigate
make push "msg"    # Git add + commit + push
make help          # Lista de comandos disponibles
```

---

### 🔄 FUNCIONAMIENTO INTERNO

1. El usuario accede a `http://frigate.gabo.ar` (proxy vía Nginx).
2. Se muestra el login. Si las credenciales son válidas:
3. Se inicia el contenedor `frigate` si no estaba corriendo.
4. Se muestra `loading.html` mientras se espera que el contenedor esté `healthy`.
5. Una vez listo, el usuario es redirigido automáticamente al sitio real.
6. Paralelamente, un monitor de inactividad se lanza:
   - Cada 5 minutos revisa los logs recientes.
   - Espera al menos 10 minutos desde que se inició.
   - Si no detecta `GET /api` en los logs → apaga el contenedor.
   - Todas las sesiones se invalidan automáticamente.

---

### 📝 LOGS PERSONALIZADOS

El activador genera su propio archivo rotativo:
```
./log.txt
```

Registra:

- Inicio y apagado del contenedor
- Errores al interactuar con Docker
- Fallos de login (con IP)
- Excepciones detectadas

---

### ⚠️ IMPORTANTE

- Si el contenedor `frigate` se inicia **por fuera** del activador, el servicio puede apagarlo por inactividad.
- Para un uso correcto, los accesos deben ser iniciados **desde `/`**.
- No uses el servidor Flask en producción directamente. El servicio systemd está preparado para usar Gunicorn.
