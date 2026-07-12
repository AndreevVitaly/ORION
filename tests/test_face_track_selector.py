import unittest

from portrait_core.tracking.selector import FaceObservation, select_dominant_track


class FaceTrackSelectorTestCase(unittest.TestCase):
    def test_selects_frequent_central_track_over_random_faces(self):
        observations = []
        for frame in range(0, 10):
            observations.append(
                FaceObservation(
                    frame_index=frame,
                    bbox=(100.0 + frame, 80.0, 90.0, 110.0),
                    frame_size=(400, 300),
                )
            )
        observations.extend(
            [
                FaceObservation(1, (10.0, 10.0, 45.0, 45.0), (400, 300)),
                FaceObservation(5, (320.0, 20.0, 40.0, 40.0), (400, 300)),
            ]
        )

        track = select_dominant_track(observations, min_count=3)

        self.assertIsNotNone(track)
        self.assertEqual(track.count, 10)
        self.assertGreater(track.mean_area, 0.05)

    def test_returns_none_when_no_repeated_track_exists(self):
        observations = [
            FaceObservation(1, (10.0, 10.0, 40.0, 40.0), (400, 300)),
            FaceObservation(5, (300.0, 10.0, 40.0, 40.0), (400, 300)),
        ]

        self.assertIsNone(select_dominant_track(observations, min_count=3))


if __name__ == "__main__":
    unittest.main()
