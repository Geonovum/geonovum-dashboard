import unittest
from datetime import date
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


if __name__ == "__main__":
    unittest.main()
