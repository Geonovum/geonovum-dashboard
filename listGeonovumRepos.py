#!/usr/bin/python3
#
# Genereert githubrepos.md met publieke, niet-gearchiveerde Geonovum repos.
#
from collections import Counter, defaultdict
from datetime import date
import json
import subprocess
import time
import urllib.parse

ORG = "Geonovum"
CODE_SEARCH_INTERVAL_SECONDS = 7
last_code_search_at = 0
RESPEC_BUILD_QUERIES = [
    {
        "query": "respec-geonovum",
        "label": "tools.geostandaarden",
        "build_url": "https://tools.geostandaarden.nl/respec/builds/respec-geonovum.js",
    },
    {
        "query": "respec-nlgov",
        "label": "respec-nlgov",
        "build_url": "https://gitdocumentatie.logius.nl/publicatie/respec/builds/respec-nlgov.js",
    },
    {
        "query": '"gitdocumentatie.logius.nl/publicatie/respec/fixup.js"',
        "label": "fixup",
        "build_url": "https://gitdocumentatie.logius.nl/publicatie/respec/fixup.js",
    },
    {
        "query": "respec-logius",
        "label": "respec-logius",
        "build_url": "https://publicatie.centrumvoorstandaarden.nl/respec/builds/respec-logius.js",
    },
    {
        "query": "respec-w3c",
        "label": "https://www.w3.org/Tools/respec/respec-w3c",
        "build_url": "https://www.w3.org/Tools/respec/respec-w3c",
    },
]


def github_json(path):
    output = subprocess.check_output(["gh", "api", path], text=True)
    return json.loads(output)


def github_code_search_json(path):
    global last_code_search_at

    elapsed = time.monotonic() - last_code_search_at
    if elapsed < CODE_SEARCH_INTERVAL_SECONDS:
        time.sleep(CODE_SEARCH_INTERVAL_SECONDS - elapsed)

    data = github_json(path)
    last_code_search_at = time.monotonic()
    return data


def github_graphql(query, variables):
    args = ["gh", "api", "graphql", "-f", "query={}".format(query)]
    for key, value in variables.items():
        args.extend(["-f", "{}={}".format(key, value)])

    output = subprocess.check_output(args, text=True)
    payload = json.loads(output)

    return payload["data"]


def table_text(value):
    if value is None:
        return ""
    return str(value).replace("|", " ").replace("\n", " ")


def is_bot_login(login):
    return bool(login) and login.lower().endswith("[bot]")


def markdown_user(user, fallback_name=""):
    if user and user.get("login"):
        login = table_text(user["login"])
        url = user.get("url")
        if url:
            return "[{}]({})".format(login, url)
        return login
    return table_text(fallback_name)


def latest_active_user(metadata):
    default_branch = metadata.get("defaultBranchRef") or {}
    target = default_branch.get("target") or {}
    history = (target.get("history") or {}).get("nodes", [])
    fallback = ""

    for commit in history:
        author = commit.get("author") or {}
        user = author.get("user")
        formatted_user = markdown_user(user, author.get("name", ""))

        if formatted_user and user and not is_bot_login(user.get("login")):
            return formatted_user

        if formatted_user and not user and not is_bot_login(formatted_user) and not fallback:
            fallback = formatted_user

    return fallback


def release_tags(metadata):
    releases = metadata.get("releases", {})
    nodes = releases.get("nodes", [])
    tags = [table_text(release.get("tagName", "")) for release in nodes if release.get("tagName")]

    if releases.get("totalCount", 0) > len(tags):
        tags.append("...")

    return " ".join(tags)


def github_file_location(repo, path):
    if path == "index.html":
        return repo["html_url"]

    directory = path.rsplit("/", 1)[0]
    encoded_directory = urllib.parse.quote(directory, safe="/")
    return "{}/tree/{}/{}".format(repo["html_url"], repo["default_branch"], encoded_directory)


def search_code(query):
    items = []
    page = 1

    while True:
        params = urllib.parse.urlencode({"q": query, "per_page": 100, "page": page})
        data = github_code_search_json("search/code?{}".format(params))
        batch = data.get("items", [])
        items.extend(batch)

        if len(batch) < 100:
            break
        page += 1

    return items


def is_index_html_search_item(item):
    path = item.get("path", "")
    return item.get("name") == "index.html" and (path == "index.html" or path.endswith("/index.html"))


