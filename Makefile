IMAGE_NAME ?= filebin
CONTAINER_NAME ?= filebin
CONTAINER_INSTANCE ?= default

PORTS ?= -p 8081:80

.PHONY: build start stop rm

build: Dockerfile
	docker build -t $(IMAGE_NAME) -f Dockerfile .

irun:
	docker run --rm -it $(PORTS) $(IMAGE_NAME)

drun:
	docker run --rm --name $(CONTAINER_NAME)-$(CONTAINER_INSTANCE) -d $(PORTS) $(IMAGE_NAME)

stop:
	docker stop $(CONTAINER_NAME)-$(CONTAINER_INSTANCE)

default: build
