.PHONY: repos

all: githubrepos.md respecbase.md


githubrepos.md: listGeonovumRepos.py
	python3 listGeonovumRepos.py

respecbase.md:
	#(cd repos; grep -oP "src=['\"]https://.*?respec.*?.js['\"]" */index.html */*/index.html */*/*/index.html | sed 's/\/index.html:src=./ | /g' | sed 's/^/| /' | sed 's/.$/ |/' | grep -v mermaid | grep -v docs.geostandaarden.nl | grep -v config.js > ../respecbase.md)
	(cd repos; grep -oP "src=['\"]https://.*?respec.*?.js['\"]" */index.html */*/index.html */*/*/index.html | sed 's/\/index.html:src=./ | /g' | sed 's/^/| /' | sed 's/.$$/ |/' | grep -v mermaid | grep -v docs.geostandaarden.nl | grep -v config.js > ../respecbase.md)

repos:
	(cd repos; python3 ../checkoutGeonovumRepos.py)
clean:
	rm -f respecbase.md
