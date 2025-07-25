SERVICE=frigate-activador.service
CONTAINER=frigate

.PHONY: start stop restart status active logs logsf logtxt logs-fri logs-fri-f help push

## Iniciar el servicio via systemd
start:
	sudo systemctl start $(SERVICE)

## Detener el servicio
stop:
	sudo systemctl stop $(SERVICE)

## Reiniciar el servicio
restart:
	sudo systemctl restart $(SERVICE)

## Mostrar estado detallado del servicio
status:
	systemctl status $(SERVICE)

## Comprobar si el servicio esta activo
active:
	systemctl is-active $(SERVICE)

## Mostrar logs completos del servicio
logs:
	journalctl -u $(SERVICE)

## Seguir logs en tiempo real del servicio
logsf:
	journalctl -u $(SERVICE) -f

## Seguir el archivo log.txt generado por el activador
logtxt:
	tail -f log.txt

## Ver logs del contenedor Frigate
logs-fri:
	docker logs $(CONTAINER)

## Seguir los logs del contenedor Frigate en tiempo real
logs-fri-f:
	docker logs -f $(CONTAINER)

## Realizar add, commit y push con un mensaje
push:
	@$(eval MSG := $(filter-out $@,$(MAKECMDGOALS)))
	@if [ -z "$(MSG)" ]; then \
echo 'Uso: make push "mensaje de commit"'; \
exit 1; \
fi
	git add .
	git commit -m "$(MSG)"
	git push

## Mostrar esta ayuda
help:
	@grep -E '^[a-zA-Z_-]+:' Makefile | sed 's/^/ - /'
