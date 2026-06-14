#!/usr/bin/python3
#
# Genereert githubrepos.md met publieke, niet-gearchiveerde Geonovum repos.
#
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
import base64
import json
import os
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request

ORG = "Geonovum"


def github_json(path):
    url = "https://api.github.com/{}".format(path)
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = "Bearer {}".format(token)

    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


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


def extract_respec_build_urls(html):
    build_urls = []

    for match in re.finditer(r"<script\b[^>]*\bsrc=[\"']([^\"']+)[\"']", html, re.IGNORECASE):
        candidate = match.group(1)
        lower_candidate = candidate.lower()

        if "respec" not in lower_candidate:
            continue
        if "respec-mermaid" in lower_candidate:
            continue
        if "/config/" in lower_candidate:
            continue
        if lower_candidate.endswith("config.js"):
            continue
        if lower_candidate.endswith(("easy-button.js", "leaflet.js", "rules.js")):
            continue

        build_urls.append(candidate)

    return build_urls


def respec_label(build_url):
    lower_url = build_url.lower()

    if "respec-geonovum" in lower_url:
        return "tools.geostandaarden"
    if "respec-nlgov" in lower_url:
        return "respec-nlgov"
    if "fixup.js" in lower_url:
        return "fixup"
    if "respec-logius" in lower_url:
        return "respec-logius"

    return build_url


def repository_tree(repo):
    branch = urllib.parse.quote(repo["default_branch"], safe="")
    path = "repos/{}/{}/git/trees/{}?recursive=1".format(
        urllib.parse.quote(ORG),
        urllib.parse.quote(repo["name"]),
        branch,
    )
    try:
        data = github_json(path)
    except urllib.error.HTTPError as error:
        if error.code in (404, 409):
            return []
        raise

    if data.get("truncated"):
        return []
    return data.get("tree", [])


def blob_text(repo, sha):
    path = "repos/{}/{}/git/blobs/{}".format(
        urllib.parse.quote(ORG),
        urllib.parse.quote(repo["name"]),
        urllib.parse.quote(sha, safe=""),
    )
    data = github_json(path)
    content = data.get("content", "")
    if data.get("encoding") != "base64" or not content:
        return ""
    return base64.b64decode(content).decode("utf-8", errors="replace")


def index_blobs_for_repo(repo):
    blobs = []
    for item in repository_tree(repo):
        path = item.get("path", "")
        if item.get("type") != "blob" or path.rsplit("/", 1)[-1] != "index.html":
            continue

        blobs.append((repo, path, item["sha"]))

    return blobs


def respec_documents_for_blob(index_blob):
    repo, path, sha = index_blob
    documents = []

    html = blob_text(repo, sha)
    for build_url in extract_respec_build_urls(html):
        documents.append(
            {
                "location": github_file_location(repo, path),
                "build_url": build_url,
                "label": respec_label(build_url),
            }
        )

    return documents


def respec_documents(repos):
    documents = []
    seen = set()

    def append_document(document):
        key = (document["location"], document["label"])
        if key in seen:
            return
        seen.add(key)
        documents.append(document)

    index_blobs = []
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = [executor.submit(index_blobs_for_repo, repo) for repo in repos]
        for future in as_completed(futures):
            index_blobs.extend(future.result())

    print("Gevonden {} index.html-bestanden voor ReSpec-scan.".format(len(index_blobs)))

    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(respec_documents_for_blob, index_blob) for index_blob in index_blobs]
        for future in as_completed(futures):
            for document in future.result():
                append_document(document)

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
