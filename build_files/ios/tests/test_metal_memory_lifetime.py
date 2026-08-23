#!/usr/bin/env python3

from pathlib import Path
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]
SHADER_SOURCE = REPOSITORY / "source" / "blender" / "gpu" / "metal" / "mtl_shader.mm"
CONTEXT_SOURCE = REPOSITORY / "source" / "blender" / "gpu" / "metal" / "mtl_context.mm"
CONTEXT_HEADER = REPOSITORY / "source" / "blender" / "gpu" / "metal" / "mtl_context.hh"


class MetalMemoryLifetimeTests(unittest.TestCase):
    def test_compute_pipeline_cache_deletes_its_cpp_records(self) -> None:
        source = SHADER_SOURCE.read_text()
        destructor = source[source.index("MTLShader::~MTLShader()") : source.index("valid_ = false;")]
        compute_cache = destructor[
            destructor.index("/* Free Compute pipeline cache. */") : destructor.index(
                "/* Free shader libraries. */"
            )
        ]

        self.assertIn("delete pso_inst;", compute_cache)

    def test_new_context_buffers_are_not_over_retained(self) -> None:
        source = CONTEXT_SOURCE.read_text()
        null_buffer = source[source.index("id<MTLBuffer> MTLContext::get_null_buffer()") :]
        null_buffer = null_buffer[: null_buffer.index("id<MTLBuffer> MTLContext::get_null_attribute_buffer()")]
        null_attribute = source[source.index("id<MTLBuffer> MTLContext::get_null_attribute_buffer()") :]
        null_attribute = null_attribute[: null_attribute.index("gpu::MTLTexture *MTLContext::get_dummy_texture")]
        buffer_clear = source[source.index("MTLContextComputeUtils::get_buffer_clear_pso()") :]
        buffer_clear = buffer_clear[: buffer_clear.index(r"/** \} */")]

        self.assertNotIn("[null_buffer_ retain]", null_buffer)
        self.assertNotIn("[null_attribute_buffer_ retain]", null_attribute)
        self.assertNotIn("[buffer_clear_pso_ retain]", buffer_clear)

    def test_texture_read_cache_is_released_once(self) -> None:
        source = CONTEXT_HEADER.read_text()

        self.assertEqual(source.count("free_cached_pso_map(texture_1d_read_compute_psos);"), 1)


if __name__ == "__main__":
    unittest.main()
