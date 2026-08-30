# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

list(APPEND SRC intern/wm_platform_ios.cc)
add_definitions(-DBLENDER_PLATFORM_INIT_AFTER_HOMEFILE=wm_init_ios_cycles_smoke)
