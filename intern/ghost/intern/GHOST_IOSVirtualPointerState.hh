/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

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

/** Platform-neutral state for the iOS virtual pointer. */
class GHOST_IOSVirtualPointerState {
 public:
  void initialize(const double width, const double height)
  {
    if (!initialized_) {
      x_ = width * 0.5;
      y_ = height * 0.5;
      initialized_ = true;
    }
  }

  void beginRelative(const double finger_x, const double finger_y)
  {
    finger_x_ = finger_x;
    finger_y_ = finger_y;
    relative_active_ = true;
    source_ = GHOST_IOSPointerSource::Finger;
  }

  void moveRelativeTo(const double finger_x, const double finger_y)
  {
    if (!relative_active_) {
      beginRelative(finger_x, finger_y);
      return;
    }
    x_ += finger_x - finger_x_;
    y_ += finger_y - finger_y_;
    finger_x_ = finger_x;
    finger_y_ = finger_y;
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
  bool buttons_[3] = {false, false, false};
  bool initialized_ = false;
  bool relative_active_ = false;
  bool blender_visible_ = true;
  GHOST_IOSPointerSource source_ = GHOST_IOSPointerSource::Finger;
};
