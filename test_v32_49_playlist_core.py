import unittest

from v32_49_playlist_core import (
    apply_search,
    chunk_entries,
    estimate_selected_duration,
    normalize_playlist_entries,
    select_range,
    selected_entries,
)


class PlaylistCoreTests(unittest.TestCase):
    def test_normalize_entries(self):
        rows = normalize_playlist_entries([
            {"id": "b", "title": "Second", "playlist_index": 2, "duration": "20"},
            {"id": "a", "title": "First", "playlist_index": 1, "duration": 10},
        ])
        self.assertEqual([1, 2], [row["index"] for row in rows])
        self.assertEqual(10.0, rows[0]["duration"])
        self.assertTrue(rows[0]["selected"])

    def test_select_range_swaps_reversed_edges(self):
        rows = normalize_playlist_entries([
            {"id": str(i), "title": f"Item {i}", "playlist_index": i}
            for i in range(1, 6)
        ])
        rows = select_range(rows, 4, 2)
        self.assertEqual([2, 3, 4], [r["index"] for r in selected_entries(rows)])

    def test_search_does_not_destroy_selection(self):
        rows = normalize_playlist_entries([
            {"id": "1", "title": "Alpha", "uploader": "One"},
            {"id": "2", "title": "Beta", "uploader": "Two"},
        ])
        rows[1]["selected"] = False
        visible = apply_search(rows, "beta")
        self.assertEqual(1, len(visible))
        self.assertFalse(visible[0]["selected"])

    def test_chunking(self):
        rows = normalize_playlist_entries([
            {"id": str(i), "title": str(i)} for i in range(1, 251)
        ])
        page, next_offset = chunk_entries(rows, 0, 100)
        self.assertEqual(100, len(page))
        self.assertEqual(100, next_offset)
        page, next_offset = chunk_entries(rows, 200, 100)
        self.assertEqual(50, len(page))
        self.assertIsNone(next_offset)

    def test_duration_estimate_uses_selected_known_values(self):
        rows = normalize_playlist_entries([
            {"id": "1", "duration": 10},
            {"id": "2", "duration": 20},
            {"id": "3", "duration": None},
        ])
        rows[1]["selected"] = False
        self.assertEqual(10.0, estimate_selected_duration(rows))


if __name__ == "__main__":
    unittest.main()
