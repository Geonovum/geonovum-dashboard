import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import listGeonovumRepos as dashboard


class MeaningfulActivityTest(unittest.TestCase):
    def test_latest_counted_commit_skips_pasibun_and_github_actions(self):
        metadata = {
            "defaultBranchRef": {
                "target": {
                    "history": {
                        "nodes": [
                            {
                                "committedDate": "2026-05-18T19:15:33Z",
                                "author": {
                                    "name": "github-actions[bot]",
                                    "user": {"login": "github-actions[bot]", "url": "https://github.com/apps/github-actions"},
                                },
                            },
                            {
                                "committedDate": "2026-02-09T12:38:43Z",
                                "author": {
                                    "name": "pasibun",
                                    "user": {"login": "pasibun", "url": "https://github.com/pasibun"},
                                },
                            },
                            {
                                "committedDate": "2021-03-08T15:14:41Z",
                                "author": {
                                    "name": "Linda van den Brink",
                                    "user": {"login": "lvdbrink", "url": "https://github.com/lvdbrink"},
                                },
                            },
                        ]
                    }
                }
            }
        }

        commit = dashboard.latest_counted_commit(metadata)

        self.assertEqual(commit["date"], date(2021, 3, 8))
        self.assertEqual(commit["author_login"], "lvdbrink")

    def test_repo_activity_days_uses_latest_counted_commit_instead_of_pushed_at(self):
        repo = {"pushed_at": "2026-05-18T19:15:33Z"}
        metadata = {
            "defaultBranchRef": {
                "target": {
                    "history": {
                        "nodes": [
                            {
                                "committedDate": "2026-05-18T19:15:33Z",
                                "author": {"name": "github-actions[bot]", "user": {"login": "github-actions[bot]"}},
                            },
                            {
                                "committedDate": "2021-03-08T15:14:41Z",
                                "author": {"name": "Linda van den Brink", "user": {"login": "lvdbrink"}},
                            },
                        ]
                    }
                }
            }
        }

        with patch.object(dashboard, "TODAY", date(2026, 7, 6)):
            self.assertEqual(dashboard.repo_activity_days(repo, metadata), 1946)

    def test_dashboard_summary_does_not_include_archive_candidates_section(self):
        repo = {
            "full_name": "Geonovum/example",
            "name": "example",
            "html_url": "https://github.com/Geonovum/example",
            "pushed_at": "2026-01-01T00:00:00Z",
            "has_pages": False,
            "owner": {"login": "Geonovum"},
        }

        with TemporaryDirectory() as tmpdir, patch.object(dashboard, "TODAY", date(2026, 7, 6)):
            cwd = Path.cwd()
            try:
                import os

                os.chdir(tmpdir)
                dashboard.write_dashboard_summary([repo], {repo["full_name"]: {}}, {repo["full_name"]: {}}, [])
                summary = Path("dashboardoverzicht.md").read_text()
            finally:
                os.chdir(cwd)

        self.assertNotIn("Archiefkandidaten", summary)
        self.assertNotIn("Repos die langer dan twee jaar niet zijn gewijzigd", summary)

    def test_repo_teams_text_links_github_teams(self):
        teams = [
            {
                "name": "RO beheerteam",
                "html_url": "https://github.com/orgs/Geonovum/teams/ro-beheerteam",
            },
            {
                "name": "technisch register",
                "html_url": "https://github.com/orgs/Geonovum/teams/technisch-register",
            },
        ]

        self.assertEqual(
            dashboard.repo_teams_text(teams),
            "[RO beheerteam](https://github.com/orgs/Geonovum/teams/ro-beheerteam), [technisch register](https://github.com/orgs/Geonovum/teams/technisch-register)",
        )

    def test_dashboard_includes_github_teams_column(self):
        repo = {
            "full_name": "Geonovum/imro",
            "name": "imro",
            "html_url": "https://github.com/Geonovum/imro",
            "pushed_at": "2026-01-01T00:00:00Z",
            "has_pages": False,
            "owner": {"login": "Geonovum"},
        }
        teams_by_repo = {
            repo["full_name"]: [
                {
                    "name": "ro-beheerteam",
                    "html_url": "https://github.com/orgs/Geonovum/teams/ro-beheerteam",
                }
            ]
        }

        with TemporaryDirectory() as tmpdir, patch.object(dashboard, "TODAY", date(2026, 7, 6)):
            cwd = Path.cwd()
            try:
                import os

                os.chdir(tmpdir)
                dashboard.write_dashboard([repo], {repo["full_name"]: {}}, {repo["full_name"]: {}}, teams_by_repo)
                overview = Path("githubrepos.md").read_text()
            finally:
                os.chdir(cwd)

        self.assertIn("| Organisatie | repo | GitHub teams | gezondheid |", overview)
        self.assertIn("[ro-beheerteam](https://github.com/orgs/Geonovum/teams/ro-beheerteam)", overview)

    def test_dashboard_summary_includes_github_team_distribution(self):
        repos = [
            {
                "full_name": "Geonovum/imro",
                "name": "imro",
                "html_url": "https://github.com/Geonovum/imro",
                "pushed_at": "2026-01-01T00:00:00Z",
                "has_pages": False,
                "owner": {"login": "Geonovum"},
            },
            {
                "full_name": "Geonovum/zonder-team",
                "name": "zonder-team",
                "html_url": "https://github.com/Geonovum/zonder-team",
                "pushed_at": "2026-01-01T00:00:00Z",
                "has_pages": False,
                "owner": {"login": "Geonovum"},
            },
        ]
        teams_by_repo = {
            "Geonovum/imro": [
                {
                    "name": "ro-beheerteam",
                    "html_url": "https://github.com/orgs/Geonovum/teams/ro-beheerteam",
                }
            ],
            "Geonovum/zonder-team": [],
        }

        with TemporaryDirectory() as tmpdir, patch.object(dashboard, "TODAY", date(2026, 7, 6)):
            cwd = Path.cwd()
            try:
                import os

                os.chdir(tmpdir)
                dashboard.write_dashboard_summary(
                    repos,
                    {repo["full_name"]: {} for repo in repos},
                    {repo["full_name"]: {} for repo in repos},
                    [],
                    teams_by_repo,
                )
                summary = Path("dashboardoverzicht.md").read_text()
            finally:
                os.chdir(cwd)

        self.assertIn("| GitHub team | repos |", summary)
        self.assertIn("| [ro-beheerteam](https://github.com/orgs/Geonovum/teams/ro-beheerteam) | 1 |", summary)
        self.assertIn("| zonder GitHub team | 1 |", summary)


if __name__ == "__main__":
    unittest.main()
