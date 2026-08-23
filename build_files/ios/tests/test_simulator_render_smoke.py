#!/usr/bin/env python3

import binascii
import importlib.util
from pathlib import Path
import struct
import unittest
import zlib


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "build_files/ios/simulator_render_smoke.py"
SPEC = importlib.util.spec_from_file_location("simulator_render_smoke", MODULE_PATH)
assert SPEC and SPEC.loader
smoke = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(smoke)


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF)
    )


def write_rgba_png(path: Path, width: int, height: int, pixels: list[bytes]) -> None:
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        rows.extend(b"".join(pixels[y * width : (y + 1) * width]))
    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", header)
        + png_chunk(b"IDAT", zlib.compress(rows))
        + png_chunk(b"IEND", b"")
    )


class SimulatorRenderSmokeTests(unittest.TestCase):
    def test_png_decoder_round_trips_rgba_pixels(self) -> None:
        import tempfile

        pixels = [bytes((index, index + 1, index + 2, 255)) for index in range(16)]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "render.png"
            write_rgba_png(path, 4, 4, pixels)
            width, height, decoded = smoke.png_pixels(path)
        self.assertEqual((width, height), (4, 4))
        self.assertEqual(decoded, pixels)

    def test_render_arguments_select_factory_eevee_frame(self) -> None:
        arguments = smoke.blender_arguments(Path("/tmp/default-cube-"))
        self.assertIn("--background", arguments)
        self.assertIn("--factory-startup", arguments)
        self.assertIn("BLENDER_EEVEE", arguments)
        self.assertIn("--render-frame", arguments)
        self.assertIn("/tmp/default-cube-", arguments)

    def test_background_mode_bypasses_clean_install_ui(self) -> None:
        source = MODULE_PATH.read_text()
        self.assertIn('"--background"', source)
        self.assertNotIn("dismiss_quick_setup", source)

    def test_rendered_viewport_expression_uses_current_eevee_identifier(self) -> None:
        expression = smoke.rendered_viewport_expression(Path("/tmp/ready"))
        self.assertIn("BLENDER_EEVEE", expression)
        self.assertNotIn("BLENDER_EEVEE_NEXT", expression)
        self.assertIn("shading,'type','RENDERED'", expression)
        self.assertIn("/tmp/ready", expression)


if __name__ == "__main__":
    unittest.main()
