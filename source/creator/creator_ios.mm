/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup creator
 */

#include <cstdlib>

#import <UIKit/UIKit.h>

namespace blender {
struct bContext;
void WM_main_loop_body(bContext *C);
}  // namespace blender

int main_ios_callback(int argc, const char **argv);

static int g_argv_argc = 0;
static const char **g_argv_argv = nullptr;
static blender::bContext *g_blender_context = nullptr;

@interface BlenderIOSAppDelegate : UIResponder <UIApplicationDelegate>

@property(nonatomic, strong) CADisplayLink *display_link;

- (void)startBlenderLoopIfReady;

@end

static BlenderIOSAppDelegate *g_app_delegate = nil;

@implementation BlenderIOSAppDelegate

- (instancetype)init
{
  self = [super init];
  if (self) {
    g_app_delegate = self;
  }
  return self;
}

- (BOOL)application:(UIApplication *)application
    didFinishLaunchingWithOptions:(NSDictionary<UIApplicationLaunchOptionsKey, id> *)launchOptions
{
  (void)application;
  (void)launchOptions;

  NSLog(@"Blender iOS bootstrap: didFinishLaunching");

  dispatch_async(dispatch_get_main_queue(), ^{
    const int exit_code = main_ios_callback(g_argv_argc, g_argv_argv);
    if (exit_code != EXIT_SUCCESS) {
      exit(exit_code);
    }

    [self startBlenderLoopIfReady];
  });

  return YES;
}

- (void)startBlenderLoopIfReady
{
  if (g_blender_context == nullptr || self.display_link != nil) {
    return;
  }

  self.display_link = [CADisplayLink displayLinkWithTarget:self selector:@selector(tick:)];
  [self.display_link addToRunLoop:NSRunLoop.mainRunLoop forMode:NSRunLoopCommonModes];

  NSLog(@"Blender iOS bootstrap: display link started");
}

- (void)tick:(CADisplayLink *)displayLink
{
  (void)displayLink;

  if (g_blender_context != nullptr) {
    blender::WM_main_loop_body(g_blender_context);
  }
}

@end

int GHOST_iosmain(int argc, const char **argv)
{
  g_argv_argc = argc;
  g_argv_argv = argv;

  @autoreleasepool {
    return UIApplicationMain(
        argc, (char * _Nullable *)argv, nil, NSStringFromClass([BlenderIOSAppDelegate class]));
  }
}

void GHOST_iosfinalize(blender::bContext *C)
{
  g_blender_context = C;
  NSLog(@"Blender iOS bootstrap: initialization complete");

  if (g_app_delegate != nil) {
    [g_app_delegate startBlenderLoopIfReady];
  }
}
