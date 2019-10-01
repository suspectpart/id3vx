.PHONY: test cover

COVERED_PACKAGES = tag,frame,codec

test:
	python -m nose

cover:
	python -m nose --with-coverage --cover-inclusive --cover-html --cover-erase --cover-package=${COVERED_PACKAGES}

lint:
	python -m flake8

clean:
	rm .coverage
	rm -rf cover/