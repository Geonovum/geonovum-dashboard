.PHONY: repos

all: githubrepos.md


githubrepos.md: listGeonovumRepos.py
	python3 listGeonovumRepos.py

respecdocuments.txt:
	(cd repos; grep -oP "src=['\"]https://.*?respec.*?.js['\"]" */index.html */*/index.html */*/*/index.html > ../respecdocuments.md)

repos:
	mkdir repos
	(cd repos; python3 ../checkoutGeonovumRepos.py)
