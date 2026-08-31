/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

/** Physical-input values expected to need tuning after testing on an iPad. */
namespace GHOST_IOSInputTuning {

inline constexpr double pointer_acceleration_start_points_per_second = 120.0;
inline constexpr double pointer_acceleration_full_points_per_second = 1100.0;
inline constexpr double pointer_min_multiplier = 1.0;
inline constexpr double pointer_max_multiplier = 4.0;

inline constexpr double two_finger_right_click_hold_seconds = 0.30;
inline constexpr double two_finger_right_click_slop_points = 14.0;

}  // namespace GHOST_IOSInputTuning
