"""Тесты приложения Dataset Builder."""

import hashlib
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from apps.dataset_builder.builder import build_dataset, collect_input_images, is_url


class DatasetBuilderAppTestCase(unittest.TestCase):
    @patch("apps.dataset_builder.builder.create_portrait_report")
    def test_dataset_builder_delegates_face_analysis_to_portrait_core(self, report_mock):
        report_mock.return_value = {
            "schema_version": 3,
            "id": "PFR-test",
            "uuid": "12345678-1234-5678-1234-567812345678",
            "quality": {"status": "passed", "issues": []},
            "lic_core": {},
            "morphology": {},
            "measurements": {},
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "frame001.jpg"
            image.write_bytes(b"not a real image; core is mocked")
            output = root / "dataset"

            summary = build_dataset(str(root), str(output), model_path="model.task")

            dataset_dir = Path(summary["dataset_dir"])
            report_path = dataset_dir / "pfr" / "0001_frame001_portrait.json"
            copied_image = dataset_dir / "images" / "0001_frame001.jpg"
            dataset_json = dataset_dir / "dataset.json"

            self.assertEqual(summary["created_reports"], 1)
            self.assertEqual(summary["statuses"]["passed"], 1)
            self.assertTrue(report_path.exists())
            self.assertTrue(copied_image.exists())
            self.assertTrue(dataset_json.exists())
            dataset = json.loads(dataset_json.read_text(encoding="utf-8"))
            self.assertTrue(dataset["id"].startswith("DS-"))
            self.assertEqual(dataset["items"][0]["pfr_id"], "PFR-test")
            report_mock.assert_called_once()
            self.assertEqual(report_mock.call_args.kwargs["model_path"], "model.task")
            self.assertEqual(report_mock.call_args.kwargs["input_metadata"]["dataset_id"], dataset["id"])

    @patch("apps.dataset_builder.builder.create_portrait_report")
    def test_dataset_builder_emits_log_and_progress_callbacks(self, report_mock):
        report_mock.return_value = {
            "schema_version": 3,
            "quality": {"status": "warning", "issues": ["test warning"]},
        }
        logs = []
        progress = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "frame001.jpg").write_bytes(b"one")
            (root / "frame002.jpg").write_bytes(b"two")
            output = root / "dataset"

            summary = build_dataset(
                str(root),
                str(output),
                log=logs.append,
                progress=lambda current, total: progress.append((current, total)),
            )
            self.assertTrue(Path(summary["dataset_dir"], "dataset.json").exists())

        self.assertEqual(summary["created_reports"], 2)
        self.assertEqual(progress[-1], (2, 2))
        self.assertTrue(any("portrait_core" in message for message in logs))


    @patch("portrait_core.tracking.select_dominant_face_track")
    def test_video_collection_can_use_dominant_face_track(self, selector_mock):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video = root / "video.mp4"
            video.write_bytes(b"fake video")
            selected = root / "selected.jpg"
            selected.write_bytes(b"face crop")
            selector_mock.return_value = [selected]

            images = collect_input_images(
                str(video),
                str(root / "frames"),
                dominant_face_track=True,
                min_track_length=4,
            )

        self.assertEqual(images, [selected])
        selector_mock.assert_called_once()
        self.assertEqual(selector_mock.call_args.kwargs["min_track_length"], 4)


    def test_is_url_accepts_http_sources_only(self):
        self.assertTrue(is_url("https://example.com/video"))
        self.assertFalse(is_url("D:/videos/example.mp4"))

    @patch("apps.dataset_builder.builder._extract_video_frames")
    @patch("apps.dataset_builder.builder.download_video_source")
    def test_url_collection_downloads_video_before_frame_extraction(self, download_mock, extract_mock):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            downloaded = root / "downloaded.mp4"
            downloaded.write_bytes(b"fake video")
            frame = root / "frame000000.jpg"
            frame.write_bytes(b"fake frame")
            download_mock.return_value = downloaded
            extract_mock.return_value = [frame]

            images = collect_input_images(
                "https://example.com/video",
                str(root / "frames"),
                frame_step=12,
            )

        self.assertEqual(images, [frame])
        download_mock.assert_called_once()
        extract_mock.assert_called_once()
        self.assertEqual(extract_mock.call_args.args[0], downloaded)
        self.assertEqual(extract_mock.call_args.args[2], 12)


    @patch("apps.dataset_builder.builder._is_readable_video")
    @patch("apps.dataset_builder.builder.subprocess.Popen")
    def test_download_prefers_readable_mp4_over_newer_webm(self, popen_mock, readable_mock):
        class FakeStdout:
            def __iter__(self):
                return iter(["[download] 100%"])

        class FakeProcess:
            stdout = FakeStdout()

            def wait(self):
                return 0

            def poll(self):
                return 0

            def terminate(self):
                return None

        popen_mock.return_value = FakeProcess()
        readable_mock.side_effect = lambda path: path.suffix.lower() == ".mp4"
        with tempfile.TemporaryDirectory() as directory:
            from apps.dataset_builder.builder import download_video_source

            root = Path(directory)
            token = hashlib.sha256(b"https://example.com/video").hexdigest()[:12]
            mp4 = root / f"source-{token}.f399.mp4"
            webm = root / f"source-{token}.f251.webm"
            mp4.write_bytes(b"video")
            webm.write_bytes(b"audio")

            selected = download_video_source("https://example.com/video", root)

        self.assertEqual(selected.name, mp4.name)

if __name__ == "__main__":
    unittest.main()
