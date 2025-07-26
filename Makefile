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

## Comprobar si el servicio está activo (sólo imprime 'active' o 'inactive')
active:
	systemctl is-active $(SERVICE)

## Mostrar logs completos del servicio
logs:
	sudo journalctl -u $(SERVICE)

## Seguir logs en tiempo real del servicio
logsf:
	sudo journalctl -u $(SERVICE) -f

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

## Mostrar esta ayuda con descripciones
help:
	@awk '/^##/ {sub(/^## /, "", $$0); desc=$$0; getline; \
	 if($$1 ~ /^[a-zA-Z_-]+:/){name=$$1; sub(/:/, "", name); \
 printf "\033[36m%-15s\033[0m %s\n", name, desc}}' $(MAKEFILE_LIST)
