
# Makefile
VERSION := 0.0.1
BE_IMAGE_NAME := browser_auto_fast_api_backend_1
DOCKER_COMPOSE_FILE := docker-compose-dev.yml

down: 
	docker-compose -f $(DOCKER_COMPOSE_FILE) down 
	docker system prune -f

build: 
	docker-compose -f $(DOCKER_COMPOSE_FILE) build --no-cache

up: 
	docker-compose -f $(DOCKER_COMPOSE_FILE) down 
	docker-compose -f $(DOCKER_COMPOSE_FILE) build --no-cache
	docker-compose -f $(DOCKER_COMPOSE_FILE) up -d --build 

stop-be:
	docker stop ${BE_IMAGE_NAME}
	docker rm ${BE_IMAGE_NAME}

logs-be:
	docker logs $(BE_IMAGE_NAME) -f --tail 150