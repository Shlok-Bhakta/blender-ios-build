#!/usr/bin/env python3
"""Guard the iOS fallback for Metal attachmentless raster passes."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]


class MetalAttachmentlessRenderingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.header = (ROOT / "source/blender/gpu/metal/mtl_framebuffer.hh").read_text()
        cls.framebuffer = (ROOT / "source/blender/gpu/metal/mtl_framebuffer.mm").read_text()
        cls.shader = (ROOT / "source/blender/gpu/metal/mtl_shader.mm").read_text()

    def test_fallback_is_limited_to_ios(self) -> None:
        self.assertIn("#ifdef WITH_APPLE_CROSSPLATFORM", self.header)
        self.assertIn("requires_attachmentless_color_target", self.header)

    def test_render_pass_owns_a_real_dummy_target(self) -> None:
        self.assertIn("attachmentless_color_texture_", self.header)
        self.assertIn("newTextureWithDescriptor", self.framebuffer)
        self.assertIn("MTLTextureUsageRenderTarget", self.framebuffer)
        self.assertIn("MTLStorageModePrivate", self.framebuffer)
        self.assertIn("MTLLoadActionDontCare", self.framebuffer)
        self.assertIn("MTLStoreActionDontCare", self.framebuffer)

    def test_pipeline_matches_dummy_target_without_writes(self) -> None:
        self.assertIn("attachmentless_color_format", self.header)
        self.assertIn("framebuffer->requires_attachmentless_color_target()", self.shader)
        self.assertIn("pipeline_descriptor.color_attachment_format[0]", self.shader)
        self.assertIn("pipeline_descriptor.color_attachment_mask &= ~1u", self.shader)

    def test_dummy_target_is_released(self) -> None:
        self.assertIn("[attachmentless_color_texture_ release]", self.framebuffer)


if __name__ == "__main__":
    unittest.main()
