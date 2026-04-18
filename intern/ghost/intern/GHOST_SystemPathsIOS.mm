/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#import <Foundation/Foundation.h>

#include "GHOST_SystemPathsIOS.hh"

#include <cstring>

namespace {

const char *path_from_nsstring(NSString *path, char *buffer, const size_t buffer_size)
{
  if (path == nil || buffer_size == 0) {
    return nullptr;
  }

  const char *path_cstr = [path cStringUsingEncoding:NSUTF8StringEncoding];
  if (path_cstr == nullptr) {
    return nullptr;
  }

  strncpy(buffer, path_cstr, buffer_size - 1);
  buffer[buffer_size - 1] = '\0';
  return buffer;
}

NSString *user_path_for_directory(NSSearchPathDirectory directory)
{
  NSArray<NSString *> *paths = NSSearchPathForDirectoriesInDomains(
      directory, NSUserDomainMask, YES);
  return paths.count ? paths[0] : nil;
}

}  // namespace

const char *GHOST_SystemPathsIOS::getSystemDir(int /*version*/, const char *versionstr) const
{
  static char path[512] = "";

  @autoreleasepool {
    NSString *bundle_path = NSBundle.mainBundle.bundlePath;
    if (bundle_path == nil) {
      return nullptr;
    }

    NSString *system_path = [bundle_path stringByAppendingPathComponent:@"Assets"];
    if (versionstr && versionstr[0]) {
      system_path = [system_path stringByAppendingPathComponent:@(versionstr)];
    }

    return path_from_nsstring(system_path, path, sizeof(path));
  }
}

const char *GHOST_SystemPathsIOS::getUserDir(int /*version*/, const char *versionstr) const
{
  static char path[512] = "";

  @autoreleasepool {
    NSString *base_path = user_path_for_directory(NSApplicationSupportDirectory);
    if (base_path == nil) {
      return nullptr;
    }

    NSString *user_path = [base_path stringByAppendingPathComponent:@"Blender"];
    if (versionstr && versionstr[0]) {
      user_path = [user_path stringByAppendingPathComponent:@(versionstr)];
    }

    return path_from_nsstring(user_path, path, sizeof(path));
  }
}

std::optional<std::string> GHOST_SystemPathsIOS::getUserSpecialDir(
    GHOST_TUserSpecialDirTypes type) const
{
  @autoreleasepool {
    NSSearchPathDirectory directory = NSDocumentDirectory;

    switch (type) {
      case GHOST_kUserSpecialDirCaches:
        directory = NSCachesDirectory;
        break;
      case GHOST_kUserSpecialDirDocuments:
      case GHOST_kUserSpecialDirDesktop:
      case GHOST_kUserSpecialDirDownloads:
      case GHOST_kUserSpecialDirMusic:
      case GHOST_kUserSpecialDirPictures:
      case GHOST_kUserSpecialDirVideos:
        directory = NSDocumentDirectory;
        break;
      default:
        return std::nullopt;
    }

    NSString *path = user_path_for_directory(directory);
    if (path == nil) {
      return std::nullopt;
    }

    return std::string([path cStringUsingEncoding:NSUTF8StringEncoding]);
  }
}

const char *GHOST_SystemPathsIOS::getBinaryDir() const
{
  static char path[512] = "";

  @autoreleasepool {
    return path_from_nsstring(NSBundle.mainBundle.bundlePath, path, sizeof(path));
  }
}

void GHOST_SystemPathsIOS::addToSystemRecentFiles(const char * /*filepath*/) const {}
