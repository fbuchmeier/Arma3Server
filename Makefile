define validate-shell =
	set -e
	shopt -s globstar
	for s in **/*.sh ; do
		shellcheck -S info "${s}"
		echo "✓ Validating script ${s}"
	done
endef

define validate-markdown =
	set -e
	shopt -s globstar
	for m in **/*.md ; do
		mdl "${m}"
		echo "✓ Validating Markdown ${m}"
	done
endef

.SILENT: validate validate-shell validate-markdown test release

.ONESHELL:
SHELL := /bin/bash

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

validate-shell: ; $(value validate-shell)

validate-markdown: ; $(value validate-markdown)

validate: validate-shell validate-markdown

format:
	black *.py

test:
	python3 -m doctest *.py

release: format validate test build publish
	
	