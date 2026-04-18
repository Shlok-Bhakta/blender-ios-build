/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup GHOST
 */

#pragma once

#ifndef __APPLE__
#  error Apple only!
#endif

#include <optional>
#include <string>

#include "GHOST_SystemPaths.hh"

class GHOST_SystemPathsIOS : public GHOST_SystemPaths {
 public:
  GHOST_SystemPathsIOS() = default;
  ~GHOST_SystemPathsIOS() override = default;

  const char *getSystemDir(int version, const char *versionstr) const override;
  const char *getUserDir(int version, const char *versionstr) const override;
  std::optional<std::string> getUserSpecialDir(GHOST_TUserSpecialDirTypes type) const override;
  const char *getBinaryDir() const override;
  void addToSystemRecentFiles(const char *filepath) const override;
};
