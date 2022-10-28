setup:
	mkdir -p ${PWD}/docker-data
	sudo chown 431 ${PWD}/docker-data

build:
	docker build -t fbuchmeier/arma3server:${VERSION} .

publish: build
	docker push fbuchmeier/arma3server:${VERSION}

run: setup build
	docker run -v ${PWD}/docker-data:/arma3 -P --rm -e STEAM_USER=${STEAM_USER} -e STEAM_PASSWORD=${STEAM_PASSWORD} -it fbuchmeier/arma3server:${VERSION}

debug: setup build
	docker run -v ${PWD}/docker-data:/arma3 -P --rm -e STEAM_USER=${STEAM_USER} -e STEAM_PASSWORD=${STEAM_PASSWORD} -it fbuchmeier/arma3server:${VERSION} bash

clean:
	rm -r ${PWD}/docker-data