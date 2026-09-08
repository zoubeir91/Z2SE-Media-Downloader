import json
import tempfile
import unittest
from pathlib import Path

from v32_49_queue_core import (
    is_duplicate,
    load_queue,
    normalize_source_url,
    restore_jobs,
    sanitize_job,
    save_queue_atomic,
    source_identity,
)


class QueueCoreTests(unittest.TestCase):
    def test_normalize_strips_tracking_and_secrets(self):
        url = (
            "https://www.youtube.com/watch?v=abc123&utm_source=x&si=share"
            "&token=SECRET&list=PL1#frag"
        )
        normalized = normalize_source_url(url)
        self.assertIn("v=abc123", normalized)
        self.assertIn("list=PL1", normalized)
        self.assertNotIn("utm_source", normalized)
        self.assertNotIn("si=", normalized)
        self.assertNotIn("SECRET", normalized)
        self.assertNotIn("#frag", normalized)

    def test_identity_prefers_media_id(self):
        self.assertEqual(
            source_identity("https://example.com/a", "video-1"),
            source_identity("https://example.com/b", "video-1"),
        )

    def test_sanitize_drops_credentials_and_clamps_progress(self):
        safe = sanitize_job(
            {
                "url": "https://example.com/v?id=1&token=abc",
                "cookie": "SID=secret",
                "password": "secret",
                "authorization": "Bearer secret",
                "progress": 140,
                "attempts": -2,
            }
        )
        self.assertNotIn("cookie", safe)
        self.assertNotIn("password", safe)
        self.assertNotIn("authorization", safe)
        self.assertNotIn("token=abc", safe["url"])
        self.assertEqual(100.0, safe["progress"])
        self.assertEqual(0, safe["attempts"])

    def test_restore_running_job_as_pending(self):
        restored = restore_jobs([{"url": "https://example.com/v", "status": "running"}])
        self.assertEqual("pending", restored[0]["status"])
        self.assertEqual("Restored after app restart", restored[0]["error"])

    def test_atomic_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "queue.json"
            jobs = [
                {
                    "url": "https://youtu.be/abc?si=share",
                    "title": "Example",
                    "status": "pending",
                    "progress": 12.5,
                }
            ]
            save_queue_atomic(path, jobs)
            loaded = load_queue(path)
            self.assertEqual(1, len(loaded))
            self.assertEqual("Example", loaded[0]["title"])
            self.assertEqual(12.5, loaded[0]["progress"])
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(1, payload["schema"])

    def test_corrupt_queue_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "queue.json"
            path.write_text("{not-json", encoding="utf-8")
            self.assertEqual([], load_queue(path))

    def test_duplicate_detection(self):
        existing = [{"url": "https://www.youtube.com/watch?v=abc&si=x", "status": "done"}]
        candidate = {"url": "https://www.youtube.com/watch?si=y&v=abc"}
        self.assertTrue(is_duplicate(candidate, existing))
        candidate["force_download"] = True
        self.assertFalse(is_duplicate(candidate, existing))

    def test_failed_job_does_not_block_retry(self):
        existing = [{"url": "https://example.com/v", "status": "failed"}]
        self.assertFalse(is_duplicate({"url": "https://example.com/v"}, existing))


if __name__ == "__main__":
    unittest.main()
