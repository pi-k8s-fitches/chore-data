IMAGE=pi-k8s-fitches-nandy-data
VERSION=0.5
ACCOUNT=gaf3
NAMESPACE=fitches
VOLUMES=-v ${PWD}/lib/:/opt/pi-k8s/lib/ -v ${PWD}/test/:/opt/pi-k8s/test/ -v ${PWD}/setup.py:/opt/pi-k8s/setup.py

.PHONY: build shell test tag push

build:
	docker build . -t $(ACCOUNT)/$(IMAGE):$(VERSION)

shell:
	docker run -it $(VOLUMES) $(ACCOUNT)/$(IMAGE):$(VERSION) sh

test:
	docker-compose -f docker-compose.yml up --build --abort-on-container-exit --exit-code-from unittest

tag:
	git tag -a "v$(VERSION)" -m "Version $(VERSION)"

push:
	git push origin "v$(VERSION)"