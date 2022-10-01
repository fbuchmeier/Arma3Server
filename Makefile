build:
	docker build -t fbuchmeier/arma3server:${VERSION} .

publish: build
	docker push fbuchmeier/arma3server:${VERSION}

run: build
	docker run --rm -it fbuchmeier/arma3server:${VERSION}

