/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup spfile
 * \brief iOS System File menu implementation.
 */

#import <Foundation/Foundation.h>

#include "BLI_fileops.h"
#include "BLI_path_utils.hh"
#include "BLI_string.h"

#include "BLT_translation.hh"
#include "UI_resources.hh"

#include "fsmenu.hh"

namespace blender {

void fsmenu_read_system(FSMenu *fsmenu, int read_bookmarks)
{
  NSURL *documents_url = [[[NSFileManager defaultManager]
      URLsForDirectory:NSDocumentDirectory
             inDomains:NSUserDomainMask] firstObject];

  if (documents_url != nil) {
    char path[FILE_MAXDIR];
    BLI_snprintf(path, sizeof(path), "%s", documents_url.path.UTF8String);
    fsmenu_insert_entry(fsmenu,
                        FS_CATEGORY_SYSTEM_BOOKMARKS,
                        path,
                        N_("Documents"),
                        ICON_DOCUMENTS,
                        FS_INSERT_LAST);
  }

  UNUSED_VARS(read_bookmarks);
}

}  // namespace blender
