.PHONY: test cover

COVERED_PACKAGES = id3vx.tag,id3vx.frame,id3vx.codec,id3vx.text

test:
	python -m nose

cover:
	python -m nose --with-coverage --cover-inclusive --cover-html --cover-erase --cover-package=${COVERED_PACKAGES}

lint:
	python -m flake8

clean:
	rm .coverage
	rm -rf cover/