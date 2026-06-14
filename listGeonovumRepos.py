#!/usr/bin/python3
#
# Genereert githubrepos.md met publieke, niet-gearchiveerde Geonovum repos.
#
import json
import subprocess
import urllib.parse

ORG = "Geonovum"


def github_json(path):
    output = subprocess.check_output(["gh", "api", path], text=True)
    return json.loads(output)


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


repos = list_repositories()
metadata_by_repo = repository_metadata([repo["name"] for repo in repos])
write_dashboard(repos, metadata_by_repo)