def respec_documents(repos):
    documents = []
    repos_by_full_name = {repo["full_name"]: repo for repo in repos}
    seen = set()

    def append_document(repo, path, build_url, label):
        location = github_file_location(repo, path)
        key = (location, label)
        if key in seen:
            return
        seen.add(key)

        documents.append(
            {
                "location": location,
                "build_url": build_url,
                "label": label,
            }
        )

    for build in RESPEC_BUILD_QUERIES:
        query = "org:{} filename:index.html {}".format(ORG, build["query"])
        for item in search_code(query):
            if not is_index_html_search_item(item):
                continue

            repo = repos_by_full_name.get((item.get("repository") or {}).get("full_name"))
            if not repo:
                continue

            append_document(repo, item["path"], build["build_url"], build["label"])

    return sorted(documents, key=lambda document: document["location"].lower())


def batched(items, size):
    for index in range(0, len(items), size):
        yield items[index : index + size]


def list_repositories():
    repos = []
    page = 1

    while True:
        params = urllib.parse.urlencode({"per_page": 100, "page": page, "type": "public"})
        batch = github_json("orgs/{}/repos?{}".format(urllib.parse.quote(ORG), params))

        if not batch:
            break

        for repo in batch:
            if repo.get("private") or repo.get("archived") or repo.get("disabled"):
                continue
            repos.append(repo)

        if len(batch) < 100:
            break
        page += 1

    return repos


def repository_metadata(repo_names):
    metadata = {}

    for batch in batched(repo_names, 25):
        fields = []
        alias_to_name = {}

        for index, repo_name in enumerate(batch):
            alias = "repo{}".format(index)
            alias_to_name[alias] = repo_name
            fields.append(
                """
                {alias}: repository(owner: $owner, name: {repo_name}) {{
                  defaultBranchRef {{
                    target {{
                      ... on Commit {{
                        history(first: 25) {{
                          nodes {{
                            author {{
                              name
                              user {{
                                login
                                url
                              }}
                            }}
                          }}
                        }}
                      }}
                    }}
                  }}
                  releases(first: 10, orderBy: {{field: CREATED_AT, direction: DESC}}) {{
                    totalCount
                    nodes {{
                      tagName
                    }}
                  }}
                }}
                """.format(
                    alias=alias,
                    repo_name=json.dumps(repo_name),
                )
            )

        query = "query($owner: String!) {{ {} }}".format("\n".join(fields))
        data = github_graphql(query, {"owner": ORG})

        for alias, repo_name in alias_to_name.items():
            metadata[repo_name] = data.get(alias) or {}

    return metadata


def write_dashboard(repos, metadata_by_repo):
    with open("githubrepos.md", "w") as f:
        f.write(
            """
# Overzicht Github repos

Op dit dashboard zie je in een oogopslag alle openbare niet gearchiveerde Github repositories van Geonovum.

| Naam | Omschrijving | laatste wijziging | laatste gebruiker | zichtbaarheid | archief | heeft_pages | nview | releases | teams |
|------|--------------|-------------------|-------------------|---------------|---------|-------------|-------|----------|-------|
"""
        )

        for repo in repos:
            metadata = metadata_by_repo.get(repo["name"], {})
            pages = ""
            if repo.get("has_pages"):
                pages = "[pages](https://geonovum.github.io/{}/)".format(repo["name"])

            f.write(
                "| [{}]({}) | {} | {} | {} | {} | {} | {} | {} | {} | {} |\n".format(
                    table_text(repo["name"]),
                    repo["html_url"],
                    table_text(repo.get("description")),
                    repo["pushed_at"][:10],
                    latest_active_user(metadata),
                    "publiek",
                    "actief",
                    pages,
                    "",
                    release_tags(metadata),
                    "",
                )
            )


def write_respec_documents(documents):
    counts = Counter(document["label"] for document in documents)
    locations_by_label = defaultdict(Counter)
    for document in documents:
        locations_by_label[document["label"]][document["build_url"]] += 1

    with open("respecdocuments.md", "w") as f:
        f.write(
            """# Welke versie van respec zit in welk repo

Automatisch bijgewerkt op {}.

| respec versie | aantal | locatie |
| ------------- | ------ | ------- |
""".format(date.today().isoformat())
        )

        for label, count in counts.most_common():
            build_url = locations_by_label[label].most_common(1)[0][0]
            f.write("| {} | {} | {} |\n".format(table_text(label), count, table_text(build_url)))

        f.write(
            """
| file | respecversie |
| ---- | ------------ |
"""
        )

        for document in documents:
            f.write(
                "| {} | {} |\n".format(
                    table_text(document["location"]),
                    table_text(document["label"]),
                )
            )


repos = list_repositories()
metadata_by_repo = repository_metadata([repo["name"] for repo in repos])
write_dashboard(repos, metadata_by_repo)
write_respec_documents(respec_documents(repos))
