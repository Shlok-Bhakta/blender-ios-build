#!/usr/bin/env python3

import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
MOVIE_DIR = ROOT / "source" / "blender" / "imbuf" / "movie" / "intern"


class FFmpegMovieOutputTests(unittest.TestCase):
    def test_hardware_only_pixel_formats_are_not_used_as_cpu_frames(self) -> None:
        compat = (MOVIE_DIR / "movie_write_pixel_format.hh").read_text()
        writer = (MOVIE_DIR / "movie_write.cc").read_text()

        self.assertIn("AV_PIX_FMT_FLAG_HWACCEL", compat)
        self.assertIn("ffmpeg_first_software_pixel_format", compat)
        self.assertIn("ffmpeg_first_software_pixel_format(pix_fmts)", writer)

    def test_movie_setup_handles_frame_allocation_failure(self) -> None:
        writer = (MOVIE_DIR / "movie_write.cc").read_text()

        self.assertIn("Failed to allocate FFmpeg output frame", writer)
        self.assertIn("Failed to allocate FFmpeg conversion frame", writer)
        self.assertGreaterEqual(writer.count("avcodec_free_context(&c)"), 3)


if __name__ == "__main__":
    unittest.main()
