NAME=hub
SALT=$(shell openssl rand -base64 16)

.PHONY : build
build:
	./version.sh

.PHONY : clean
clean:
	./version.sh --reset
	find . -name "*.pyc" -o -name "*.pyo" | xargs -n1 rm -f
	rm -Rf build *.egg-info
