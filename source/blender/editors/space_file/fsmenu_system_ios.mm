/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup spfile
 * \brief iOS System File menu implementation.
 */

#import <Foundation/Foundation.h>

#include <cstdlib>
#include <cstring>

#include "BLI_fileops.h"
#include "BLI_path_utils.hh"
#include "BLI_string.h"

#include "BLT_translation.hh"
#include "UI_resources.hh"

#include "WM_api.hh"
#include "WM_types.hh"

#include "fsmenu.hh"

static NSString *const GHOST_IOSFileLocationDidGrantAccess =
    @"GHOST_IOSFileLocationDidGrantAccess";
static NSString *const IOSFileLocationBookmarksKey = @"BlenderIOSFileLocationBookmarks";

static NSMutableDictionary<NSString *, NSURL *> *g_security_scoped_urls = nil;
static NSObject *g_file_location_observer = nil;

static NSString *IOS_file_location_key(NSURL *url)
{
  return url.URLByStandardizingPath.path;
}

static void IOS_begin_accessing_file_location(NSURL *url)
{
  NSString *key = IOS_file_location_key(url);
  if (key == nil || g_security_scoped_urls[key] != nil) {
    return;
  }

  if ([url startAccessingSecurityScopedResource]) {
    g_security_scoped_urls[key] = url;
  }
}

static void IOS_stop_accessing_file_locations()
{
  for (NSURL *url in g_security_scoped_urls.allValues) {
    [url stopAccessingSecurityScopedResource];
  }
  [g_security_scoped_urls removeAllObjects];
  [g_security_scoped_urls release];
  g_security_scoped_urls = nil;

  if (g_file_location_observer != nil) {
    [[NSNotificationCenter defaultCenter] removeObserver:g_file_location_observer];
    [g_file_location_observer release];
    g_file_location_observer = nil;
  }
}

static NSURL *IOS_resolve_file_location(NSData *bookmark, BOOL *is_stale)
{
  if (![bookmark isKindOfClass:[NSData class]]) {
    return nil;
  }

  NSError *error = nil;
  NSURL *url = [NSURL URLByResolvingBookmarkData:bookmark
                                         options:0
                                   relativeToURL:nil
                             bookmarkDataIsStale:is_stale
                                           error:&error];
  if (url == nil) {
    NSLog(@"Unable to restore Blender file location: %@", error.localizedDescription);
  }
  return url;
}

static NSData *IOS_create_file_location_bookmark(NSURL *url)
{
  NSError *error = nil;
  NSData *bookmark = [url bookmarkDataWithOptions:NSURLBookmarkCreationMinimalBookmark
                   includingResourceValuesForKeys:nil
                                    relativeToURL:nil
                                            error:&error];
  if (bookmark == nil) {
    NSLog(@"Unable to save Blender file location: %@", error.localizedDescription);
  }
  return bookmark;
}

static void IOS_persist_file_location(NSURL *url)
{
  IOS_begin_accessing_file_location(url);
  NSData *new_bookmark = IOS_create_file_location_bookmark(url);
  if (new_bookmark == nil) {
    return;
  }

  NSUserDefaults *defaults = [NSUserDefaults standardUserDefaults];
  NSArray<NSData *> *saved_bookmarks = [defaults arrayForKey:IOSFileLocationBookmarksKey];
  NSMutableArray<NSData *> *bookmarks = saved_bookmarks != nil ? [saved_bookmarks mutableCopy] :
                                                                 [[NSMutableArray alloc] init];
  NSString *new_key = IOS_file_location_key(url);
  NSIndexSet *duplicates = [bookmarks
      indexesOfObjectsPassingTest:^BOOL(NSData *bookmark, NSUInteger index, BOOL *stop) {
        (void)index;
        (void)stop;
        BOOL is_stale = NO;
        NSURL *saved_url = IOS_resolve_file_location(bookmark, &is_stale);
        return [IOS_file_location_key(saved_url) isEqualToString:new_key];
      }];
  [bookmarks removeObjectsAtIndexes:duplicates];
  [bookmarks addObject:new_bookmark];
  [defaults setObject:bookmarks forKey:IOSFileLocationBookmarksKey];
  [bookmarks release];
}

static void IOS_insert_file_location(blender::FSMenu *fsmenu, NSURL *url)
{
  const char *path = url.path.UTF8String;
  if (path == nullptr || path[0] == '\0' || strlen(path) >= FILE_MAXDIR) {
    return;
  }

  NSString *name = url.lastPathComponent;
  blender::fsmenu_insert_entry(fsmenu,
                               blender::FS_CATEGORY_SYSTEM_BOOKMARKS,
                               path,
                               name.length > 0 ? name.UTF8String : nullptr,
                               blender::ICON_FILE_FOLDER,
                               blender::FS_INSERT_LAST);
}

@interface BlenderIOSFileLocationObserver : NSObject
- (void)didGrantFileLocationAccess:(NSNotification *)notification;
@end

@implementation BlenderIOSFileLocationObserver
- (void)didGrantFileLocationAccess:(NSNotification *)notification
{
  NSURL *url = [notification.object isKindOfClass:[NSURL class]] ? notification.object : nil;
  if (url == nil || !url.isFileURL) {
    return;
  }

  IOS_persist_file_location(url);
  IOS_insert_file_location(blender::ED_fsmenu_get(), url);
  blender::WM_main_add_notifier(NC_SPACE | ND_SPACE_FILE_PARAMS, nullptr);
}
@end

static void IOS_ensure_file_location_observer()
{
  if (g_file_location_observer != nil) {
    return;
  }

  g_security_scoped_urls = [[NSMutableDictionary alloc] init];
  g_file_location_observer = [[BlenderIOSFileLocationObserver alloc] init];
  [[NSNotificationCenter defaultCenter] addObserver:g_file_location_observer
                                           selector:@selector(didGrantFileLocationAccess:)
                                               name:GHOST_IOSFileLocationDidGrantAccess
                                             object:nil];
  atexit(IOS_stop_accessing_file_locations);
}

namespace blender {

void fsmenu_read_system(FSMenu *fsmenu, int read_bookmarks)
{
  IOS_ensure_file_location_observer();

  NSURL *documents_url = [[[NSFileManager defaultManager] URLsForDirectory:NSDocumentDirectory
                                                                 inDomains:NSUserDomainMask]
      firstObject];

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

  if (!read_bookmarks) {
    return;
  }

  NSArray<NSData *> *bookmarks = [[NSUserDefaults standardUserDefaults]
      arrayForKey:IOSFileLocationBookmarksKey];
  for (NSData *bookmark in bookmarks) {
    BOOL is_stale = NO;
    NSURL *url = IOS_resolve_file_location(bookmark, &is_stale);
    if (url == nil) {
      continue;
    }
    IOS_begin_accessing_file_location(url);
    IOS_insert_file_location(fsmenu, url);
    if (is_stale) {
      IOS_persist_file_location(url);
    }
  }
}

}  // namespace blender
