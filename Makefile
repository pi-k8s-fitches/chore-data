IMAGE=pi-k8s-fitches-nandy-data
VERSION=0.5
ACCOUNT=gaf3
NAMESPACE=fitches
VOLUMES=-v ${PWD}/lib/:/opt/pi-k8s/lib/ -v ${PWD}/test/:/opt/pi-k8s/test/ -v ${PWD}/mysql:/opt/pi-k8s/mysql

.PHONY: build shell test mysql tag

build:
	docker build . -t $(ACCOUNT)/$(IMAGE):$(VERSION)

shell:
	docker run -it $(VOLUMES) $(ACCOUNT)/$(IMAGE):$(VERSION) sh

test:
	docker-compose -f docker-compose.yml up --abort-on-container-exit --exit-code-from unittest

mysql:
	docker-compose -f docker-compose-mysql.yml up --abort-on-container-exit --exit-code-from dump
	
tag:
	git tag -a "v$(VERSION)" -m "Version $(VERSION)"
