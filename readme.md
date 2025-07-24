FRIGATE ACTIVADOR - DOCUMENTACIÓN Y USO
========================================

Este servicio permite iniciar el contenedor Docker de Frigate bajo demanda 
cuando un usuario accede al sitio, mostrando una pantalla de espera ("loading") 
hasta que el contenedor esté listo (estado healthy). 
Luego, redirige automáticamente al sitio real. 

Además, monitorea la actividad del usuario en los logs: 
si pasan más de 10 minutos sin actividad (peticiones GET), 
el servicio detiene el contenedor de Frigate para ahorrar recursos.

--------------------------------------------------
UBICACIÓN DEL CÓDIGO:
  /srv/dev-disk-by-uuid-1735d6ab-2a75-4dc4-91a9-b81bb3fda73d/Servicios/CamarasTa/frigate-activador/main.py

--------------------------------------------------
USO GENERAL
===========

▶️ Iniciar el servicio manualmente:
  sudo systemctl start frigate-activador.service

⏹️ Detener el servicio manualmente:
  sudo systemctl stop frigate-activador.service

🔁 Reiniciar el servicio:
  sudo systemctl restart frigate-activador.service

🔎 Ver estado actual del servicio:
  systemctl status frigate-activador.service

✅ Ver si el servicio está activo (simple):
  systemctl is-active frigate-activador.service

📋 Ver logs en tiempo real (salida por consola):
  journalctl -u frigate-activador.service -f

📅 Ver logs completos:
  journalctl -u frigate-activador.service


--------------------------------------------------
FUNCIONAMIENTO INTERNO
======================

1. El usuario accede a `http://frigate.gabo.ar` (redirigido por Nginx Proxy Manager).
2. Llega al servicio Flask del activador en el puerto 5544.
3. El activador:
   - Inicia el contenedor `frigate` (si no está corriendo).
   - Espera a que esté en estado `healthy` leyendo su estado con `docker inspect`.
   - Mientras tanto, muestra la pantalla `loading.html`.
   - Cuando el contenedor está listo, redirige al usuario al sitio real.
4. Luego inicia un proceso de monitoreo en segundo plano:
   - Cada 1 minuto chequea los últimos logs del contenedor.
   - Si no encuentra actividad (GETs) en los últimos 10 minutos, lo detiene automáticamente.
   - Finaliza el monitoreo (y no lo reinicia, salvo que se vuelva a acceder a `/`).

--------------------------------------------------
LOGS PERSONALIZADOS
===================

El activador registra eventos importantes en el archivo rotativo:
  ./log.txt (tamaño máximo 3 MB)

Ejemplos de entradas:
  - Inicio de Frigate
  - Detención por inactividad
  - Errores al iniciar o acceder al contenedor
  - Lectura de logs fallida

--------------------------------------------------

IMPORTANTE:
  - Si el contenedor `frigate` se inicia por fuera del activador, 
    **este servicio podría detenerlo** si no detecta usuarios activos.
  - Para que el servicio monitoree correctamente, 
    **es necesario que el contenedor se inicie desde el activador (/)**.

--------------------------------------------------
