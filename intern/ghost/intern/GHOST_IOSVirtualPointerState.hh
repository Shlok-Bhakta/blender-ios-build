/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

#include "GHOST_IOSInputTuning.hh"

#include <algorithm>
#include <cmath>
#include <cstdint>

enum class GHOST_IOSPointerSource : uint8_t {
  Finger,
  Pencil,
  Hardware,
};

enum class GHOST_IOSPointerButton : uint8_t {
  Left,
  Middle,
  Right,
};

/** Pure acceleration math, kept independent of UIKit so it can be tested directly. */
class GHOST_IOSPointerAcceleration {
 public:
  static double multiplier(const double delta_x,
                           const double delta_y,
                           const double elapsed_seconds,
                           const double input_scale)
  {
    if (elapsed_seconds <= 0.0 || input_scale <= 0.0) {
      return GHOST_IOSInputTuning::pointer_min_multiplier;
    }

    const double distance_points = std::hypot(delta_x, delta_y) / input_scale;
    const double velocity_points_per_second = distance_points / elapsed_seconds;
    const double acceleration_range =
        GHOST_IOSInputTuning::pointer_acceleration_full_points_per_second -
        GHOST_IOSInputTuning::pointer_acceleration_start_points_per_second;
    const double normalized_velocity = std::clamp(
        (velocity_points_per_second -
         GHOST_IOSInputTuning::pointer_acceleration_start_points_per_second) /
            acceleration_range,
        0.0,
        1.0);
    const double smooth_velocity = normalized_velocity * normalized_velocity *
                                   (3.0 - 2.0 * normalized_velocity);
    return GHOST_IOSInputTuning::pointer_min_multiplier +
           (GHOST_IOSInputTuning::pointer_max_multiplier -
            GHOST_IOSInputTuning::pointer_min_multiplier) *
               smooth_velocity;
  }
};

/** Platform-neutral state for the iOS virtual pointer. */
class GHOST_IOSVirtualPointerState {
 public:
  void initialize(const double width, const double height, const double input_scale)
  {
    input_scale_ = input_scale > 0.0 ? input_scale : 1.0;
    if (!initialized_) {
      x_ = width * 0.5;
      y_ = height * 0.5;
      initialized_ = true;
    }
  }

  void beginRelative(const double finger_x, const double finger_y, const double timestamp_seconds)
  {
    finger_x_ = finger_x;
    finger_y_ = finger_y;
    last_relative_time_seconds_ = timestamp_seconds;
    relative_active_ = true;
    source_ = GHOST_IOSPointerSource::Finger;
  }

  void moveRelativeTo(const double finger_x, const double finger_y, const double timestamp_seconds)
  {
    if (!relative_active_) {
      beginRelative(finger_x, finger_y, timestamp_seconds);
      return;
    }
    const double delta_x = finger_x - finger_x_;
    const double delta_y = finger_y - finger_y_;
    const double multiplier = GHOST_IOSPointerAcceleration::multiplier(
        delta_x, delta_y, timestamp_seconds - last_relative_time_seconds_, input_scale_);
    x_ += delta_x * multiplier;
    y_ += delta_y * multiplier;
    finger_x_ = finger_x;
    finger_y_ = finger_y;
    last_relative_time_seconds_ = timestamp_seconds;
    initialized_ = true;
    source_ = GHOST_IOSPointerSource::Finger;
  }

  void endRelative()
  {
    relative_active_ = false;
  }

  void moveAbsolute(const double x, const double y, const GHOST_IOSPointerSource source)
  {
    x_ = x;
    y_ = y;
    initialized_ = true;
    source_ = source;
    relative_active_ = false;
  }

  void warp(const double x, const double y)
  {
    x_ = x;
    y_ = y;
    initialized_ = true;
  }

  void setSource(const GHOST_IOSPointerSource source)
  {
    source_ = source;
  }

  void setButton(const GHOST_IOSPointerButton button, const bool down)
  {
    buttons_[static_cast<uint8_t>(button)] = down;
  }

  bool buttonDown(const GHOST_IOSPointerButton button) const
  {
    return buttons_[static_cast<uint8_t>(button)];
  }

  void clearButtons()
  {
    for (bool &button : buttons_) {
      button = false;
    }
  }

  void setBlenderVisibility(const bool visible)
  {
    blender_visible_ = visible;
  }

  bool visible() const
  {
    return blender_visible_ && source_ != GHOST_IOSPointerSource::Pencil;
  }

  double x() const
  {
    return x_;
  }

  double y() const
  {
    return y_;
  }

 private:
  double x_ = 0.0;
  double y_ = 0.0;
  double finger_x_ = 0.0;
  double finger_y_ = 0.0;
  double last_relative_time_seconds_ = 0.0;
  double input_scale_ = 1.0;
  bool buttons_[3] = {false, false, false};
  bool initialized_ = false;
  bool relative_active_ = false;
  bool blender_visible_ = true;
  GHOST_IOSPointerSource source_ = GHOST_IOSPointerSource::Finger;
};
