# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

list(APPEND SRC
  intern/GHOST_ContextIOS.hh
  intern/GHOST_ContextIOS.mm
  intern/GHOST_EventTouch.hh
  intern/GHOST_SystemIOS.hh
  intern/GHOST_SystemIOS.mm
  intern/GHOST_SystemPathsCocoa.hh
  intern/GHOST_SystemPathsIOS.mm
  intern/GHOST_WindowIOS.hh
  intern/GHOST_WindowIOS.mm
)

add_definitions(
  -DGHOST_PLATFORM_SYSTEM_HEADER=\"GHOST_SystemIOS.hh\"
  -DGHOST_PLATFORM_SYSTEM_CLASS=GHOST_SystemIOS
  -DGHOST_PLATFORM_SYSTEM_NAME=\"IOS\"
)
