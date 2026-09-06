/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/* Simulator-only fault injection. Stall the real NSURL bookmark operation until the
 * test releases it, as a slow Files provider can. No production code loads this library. */
#import <Foundation/Foundation.h>
#import <UIKit/UIKit.h>
#import <objc/runtime.h>

#include <atomic>
#include <unistd.h>

static std::atomic<bool> armed{false};
static std::atomic<bool> selection_callback_active{false};
static std::atomic<bool> scope_claimed_during_selection{false};
static std::atomic<bool> scope_claimed_on_main{false};
static bool delay_selection = false;
static NSString *marker_directory;
static IMP original_bookmark;
static IMP original_picker_init;
static IMP original_selection;
static IMP original_start_access;
static NSURL *picker_directory;

static BOOL observed_start_access(id url, SEL selector);

static void picked_documents(id controls, SEL selector, id picker, NSArray *urls)
{
  [@"entered"
      writeToFile:[marker_directory stringByAppendingPathComponent:@"picker-callback-entered"]
       atomically:YES
         encoding:NSUTF8StringEncoding
            error:nil];
  /* Arm only from a real selection, never from startup refreshing a stale bookmark. */
  armed = delay_selection;
  delay_selection = false;
  if (original_start_access == nullptr) {
    NSURL *selected_url = urls.firstObject;
    Class url_class = selected_url.class;
    SEL start_selector = @selector(startAccessingSecurityScopedResource);
    Method start_access = class_getInstanceMethod(url_class, start_selector);
    original_start_access = method_getImplementation(start_access);
    if (!class_addMethod(url_class,
                         start_selector,
                         reinterpret_cast<IMP>(observed_start_access),
                         method_getTypeEncoding(start_access)))
    {
      method_setImplementation(start_access, reinterpret_cast<IMP>(observed_start_access));
    }
  }
  selection_callback_active = true;
  using SelectionFn = void (*)(id, SEL, id, NSArray *);
  reinterpret_cast<SelectionFn>(original_selection)(controls, selector, picker, urls);
  selection_callback_active = false;
  NSString *claim = scope_claimed_during_selection ?
                        (scope_claimed_on_main ? @"main" : @"worker") :
                        @"missing";
  [claim writeToFile:[marker_directory stringByAppendingPathComponent:@"grant-claim"]
          atomically:YES
            encoding:NSUTF8StringEncoding
               error:nil];
}

static id picker_init(id picker, SEL selector, NSArray *types)
{
  using InitFn = id (*)(id, SEL, NSArray *);
  UIDocumentPickerViewController *result = reinterpret_cast<InitFn>(original_picker_init)(
      picker, selector, types);
  result.directoryURL = picker_directory;
  return result;
}

extern "C" void blender_test_set_picker_directory(const char *directory)
{
  picker_directory = [[NSURL fileURLWithPath:[NSString stringWithUTF8String:directory]
                                 isDirectory:YES] retain];
  Method method = class_getInstanceMethod(UIDocumentPickerViewController.class,
                                          @selector(initForOpeningContentTypes:));
  original_picker_init = method_setImplementation(method, reinterpret_cast<IMP>(picker_init));
}

static id delayed_bookmark(id url,
                           SEL selector,
                           NSURLBookmarkCreationOptions options,
                           NSArray *keys,
                           NSURL *relative_url,
                           NSError **error)
{
  if (armed.exchange(false)) {
    NSString *thread = NSThread.isMainThread ? @"main" : @"worker";
    [thread writeToFile:[marker_directory stringByAppendingPathComponent:@"provider-entered"]
             atomically:YES
               encoding:NSUTF8StringEncoding
                  error:nil];
    const char *release_path = [marker_directory
                                   stringByAppendingPathComponent:@"provider-release"]
                                   .fileSystemRepresentation;
    /* External test process controls completion, including cleanup after a red failure. */
    while (access(release_path, F_OK) != 0) {
      usleep(10000);
    }
  }
  using BookmarkFn = id (*)(id, SEL, NSURLBookmarkCreationOptions, NSArray *, NSURL *, NSError **);
  return reinterpret_cast<BookmarkFn>(original_bookmark)(
      url, selector, options, keys, relative_url, error);
}

static BOOL observed_start_access(id url, SEL selector)
{
  if (selection_callback_active) {
    scope_claimed_during_selection = true;
    scope_claimed_on_main = NSThread.isMainThread;
  }
  using StartAccessFn = BOOL (*)(id, SEL);
  return reinterpret_cast<StartAccessFn>(original_start_access)(url, selector);
}

extern "C" void blender_test_delay_next_bookmark(const char *directory)
{
  marker_directory = [[NSString alloc] initWithUTF8String:directory];
  Method method = class_getInstanceMethod(
      NSURL.class,
      @selector(bookmarkDataWithOptions:includingResourceValuesForKeys:relativeToURL:error:));
  original_bookmark = method_setImplementation(method, reinterpret_cast<IMP>(delayed_bookmark));
  Method selection = class_getInstanceMethod(NSClassFromString(@"GHOSTIOSFileAccessControls"),
                                             @selector(documentPicker:didPickDocumentsAtURLs:));
  original_selection = method_setImplementation(selection,
                                                reinterpret_cast<IMP>(picked_documents));
  delay_selection = true;
}
