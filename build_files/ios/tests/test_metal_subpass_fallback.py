#!/usr/bin/env python3
"""Guard Metal subpass emulation used by the iOS Simulator."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]


class MetalSubpassFallbackTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.backend = (ROOT / "source/blender/gpu/metal/mtl_backend.mm").read_text()
        cls.generator = (ROOT / "source/blender/gpu/metal/mtl_shader_generate.cc").read_text()
        cls.interface = (ROOT / "source/blender/gpu/metal/mtl_shader_interface.mm").read_text()
        cls.framebuffer = (ROOT / "source/blender/gpu/metal/mtl_framebuffer.mm").read_text()

    def test_simulator_does_not_advertise_framebuffer_fetch(self) -> None:
        self.assertIn("TARGET_OS_SIMULATOR", self.backend)
        self.assertIn("supports_native_tile_inputs = false", self.backend)

    def test_shader_generator_loads_subpass_inputs_from_bound_textures(self) -> None:
        self.assertIn("generate_subpass_input_fallback", self.generator)
        self.assertIn("MTLBackend::get_capabilities().supports_native_tile_inputs", self.generator)
        self.assertIn("[[position]]", self.generator)
        self.assertIn("[[texture(", self.generator)
        self.assertIn(".read(", self.generator)

    def test_fallback_images_are_registered_with_shader_interface(self) -> None:
        self.assertIn("info.subpass_inputs_", self.interface)
        self.assertIn("enabled_ima_mask_", self.interface)
        self.assertIn("gpu_subpass_img_", self.interface)

    def test_subpass_transition_binds_read_attachments(self) -> None:
        self.assertIn("GPU_texture_image_bind", self.framebuffer)
        self.assertIn("attachment_config.read", self.framebuffer)


if __name__ == "__main__":
    unittest.main()
