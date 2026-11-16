"""Integration tests for FastAPI server portability, SQLite schema, and Validation Plan 02 endpoints."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from chaucer_canterbury import server


class TestServerPortabilityAndValidationEndpoints(unittest.TestCase):
    def test_repo_relative_default_paths(self) -> None:
        self.assertNotIn("chaucer-canterbury-app", str(server.DEFAULT_DB_PATH))
        self.assertNotIn("chaucer-canterbury-app", str(server.DEFAULT_STATIC_DIR))
        self.assertTrue(str(server.DEFAULT_DB_PATH).endswith(".local/studio.db"))
        self.assertTrue(str(server.DEFAULT_STATIC_DIR).endswith("webapp/dist/public"))

    def test_additive_sqlite_schema_and_validation_endpoints(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_studio.db"
            test_app = server.create_app(db_path=db_path)
            client = TestClient(test_app)

            # Verify all 5 SQLite tables exist cleanly
            with sqlite3.connect(str(db_path)) as conn:
                tables = {
                    row[0]
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                }
            self.assertEqual(
                tables,
                {
                    "author_config",
                    "world_state",
                    "turns",
                    "counterfactual_runs",
                    "blind_scansion_runs",
                },
            )

            health = client.get("/api/health")
            self.assertEqual(health.status_code, 200)
            self.assertEqual(health.json()["status"], "ok")

            overview = client.get("/api/overview")
            self.assertEqual(overview.status_code, 200)
            ov_data = overview.json()
            self.assertIn("blind_scansion", ov_data)
            self.assertIsNotNone(ov_data["blind_scansion"]["baseline"])
            self.assertIsNotNone(ov_data["blind_scansion"]["current"])
            self.assertTrue(ov_data["blind_scansion"]["current"]["all_thresholds_passed"])

            blind_res = client.get("/api/validation/blind-scansion")
            self.assertEqual(blind_res.status_code, 200)
            b_json = blind_res.json()
            self.assertEqual(b_json["baseline"]["engine_version"], "v0.1-baseline")
            self.assertEqual(b_json["current"]["engine_version"], "v0.2")
            self.assertGreaterEqual(len(b_json["runs"]), 2)

            rerun_h3 = client.post(
                "/api/validation/blind-scansion/run", json={"target_set": "H3"}
            )
            self.assertEqual(rerun_h3.status_code, 200)
            r_json = rerun_h3.json()
            self.assertEqual(r_json["latest_run"]["evaluated_sets"], ["H3"])
            self.assertEqual(
                r_json["latest_run"]["set_summaries"][0]["line_recall"], 1.0
            )

            scan_tail = client.post(
                "/api/scan",
                json={
                    "text": "\n".join(
                        [
                            "Listeth, lordes, in good entent,",
                            "And I wol telle verrayment",
                            "Of mirthe and of solas;",
                            "Al of a knyght was fair and gent",
                            "In bataille and in tourneyment,",
                            "His name was sir Thopas.",
                        ]
                    ),
                    "rhyme_scheme": "AABCCB",
                },
            )
            self.assertEqual(scan_tail.status_code, 200)
            st_audit = scan_tail.json()["stanza_audit"]
            self.assertIsNotNone(st_audit)
            self.assertTrue(st_audit["is_valid"])


if __name__ == "__main__":
    unittest.main()
