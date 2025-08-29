#!/usr/bin/python3
#
# https://pygithub.readthedocs.io/en/latest/github_objects/Repository.html
#
from github import Github
import pprint
import os
import sys
import logging

f = open('githubrepos.md', 'w')

f.write('''
# Overzicht Github repos

Op dit dashboard zie je in één oogopslag alle openbare niet gearchiveerde Github repositories van Geonovum.

| Naam | Omschrijving | laatste wijziging| zichtbaarheid | archief |heeft_pages|nview|releases|teams|
|------|-------------|-----------|----|----|---|---|----|-----|
''')

#
# Het script maakt gebruik van de GitHub API hiervoor heb je een access token nodig.
# Dit script gaat ervan uit dat deze in een environment variable staat.
#
git = Github(os.environ['GH_TOKEN'])
org = git.get_organization('Geonovum')

#
# Itereer over alle repositories van Geonovum.
#
for repo in org.get_repos():
    #
    # Sla private repos over.
    #
    if repo.private:
        continue

    if repo.archived:
        continue

    #
    # Dit zou een list teams moeten opleveren maar werkt nog niet.
    #
    teams = ""
    for team in repo.get_teams():
        teams = teams + "'{}',".format(team.name)
    if not len(teams) == 0:
    	teams = teams[:-1]

    releases = ""
    for release in repo.get_releases():
        releases = releases + " " + release.tag_name



    description = repo.description
    if description is not None:
        description = description.replace('|',' ')
    else:
        description = ""

    if repo.has_pages:
        pages = "[pages](https://geonovum.github.io/{}/)".format(repo.name)
    else:
        pages = "";

    if not repo.archived:
        archief = "actief";
    else:
        archief = "archived";

    if not repo.private:
        zichtbaarheid = "publiek";
    else:
        zichtbaarheid = "prive";

    views = repo.get_views_traffic('week')

    f.write("| [{}]({}) | {} | {} | {} | {} | {} | {} | {} | {} |\n".format(
        repo.name,
        repo.html_url,
        description,
        repo.pushed_at.date(),
        zichtbaarheid,
        archief,
        pages,
        views['count'],
        releases,
        teams))
