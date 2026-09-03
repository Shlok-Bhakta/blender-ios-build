/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

extern "C" {
#include <libavutil/pixdesc.h>
}

namespace blender {

/**
 * Return the first encoder pixel format backed by ordinary CPU-addressable frame memory.
 *
 * Hardware encoders can advertise an opaque hardware-frame format before the software formats
 * they accept as input. Such formats cannot be allocated or populated with av_frame_get_buffer().
 */
inline AVPixelFormat ffmpeg_first_software_pixel_format(const AVPixelFormat *pixel_formats)
{
  if (pixel_formats == nullptr) {
    return AV_PIX_FMT_NONE;
  }

  for (const AVPixelFormat *pixel_format = pixel_formats; *pixel_format != AV_PIX_FMT_NONE;
       pixel_format++)
  {
    const AVPixFmtDescriptor *descriptor = av_pix_fmt_desc_get(*pixel_format);
    if (descriptor != nullptr && (descriptor->flags & AV_PIX_FMT_FLAG_HWACCEL) == 0) {
      return *pixel_format;
    }
  }

  return AV_PIX_FMT_NONE;
}

}  // namespace blender
