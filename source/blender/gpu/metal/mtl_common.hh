/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

#include <Foundation/Foundation.h>
#include <Metal/Metal.h>

/** -- Renderer Options -- */
/* Number of frames over which rolling averages are taken. */
#define MTL_FRAME_AVERAGE_COUNT 15
#define MTL_MAX_DRAWABLES 3
#define MTL_FORCE_WAIT_IDLE 0

/* Number of frames for which we retain in-flight resources such as scratch buffers.
 * Set as number of GPU frames in flight, plus an additional value for extra possible CPU frame. */
#define MTL_NUM_SAFE_FRAMES (MTL_MAX_DRAWABLES + 1)

/* Display debug information about missing attributes and incorrect vertex formats. */
#define MTL_DEBUG_SHADER_ATTRIBUTES 0

inline MTLResourceOptions mtl_resource_options_cpu_visible(id<MTLDevice> device)
{
#ifdef WITH_APPLE_CROSSPLATFORM
  (void)device;
  return MTLResourceStorageModeShared;
#else
  return ([device hasUnifiedMemory]) ? MTLResourceStorageModeShared :
                                       MTLResourceStorageModeManaged;
#endif
}

inline bool mtl_resource_options_is_managed(MTLResourceOptions options)
{
#ifdef WITH_APPLE_CROSSPLATFORM
  (void)options;
  return false;
#else
  return (options & MTLResourceStorageModeManaged) != 0;
#endif
}

inline bool mtl_storage_mode_is_managed(MTLStorageMode storage_mode)
{
#ifdef WITH_APPLE_CROSSPLATFORM
  (void)storage_mode;
  return false;
#else
  return storage_mode == MTLStorageModeManaged;
#endif
}

inline void mtl_buffer_flush_range(id<MTLBuffer> buffer, NSRange range)
{
#ifndef WITH_APPLE_CROSSPLATFORM
  [buffer didModifyRange:range];
#else
  (void)buffer;
  (void)range;
#endif
}

inline void mtl_synchronize_resource(id<MTLBlitCommandEncoder> encoder, id<MTLResource> resource)
{
#ifndef WITH_APPLE_CROSSPLATFORM
  [encoder synchronizeResource:resource];
#else
  (void)encoder;
  (void)resource;
#endif
}
