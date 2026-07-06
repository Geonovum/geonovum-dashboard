#!/usr/bin/python3
#
# Genereert githubrepos.md met publieke, niet-gearchiveerde repos.
#
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
import json
import os
import re
import socket
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

ORGS = ["Geonovum", "BROprogramma"]
TREE_CACHE = {}
TODAY = date.today()
CHECK_DIR = os.environ.get("CHECK_DIR", ".checks")
IGNORED_ACTIVITY_LOGINS = {"pasibun", "github-actions[bot]", "github-action[bot]"}
GRAPHQL_REPO_BATCH_SIZE = 10


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
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            if error.code in (403, 429) and attempt < 4:
                retry_after = error.headers.get("Retry-After")
                wait_seconds = int(retry_after) if retry_after and retry_after.isdigit() else 8 * (attempt + 1)
                time.sleep(wait_seconds)
                continue
            raise
        except (TimeoutError, socket.timeout, urllib.error.URLError):
            if attempt == 4:
                raise
            time.sleep(2 * (attempt + 1))


def http_text(url):
    request = urllib.request.Request(url, headers={"User-Agent": "geonovum-dashboard"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return ""
            if error.code in (403, 429) and attempt < 4:
                retry_after = error.headers.get("Retry-After")
                wait_seconds = int(retry_after) if retry_after and retry_after.isdigit() else 8 * (attempt + 1)
                time.sleep(wait_seconds)
                continue
            raise
        except (TimeoutError, socket.timeout, urllib.error.URLError):
            if attempt == 4:
                raise
            time.sleep(2 * (attempt + 1))

    return ""


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


def percentage(part, total):
    if not total:
        return "0%"
    return "{:.0f}%".format((part / total) * 100)


def ratio(part, total):
    return "{} / {} ({})".format(part, total, percentage(part, total))


def badge(text, kind):
    return '<span class="dashboard-badge dashboard-badge--{}">{}</span>'.format(kind, table_text(text))


def markdown_link(text, url):
    if not url:
        return table_text(text)
    return "[{}]({})".format(table_text(text), table_text(url))


def parse_github_date(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def days_since(value):
    parsed = parse_github_date(value)
    if not parsed:
        return ""
    return (TODAY - parsed).days


def days_since_date(value):
    if not value:
        return ""
    return (TODAY - value).days


def commit_history(metadata):
    default_branch = metadata.get("defaultBranchRef") or {}
    target = default_branch.get("target") or {}
    return (target.get("history") or {}).get("nodes", [])


def commit_author_login(commit):
    author = commit.get("author") or {}
    user = author.get("user")
    if user and user.get("login"):
        return user["login"]
    return author.get("name", "")


def is_ignored_activity_login(login):
    if not login:
        return False
    return login.lower() in IGNORED_ACTIVITY_LOGINS


def latest_counted_commit(metadata):
    for commit in commit_history(metadata):
        author_login = commit_author_login(commit)
        if is_ignored_activity_login(author_login):
            continue

        committed_date = parse_github_date(commit.get("committedDate"))
        if not committed_date:
            continue

        return {
            "date": committed_date,
            "author_login": author_login,
        }

    return None


def repo_activity_date(repo, metadata):
    counted_commit = latest_counted_commit(metadata)
    if counted_commit:
        return counted_commit["date"]
    return parse_github_date(repo.get("pushed_at"))


def repo_activity_days(repo, metadata):
    return days_since_date(repo_activity_date(repo, metadata))


def repo_activity_date_text(repo, metadata):
    activity_date = repo_activity_date(repo, metadata)
    return activity_date.isoformat() if activity_date else ""


def repo_health(repo, metadata=None):
    age = repo_activity_days(repo, metadata or {})
    if age == "":
        return badge("onbekend", "neutral")
    if age > 730:
        return badge("slapend", "danger")
    if age > 365:
        return badge("stil", "warning")
    if age > 180:
        return badge("rustig", "attention")
    return badge("actief", "success")


def yes_no(value):
    return badge("ja", "success") if value else badge("nee", "neutral")


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


def markdown_actor(actor):
    if actor and actor.get("login"):
        return markdown_link(actor["login"], actor.get("url"))
    return ""


def latest_active_user(metadata):
    fallback = ""

    for commit in commit_history(metadata):
        author = commit.get("author") or {}
        user = author.get("user")
        formatted_user = markdown_user(user, author.get("name", ""))

        if formatted_user and user and not is_bot_login(user.get("login")) and not is_ignored_activity_login(user.get("login")):
            return formatted_user

        if formatted_user and not user and not is_bot_login(formatted_user) and not is_ignored_activity_login(formatted_user) and not fallback:
            fallback = formatted_user

    return fallback


def latest_activity_contact(metadata):
    commit_user = latest_active_user(metadata)
    if commit_user:
        return commit_user, "commit"

    pull_requests = metadata.get("pullRequests", {}).get("nodes", [])
    if pull_requests:
        actor = markdown_actor((pull_requests[0] or {}).get("author"))
        if actor:
            return actor, "PR"

    issues = metadata.get("issues", {}).get("nodes", [])
    if issues:
        actor = markdown_actor((issues[0] or {}).get("author"))
        if actor:
            return actor, "issue"

    return "", ""


def release_tags(metadata):
    releases = metadata.get("releases", {})
    nodes = releases.get("nodes", [])
    tags = [table_text(release.get("tagName", "")) for release in nodes if release.get("tagName")]

    if releases.get("totalCount", 0) > len(tags):
        tags.append("...")

    return " ".join(tags)


def latest_release_date(metadata):
    releases = metadata.get("releases", {}).get("nodes", [])
    if not releases:
        return ""
    release = releases[0]
    released_at = release.get("publishedAt") or release.get("createdAt")
    if not released_at:
        return ""
    return released_at[:10]


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
    if repo["full_name"] in TREE_CACHE:
        return TREE_CACHE[repo["full_name"]]

    branch = urllib.parse.quote(repo["default_branch"], safe="")
    path = "repos/{}/{}/git/trees/{}?recursive=1".format(
        urllib.parse.quote(repo["owner"]["login"]),
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
        TREE_CACHE[repo["full_name"]] = []
        return []

    TREE_CACHE[repo["full_name"]] = data.get("tree", [])
    return TREE_CACHE[repo["full_name"]]


def repo_file_flags(repo):
    paths = [item.get("path", "") for item in repository_tree(repo) if item.get("type") == "blob"]
    lower_paths = {path.lower() for path in paths}
    basenames = {path.rsplit("/", 1)[-1].lower() for path in paths}

    workflow_count = sum(
        1
        for path in lower_paths
        if path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml"))
    )

    flags = {
        "readme": any(name.startswith("readme") for name in basenames),
        "license": bool(repo.get("license")) or any(name.startswith(("license", "copying")) for name in basenames),
        "contributing": "contributing.md" in basenames or ".github/contributing.md" in lower_paths,
        "security": "security.md" in basenames or ".github/security.md" in lower_paths,
        "publiccode": "publiccode.yml" in basenames or "publiccode.yaml" in basenames,
        "dependabot": ".github/dependabot.yml" in lower_paths or ".github/dependabot.yaml" in lower_paths,
        "codeowners": (
            "codeowners" in basenames
            or ".github/codeowners" in lower_paths
            or "docs/codeowners" in lower_paths
        ),
        "workflow_count": workflow_count,
    }
    flags["score"] = sum(
        1
        for key in ("readme", "license", "contributing", "security", "publiccode", "dependabot", "codeowners")
        if flags[key]
    )
    return flags


def repository_file_flags(repos):
    flags_by_repo = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(repo_file_flags, repo): repo["full_name"] for repo in repos}
        for future in as_completed(futures):
            flags_by_repo[futures[future]] = future.result()
    return flags_by_repo


def management_files_text(flags):
    missing = [
        label
        for key, label in (
            ("readme", "README"),
            ("license", "LICENSE"),
            ("contributing", "CONTRIBUTING"),
            ("security", "SECURITY"),
            ("publiccode", "publiccode"),
            ("dependabot", "dependabot"),
            ("codeowners", "CODEOWNERS"),
        )
        if not flags.get(key)
    ]
    if not missing:
        return badge("7/7", "success")
    if len(missing) <= 2:
        return "{} mist {}".format(badge("{}/7".format(flags.get("score", 0)), "attention"), ", ".join(missing))
    return "{} mist {}".format(badge("{}/7".format(flags.get("score", 0)), "warning"), ", ".join(missing[:3]) + " ...")


def raw_file_text(repo, path):
    raw_url = "https://raw.githubusercontent.com/{}/{}/{}/{}".format(
        urllib.parse.quote(repo["owner"]["login"]),
        urllib.parse.quote(repo["name"]),
        urllib.parse.quote(repo["default_branch"], safe=""),
        urllib.parse.quote(path, safe="/"),
    )
    return http_text(raw_url)


def index_blobs_for_repo(repo):
    blobs = []
    for item in repository_tree(repo):
        path = item.get("path", "")
        if item.get("type") != "blob" or path.rsplit("/", 1)[-1] != "index.html":
            continue

        blobs.append((repo, path))

    return blobs


def respec_documents_for_blob(index_blob):
    repo, path = index_blob
    documents = []

    html = raw_file_text(repo, path)
    for build_url in extract_respec_build_urls(html):
        documents.append(
            {
                "organization": repo["owner"]["login"],
                "repository": repo["name"],
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

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(respec_documents_for_blob, index_blob) for index_blob in index_blobs]
        for future in as_completed(futures):
            for document in future.result():
                append_document(document)

    return sorted(documents, key=lambda document: document["location"].lower())


def batched(items, size):
    for index in range(0, len(items), size):
        yield items[index : index + size]


def list_org_repositories(org):
    repos = []
    page = 1

    while True:
        params = urllib.parse.urlencode({"per_page": 100, "page": page, "type": "public"})
        batch = github_json("orgs/{}/repos?{}".format(urllib.parse.quote(org), params))

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


def list_repositories():
    repos = []
    for org in ORGS:
        repos.extend(list_org_repositories(org))
    return repos


def repository_metadata(repos):
    metadata = {}
    repos_by_owner = defaultdict(list)
    for repo in repos:
        repos_by_owner[repo["owner"]["login"]].append(repo)

    for owner, owner_repos in repos_by_owner.items():
        for batch in batched(owner_repos, GRAPHQL_REPO_BATCH_SIZE):
            fields = []
            alias_to_full_name = {}

            for index, repo in enumerate(batch):
                alias = "repo{}".format(index)
                alias_to_full_name[alias] = repo["full_name"]
                fields.append(
                    """
                    {alias}: repository(owner: $owner, name: {repo_name}) {{
                      defaultBranchRef {{
                        target {{
                          ... on Commit {{
                            history(first: 100) {{
                              nodes {{
                                committedDate
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
                      issues(first: 1, states: OPEN, orderBy: {{field: UPDATED_AT, direction: DESC}}) {{
                        totalCount
                        nodes {{
                          updatedAt
                          author {{
                            login
                            url
                          }}
                        }}
                      }}
                      pullRequests(first: 1, states: OPEN, orderBy: {{field: UPDATED_AT, direction: DESC}}) {{
                        totalCount
                        nodes {{
                          updatedAt
                          author {{
                            login
                            url
                          }}
                        }}
                      }}
                      releases(first: 10, orderBy: {{field: CREATED_AT, direction: DESC}}) {{
                        totalCount
                        nodes {{
                          tagName
                          publishedAt
                          createdAt
                        }}
                      }}
                    }}
                    """.format(
                        alias=alias,
                        repo_name=json.dumps(repo["name"]),
                    )
                )

            query = "query($owner: String!) {{ {} }}".format("\n".join(fields))
            data = github_graphql(query, {"owner": owner})

            for alias, full_name in alias_to_full_name.items():
                metadata[full_name] = data.get(alias) or {}

    return metadata


def repo_pages_link(repo):
    url = repo_pages_url(repo)
    if not url:
        return ""
    return "[pages]({})".format(url)


def repo_pages_url(repo):
    if not repo.get("has_pages"):
        return ""

    owner = repo["owner"]["login"].lower()
    name = repo["name"]
    if name.lower() == "{}.github.io".format(owner):
        return "https://{}.github.io/".format(owner)

    return "https://{}.github.io/{}/".format(
        repo["owner"]["login"].lower(),
        repo["name"],
    )


def write_pages_urls(repos):
    path = os.path.join(CHECK_DIR, "pages-urls.txt")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    urls = sorted({url for repo in repos for url in [repo_pages_url(repo)] if url})
    with open(path, "w") as f:
        for url in urls:
            f.write("{}\n".format(url))


def repo_open_work(metadata):
    issues = (metadata.get("issues") or {}).get("totalCount", 0)
    pull_requests = (metadata.get("pullRequests") or {}).get("totalCount", 0)
    return issues, pull_requests


def repo_action_score(repo, metadata, flags):
    age = repo_activity_days(repo, metadata)
    issues, pull_requests = repo_open_work(metadata)
    missing_score = 7 - flags.get("score", 0)
    stale_score = age if isinstance(age, int) else 0
    return stale_score + issues * 15 + pull_requests * 30 + missing_score * 20


def repo_contact_text(metadata):
    contact, source = latest_activity_contact(metadata)
    return "{} ({})".format(contact, source) if contact and source else contact


def repo_missing_score(flags):
    return 7 - flags.get("score", 0)


def repo_link(repo):
    return "[{}]({})".format(table_text(repo["name"]), repo["html_url"])


def write_dashboard_summary(repos, metadata_by_repo, flags_by_repo, documents):
    repos_by_org = Counter(repo["owner"]["login"] for repo in repos)
    stale_repos = [
        repo
        for repo in repos
        if isinstance(repo_activity_days(repo, metadata_by_repo.get(repo["full_name"], {})), int)
        and repo_activity_days(repo, metadata_by_repo.get(repo["full_name"], {})) > 365
    ]
    sleeping_repos = [
        repo
        for repo in repos
        if isinstance(repo_activity_days(repo, metadata_by_repo.get(repo["full_name"], {})), int)
        and repo_activity_days(repo, metadata_by_repo.get(repo["full_name"], {})) > 730
    ]
    pages_repos = [repo for repo in repos if repo.get("has_pages")]
    workflow_repos = [repo for repo in repos if flags_by_repo.get(repo["full_name"], {}).get("workflow_count", 0) > 0]
    open_issues = 0
    open_prs = 0
    for repo in repos:
        issues, pull_requests = repo_open_work(metadata_by_repo.get(repo["full_name"], {}))
        open_issues += issues
        open_prs += pull_requests

    missing_security = [repo for repo in repos if not flags_by_repo.get(repo["full_name"], {}).get("security")]
    missing_publiccode = [repo for repo in repos if not flags_by_repo.get(repo["full_name"], {}).get("publiccode")]
    old_respec_documents = [
        document
        for document in documents
        if document["label"] not in ("tools.geostandaarden",)
    ]
    open_work_repos = sorted(
        [
            repo
            for repo in repos
            if sum(repo_open_work(metadata_by_repo.get(repo["full_name"], {}))) > 0
        ],
        key=lambda repo: (
            repo_open_work(metadata_by_repo.get(repo["full_name"], {}))[1],
            repo_open_work(metadata_by_repo.get(repo["full_name"], {}))[0],
        ),
        reverse=True,
    )[:12]
    active_missing_management = sorted(
        [
            repo
            for repo in repos
            if isinstance(repo_activity_days(repo, metadata_by_repo.get(repo["full_name"], {})), int)
            and repo_activity_days(repo, metadata_by_repo.get(repo["full_name"], {})) <= 365
            and repo_missing_score(flags_by_repo.get(repo["full_name"], {})) > 0
        ],
        key=lambda repo: (
            repo_missing_score(flags_by_repo.get(repo["full_name"], {})),
            sum(repo_open_work(metadata_by_repo.get(repo["full_name"], {}))),
            -repo_activity_days(repo, metadata_by_repo.get(repo["full_name"], {})),
        ),
        reverse=True,
    )[:12]
    old_respec_by_repo = defaultdict(lambda: {"count": 0, "labels": Counter(), "org": "", "repo": "", "url": ""})
    for document in old_respec_documents:
        key = (document["organization"], document["repository"])
        old_respec_by_repo[key]["org"] = document["organization"]
        old_respec_by_repo[key]["repo"] = document["repository"]
        old_respec_by_repo[key]["url"] = "https://github.com/{}/{}".format(document["organization"], document["repository"])
        old_respec_by_repo[key]["count"] += 1
        old_respec_by_repo[key]["labels"][document["label"]] += 1
    respec_attention = sorted(old_respec_by_repo.values(), key=lambda item: item["count"], reverse=True)[:12]

    with open("dashboardoverzicht.md", "w") as f:
        f.write(
            """# Dashboard overzicht

Automatisch bijgewerkt op {}.

<div class="dashboard-kpis">
<div><strong>{}</strong><span>repos</span></div>
<div><strong>{}</strong><span>ReSpec documenten</span></div>
<div><strong>{}</strong><span>open issues</span></div>
<div><strong>{}</strong><span>open PR's</span></div>
<div><strong>{}</strong><span>Pages repos</span></div>
<div><strong>{}</strong><span>met workflow</span></div>
</div>

| Organisatie | repos |
| ----------- | ----- |
""".format(
                TODAY.isoformat(),
                len(repos),
                len(documents),
                open_issues,
                open_prs,
                ratio(len(pages_repos), len(repos)),
                ratio(len(workflow_repos), len(repos)),
            )
        )

        for org, count in repos_by_org.most_common():
            f.write("| {} | {} |\n".format(table_text(org), count))

        f.write(
            """
| Indicator | aantal | aandeel |
| --------- | ------ | ------- |
| Repos stiler dan 1 jaar | {} | {} |
| Repos stiler dan 2 jaar | {} | {} |
| Repos zonder SECURITY.md | {} | {} |
| Repos zonder publiccode.yml | {} | {} |
| ReSpec documenten met migratie-aandacht | {} | {} |

## Actielijsten

**Open werk**

Repos met de meeste open pull requests en issues.

| Organisatie | repo | gezondheid | laatste wijziging | contact | open issues | open PR's |
| ----------- | ---- | ---------- | ----------------- | ------- | ----------- | --------- |
""".format(
                len(stale_repos),
                percentage(len(stale_repos), len(repos)),
                len(sleeping_repos),
                percentage(len(sleeping_repos), len(repos)),
                len(missing_security),
                percentage(len(missing_security), len(repos)),
                len(missing_publiccode),
                percentage(len(missing_publiccode), len(repos)),
                len(old_respec_documents),
                percentage(len(old_respec_documents), len(documents)),
            )
        )

        for repo in open_work_repos:
            metadata = metadata_by_repo.get(repo["full_name"], {})
            issues, pull_requests = repo_open_work(metadata)
            f.write(
                "| {} | {} | {} | {} | {} | {} | {} |\n".format(
                    table_text(repo["owner"]["login"]),
                    repo_link(repo),
                    repo_health(repo, metadata),
                    table_text(repo_activity_date_text(repo, metadata)),
                    repo_contact_text(metadata),
                    issues,
                    pull_requests,
                )
            )

        f.write(
            """
**Actieve repos met ontbrekende beheerbestanden**

Repos die afgelopen jaar zijn bijgewerkt, maar nog beheerbestanden missen.

| Organisatie | repo | laatste wijziging | contact | beheerbestanden |
| ----------- | ---- | ----------------- | ------- | --------------- |
"""
        )
        for repo in active_missing_management:
            metadata = metadata_by_repo.get(repo["full_name"], {})
            flags = flags_by_repo.get(repo["full_name"], {})
            f.write(
                "| {} | {} | {} | {} | {} |\n".format(
                    table_text(repo["owner"]["login"]),
                    repo_link(repo),
                    table_text(repo_activity_date_text(repo, metadata)),
                    repo_contact_text(metadata),
                    management_files_text(flags),
                )
            )

        f.write(
            """
**ReSpec migratie-aandacht**

Repos met ReSpec-documenten die niet op `tools.geostandaarden` staan.

| Organisatie | repo | documenten | gevonden ReSpec-versies |
| ----------- | ---- | ---------- | ----------------------- |
"""
        )
        for item in respec_attention:
            labels = ", ".join(label for label, _ in item["labels"].most_common(4))
            if len(item["labels"]) > 4:
                labels += ", ..."
            f.write(
                "| {} | [{}]({}) | {} | {} |\n".format(
                    table_text(item["org"]),
                    table_text(item["repo"]),
                    item["url"],
                    item["count"],
                    table_text(labels),
                )
            )


def write_dashboard(repos, metadata_by_repo, flags_by_repo):
    with open("githubrepos.md", "w") as f:
        f.write(
            """
# Overzicht GitHub repos

Op dit dashboard zie je in een oogopslag alle openbare niet-gearchiveerde GitHub repositories van Geonovum en BROprogramma.

De tabellen zijn opgesplitst, zodat beheer, publicatie en releases apart te scannen zijn.

## Repo beheer

| Organisatie | repo | gezondheid | laatste wijziging | dagen stil | contact | open issues | open PR's | beheerbestanden |
| ----------- | ---- | ---------- | ----------------- | ---------- | ------- | ----------- | --------- | --------------- |
"""
        )

        for repo in repos:
            metadata = metadata_by_repo.get(repo["full_name"], {})
            flags = flags_by_repo.get(repo["full_name"], {})
            issues, pull_requests = repo_open_work(metadata)

            f.write(
                "| {} | {} | {} | {} | {} | {} | {} | {} | {} |\n".format(
                    table_text(repo["owner"]["login"]),
                    repo_link(repo),
                    repo_health(repo, metadata),
                    table_text(repo_activity_date_text(repo, metadata)),
                    repo_activity_days(repo, metadata),
                    repo_contact_text(metadata),
                    issues,
                    pull_requests,
                    management_files_text(flags),
                )
            )

        f.write(
            """
## Publicatie en workflows

| Organisatie | repo | Pages | workflows | laatste wijziging |
| ----------- | ---- | ----- | --------- | ----------------- |
"""
        )
        for repo in repos:
            flags = flags_by_repo.get(repo["full_name"], {})
            f.write(
                "| {} | {} | {} | {} | {} |\n".format(
                    table_text(repo["owner"]["login"]),
                    repo_link(repo),
                    repo_pages_link(repo),
                    flags.get("workflow_count", 0),
                    table_text(repo_activity_date_text(repo, metadata_by_repo.get(repo["full_name"], {}))),
                )
            )

        release_repos = [
            repo
            for repo in repos
            if latest_release_date(metadata_by_repo.get(repo["full_name"], {}))
            or release_tags(metadata_by_repo.get(repo["full_name"], {}))
        ]
        f.write(
            """
## Releases

| Organisatie | repo | laatste release | releases |
| ----------- | ---- | --------------- | -------- |
"""
        )
        for repo in release_repos:
            metadata = metadata_by_repo.get(repo["full_name"], {})
            f.write(
                "| {} | {} | {} | {} |\n".format(
                    table_text(repo["owner"]["login"]),
                    repo_link(repo),
                    latest_release_date(metadata),
                    release_tags(metadata),
                )
            )

        f.write(
            """
## Beschrijvingen

| Organisatie | repo | omschrijving |
| ----------- | ---- | ------------ |
"""
        )
        for repo in repos:
            f.write(
                "| {} | {} | {} |\n".format(
                    table_text(repo["owner"]["login"]),
                    repo_link(repo),
                    table_text(repo.get("description")),
                )
            )


def write_respec_documents(documents):
    counts = Counter(document["label"] for document in documents)
    counts_by_org = Counter(document["location"].split("/")[3] for document in documents if document["location"].startswith("https://github.com/"))
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
| organisatie | aantal documenten |
| ----------- | ----------------- |
"""
        )
        for org, count in counts_by_org.most_common():
            f.write("| {} | {} |\n".format(table_text(org), count))

        f.write(
            """
| organisatie | repo | file | respecversie |
| ----------- | ---- | ---- | ------------ |
"""
        )

        for document in documents:
            f.write(
                "| {} | {} | {} | {} |\n".format(
                    table_text(document["organization"]),
                    table_text(document["repository"]),
                    table_text(document["location"]),
                    table_text(document["label"]),
                )
            )


def main():
    repos = list_repositories()
    metadata_by_repo = repository_metadata(repos)
    flags_by_repo = repository_file_flags(repos)
    documents = respec_documents(repos)
    write_dashboard_summary(repos, metadata_by_repo, flags_by_repo, documents)
    write_dashboard(repos, metadata_by_repo, flags_by_repo)
    write_respec_documents(documents)
    write_pages_urls(repos)


if __name__ == "__main__":
    main()
