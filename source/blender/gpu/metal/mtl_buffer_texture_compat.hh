/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

#import <Metal/Metal.h>

namespace blender::gpu {

class MTLBuffer;

/**
 * Return a private copy for iOS buffer-backed textures. This avoids simulator validation failures
 * and keeps the physical-device render path on GPU-private storage. The caller owns the returned
 * pooled buffer. A null return means the source can be used directly.
 */
MTLBuffer *mtl_buffer_texture_compat_prepare_private_copy(id<MTLBuffer> source_buffer);

}  // namespace blender::gpu
