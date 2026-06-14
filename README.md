# Geonovum dashboard

Deze repository bevat het dashboard voor een overzicht van Geonovum- en
BROprogramma-repositories, ReSpec-documenten, beheerindicatoren en
publicatiechecks.

Live dashboard:

[Dashboard](https://geonovum.github.io/geonovum-dashboard/)

## Wat wordt bijgehouden

Het dashboard combineert handmatig beheerde overzichten met automatisch
gegenereerde data:

- GitHub-repositories van `Geonovum` en `BROprogramma`
- ReSpec-documenten per repository
- gebruikte ReSpec-configuratie en publicatielocaties
- laatste repository-activiteit en contactkandidaat
- open issues en pull requests
- aanwezigheid van beheerbestanden zoals `README`, `LICENSE`,
  workflowconfiguratie en `CODEOWNERS`
- linkcheck-resultaten
- WCAG-checkresultaten

## Belangrijkste bestanden

| bestand | doel |
| --- | --- |
| `index.html` | ReSpec-ingangspunt voor het dashboard |
| `dashboardoverzicht.md` | automatisch gegenereerde samenvatting en actielijst |
| `githubrepos.md` | automatisch gegenereerd repositoryoverzicht |
| `respecdocuments.md` | automatisch gegenereerd ReSpec-documentoverzicht |
| `brokenlinks.md` | automatisch gegenereerd linkcheckrapport |
| `listGeonovumRepos.py` | haalt GitHub- en ReSpec-data op |
| `generateBrokenLinks.py` | zet Muffet JSON-output om naar `brokenlinks.md` |
| `.checks/` | gegenereerde checkresultaten voor linkcheck en WCAG |
| `snapshot.html` | door ReSpec gegenereerde HTML-snapshot |

De overige Markdown-bestanden, zoals `informatiemodellen.md`,
`conceptenbibliotheken.md` en `svn.md`, bevatten aanvullende
dashboardsecties.

## Automatische workflow

De workflow draait via GitHub Actions:

- bij iedere push
- bij pull requests
- dagelijks om `04:17 UTC`
- bij releases

De hoofdworkflow staat in `.github/workflows/main.yml`. De build- en
checkstappen staan in `.github/workflows/build.yml`.

Tijdens een push of dagelijkse run worden de gegenereerde bestanden
teruggeschreven naar dezelfde branch. Deze commit wordt gemaakt door
`github-actions[bot]`, zodat duidelijk is welke wijzigingen automatisch zijn
gegenereerd.

De workflow voert onder andere deze stappen uit:

1. GitHub-repositorydata ophalen.
2. `dashboardoverzicht.md`, `githubrepos.md` en `respecdocuments.md` genereren.
3. ReSpec HTML-snapshot genereren.
4. HTML-validatie uitvoeren.
5. WCAG 2.2-check uitvoeren met Axe.
6. Linkcheck uitvoeren met Muffet.
7. `brokenlinks.md` genereren uit de linkcheck-output.
8. Checkresultaten en snapshot committen.

## Lokaal draaien

Voor het genereren van de repository- en ReSpec-overzichten:

```sh
python3 listGeonovumRepos.py
```

Voor het genereren van het broken-links rapport uit bestaande Muffet-output:

```sh
python3 generateBrokenLinks.py \
  .checks/link-check.json \
  brokenlinks.md \
  .checks/link-check.txt
```

Voor het genereren van de HTML-snapshot:

```sh
npx respec --localhost --src index.html --out snapshot.html
```

Voor een lokale preview:

```sh
python3 -m http.server 8080
```

Open daarna:

<http://localhost:8080/>

## GitHub-token

`listGeonovumRepos.py` gebruikt de GitHub API. In GitHub Actions wordt
automatisch `GH_TOKEN` gezet.

Lokaal werkt het script zonder token, maar met een token zijn rate limits
minder snel een probleem:

```sh
export GH_TOKEN=...
python3 listGeonovumRepos.py
```

## Organisaties toevoegen

De te scannen organisaties staan in `listGeonovumRepos.py`:

```py
ORGS = ["Geonovum", "BROprogramma"]
```

Voeg daar een organisatie aan toe als die in dezelfde dashboardrapportage moet
worden meegenomen.

## Linkcheck

De linkcheck gebruikt Muffet en schrijft JSON-output naar
`.checks/link-check.json`.

`generateBrokenLinks.py` vertaalt die output naar `brokenlinks.md`. Daarbij
worden tijdelijke of niet-actiegerichte responses, zoals `401`, `403` en `429`,
niet als kapotte link behandeld. Zo blijft het dashboard gericht op links die
waarschijnlijk echt aandacht nodig hebben.

## Publicatie

GitHub Pages publiceert de inhoud van `main`.

Voor gewone wijzigingen:

1. Werk op een featurebranch, bijvoorbeeld `dashboard-daily-update`.
2. Push de branch.
3. Controleer de GitHub Actions-run.
4. Maak een pull request naar `main`.
5. Na merge wordt GitHub Pages opnieuw opgebouwd.

## Bekende aandachtspunten

- De workflow commit gegenereerde bestanden terug. Daardoor kunnen na een push
  extra commits van `github-actions[bot]` verschijnen.
- Linkchecks op externe sites kunnen per netwerk of moment verschillen.
- GitHub-webpagina's kunnen rate limits geven; daarom worden `429` responses
  niet als kapotte links geteld.
- De README beschrijft dit dashboardrepository. Gebruik `NL-ReSpec-template`
  voor documenttemplates.
