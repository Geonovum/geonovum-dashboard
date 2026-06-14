#!/usr/bin/env python3
"""Generate the dashboard broken-links section from Muffet JSON output."""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TRANSIENT_MARKERS = (
    "429",
    "timeout",
    "timed out",
    "dialing",
    "connection reset",
    "connection refused",
    "temporary failure",
    "tls handshake timeout",
)


def escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def source_label(value: str) -> str:
    if "snapshot.html" in value and ("localhost" in value or "127.0.0.1" in value):
        return "dashboard snapshot"
    return value


def is_transient(error: str) -> bool:
    value = error.lower()
    return any(marker in value for marker in TRANSIENT_MARKERS)


def status_kind(error: str) -> str:
    if error.isdigit():
        code = int(error)
        if code in (404, 410):
            return "kapot"
        if code == 429:
            return "tijdelijk"
        if 500 <= code <= 599:
            return "serverfout"
        if code in (401, 403):
            return "afgeschermd"
        if 400 <= code <= 499:
            return "clientfout"
    if is_transient(error):
        return "tijdelijk"
    return "onbekend"


def flatten_results(data: Any) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if not isinstance(data, list):
        return rows

    for page in data:
        if not isinstance(page, dict):
            continue
        source = str(page.get("url") or "")
        links = page.get("links") or []
        if not isinstance(links, list):
            continue
        for link in links:
            if not isinstance(link, dict):
                continue
            url = str(link.get("url") or "")
            error = str(link.get("error") or "")
            if not url or not error:
                continue
            rows.append(
                {
                    "source": source_label(source),
                    "url": url,
                    "error": error,
                    "kind": status_kind(error),
                }
            )
    return rows


def read_results(path: Path) -> tuple[list[dict[str, str]], str | None]:
    if not path.exists() or path.stat().st_size == 0:
        return [], None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [], f"Muffet-output is geen geldige JSON: {exc}"

    return flatten_results(data), None


def write_markdown(rows: list[dict[str, str]], parse_error: str | None, target: Path) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    actual = [row for row in rows if row["kind"] in {"kapot", "clientfout", "serverfout"}]
    uncertain = [row for row in rows if row["kind"] not in {"kapot", "clientfout", "serverfout"}]
    counts = Counter(row["error"] for row in rows)

    lines: list[str] = [
        "# Broken links",
        "",
        f"Laatst bijgewerkt: {now}.",
        "",
    ]

    if parse_error:
        lines.extend(
            [
                '<span class="dashboard-badge dashboard-badge--danger">!</span> De linkcheck kon niet worden verwerkt.',
                "",
                parse_error,
                "",
            ]
        )
    else:
        lines.extend(
            [
                '<div class="dashboard-kpis">',
                f"<div><strong>{len(actual)}</strong><span>kapotte links</span></div>",
                f"<div><strong>{len(uncertain)}</strong><span>tijdelijke meldingen</span></div>",
                f"<div><strong>{len(rows)}</strong><span>meldingen totaal</span></div>",
                "</div>",
                "",
            ]
        )

    if not rows and not parse_error:
        lines.extend(
            [
                '<span class="dashboard-badge dashboard-badge--success">0</span> Geen kapotte links gevonden.',
                "",
            ]
        )
    else:
        lines.extend(["## Samenvatting per fout", ""])
        if counts:
            lines.extend(["| fout | aantal |", "| --- | ---: |"])
            for error, count in counts.most_common():
                lines.append(f"| {escape_md(error)} | {count} |")
        else:
            lines.append("Geen verwerkbare linkmeldingen gevonden.")
        lines.append("")

    lines.extend(["## Kapotte links", ""])
    if actual:
        lines.extend(["| fout | link | gevonden op |", "| --- | --- | --- |"])
        for row in actual:
            lines.append(
                f"| {escape_md(row['error'])} | [{escape_md(row['url'])}]({row['url']}) | {escape_md(row['source'])} |"
            )
    else:
        lines.append('<span class="dashboard-badge dashboard-badge--success">0</span> Geen kapotte links gevonden.')
    lines.append("")

    if uncertain:
        lines.extend(
            [
                "## Tijdelijke of onzekere meldingen",
                "",
                "Deze meldingen tellen niet mee als kapotte link. Het gaat bijvoorbeeld om rate limits, timeouts of afgeschermde pagina's.",
                "",
                "| fout | link |",
                "| --- | --- |",
            ]
        )
        for row in uncertain[:50]:
            lines.append(f"| {escape_md(row['error'])} | [{escape_md(row['url'])}]({row['url']}) |")
        if len(uncertain) > 50:
            lines.append(f"| ... | {len(uncertain) - 50} extra meldingen weggelaten uit het dashboard |")
        lines.append("")

    target.write_text("\n".join(lines), encoding="utf-8")


def write_text_summary(rows: list[dict[str, str]], parse_error: str | None, target: Path) -> None:
    actual = [row for row in rows if row["kind"] in {"kapot", "clientfout", "serverfout"}]
    uncertain = [row for row in rows if row["kind"] not in {"kapot", "clientfout", "serverfout"}]
    lines = [
        f"Kapotte links: {len(actual)}",
        f"Tijdelijke/onzekere meldingen: {len(uncertain)}",
        f"Meldingen totaal: {len(rows)}",
    ]
    if parse_error:
        lines.append(parse_error)
    for row in actual:
        lines.append(f"{row['error']}\t{row['url']}\t{row['source']}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: generateBrokenLinks.py <muffet-json> <brokenlinks-md> <summary-txt>", file=sys.stderr)
        return 2

    source = Path(sys.argv[1])
    markdown_target = Path(sys.argv[2])
    summary_target = Path(sys.argv[3])

    rows, parse_error = read_results(source)
    write_markdown(rows, parse_error, markdown_target)
    write_text_summary(rows, parse_error, summary_target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
