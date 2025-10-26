build:
	docker build -t normaliser:local .

up:
	docker compose -f compose.yml up -d

wait:
	@echo "Waiting for container to start..."
	@sleep 5
	@for i in 1 2 3 4 5; do \
		if curl -fsS http://localhost:8000/healthz >/dev/null 2>&1; then \
			echo "Service is up!"; \
			exit 0; \
		else \
			echo "Waiting... ($$i)"; \
			sleep 2; \
		fi; \
	done; \
	echo "Service failed to start" && exit 1

smoke:
	curl -fsS http://localhost:8000/openapi.json | head -c 80
	curl -fsS -X POST http://localhost:8000/normalise \
	  -H 'Content-Type: application/json' \
	  -d '{"messy_title":"BILLY THE EXTERMINATOR-DAY (R)"}'

deploy: build up wait smoke

down:
	docker compose -f compose.yml down
