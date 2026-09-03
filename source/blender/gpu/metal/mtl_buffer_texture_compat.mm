/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "mtl_buffer_texture_compat.hh"

#include "mtl_context.hh"
#include "mtl_memory.hh"

#import <TargetConditionals.h>

namespace blender::gpu {

MTLBuffer *mtl_buffer_texture_compat_prepare_private_copy(id<MTLBuffer> source_buffer)
{
#if TARGET_OS_IOS
  if (source_buffer.storageMode != MTLStorageModePrivate) {
    MTLContext *context = MTLContext::get();
    MTLBuffer *private_buffer = MTLContext::get_global_memory_manager()->allocate(
        source_buffer.length, false);
    id<MTLBlitCommandEncoder> encoder =
        context->main_command_buffer.ensure_begin_blit_encoder();
    [encoder copyFromBuffer:source_buffer
               sourceOffset:0
                   toBuffer:private_buffer->get_metal_buffer()
          destinationOffset:0
                       size:source_buffer.length];
    return private_buffer;
  }
#else
  (void)source_buffer;
#endif
  return nullptr;
}

}  // namespace blender::gpu
