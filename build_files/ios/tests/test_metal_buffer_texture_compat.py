#!/usr/bin/env python3

import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
METAL_DIR = ROOT / "source" / "blender" / "gpu" / "metal"


class MetalBufferTextureCompatTests(unittest.TestCase):
    def test_ios_uses_private_backing_for_linear_buffer_textures(self) -> None:
        compat = (METAL_DIR / "mtl_buffer_texture_compat.mm").read_text()

        self.assertIn("TARGET_OS_IOS", compat)
        self.assertIn("source_buffer.storageMode != MTLStorageModePrivate", compat)
        self.assertRegex(compat, r"allocate\(\s*source_buffer\.length, false\)")
        self.assertIn("copyFromBuffer:source_buffer", compat)

    def test_texture_creation_uses_compat_buffer_but_tracks_original_vbo(self) -> None:
        texture = (METAL_DIR / "mtl_texture.mm").read_text()

        self.assertIn("mtl_buffer_texture_compat_prepare_private_copy", texture)
        self.assertIn("texture_buffer.storageMode", texture)
        self.assertIn("[texture_buffer", texture)
        self.assertIn("vert_buffer_mtl_ = source_buffer", texture)

    def test_compat_shim_is_part_of_the_metal_target(self) -> None:
        cmake = (ROOT / "source" / "blender" / "gpu" / "CMakeLists.txt").read_text()

        self.assertIn("metal/mtl_buffer_texture_compat.mm", cmake)
        self.assertIn("metal/mtl_buffer_texture_compat.hh", cmake)


if __name__ == "__main__":
    unittest.main()
