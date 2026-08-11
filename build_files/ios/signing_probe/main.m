// SPDX-FileCopyrightText: 2026 Blender Authors
//
// SPDX-License-Identifier: GPL-2.0-or-later

#import <UIKit/UIKit.h>

@interface SigningProbeDelegate : UIResponder <UIApplicationDelegate>
@property(nonatomic, strong) UIWindow *window;
@end

@implementation SigningProbeDelegate

- (BOOL)application:(UIApplication *)application
    didFinishLaunchingWithOptions:(NSDictionary *)launch_options
{
  (void)application;
  (void)launch_options;

  self.window = [[UIWindow alloc] initWithFrame:[UIScreen mainScreen].bounds];
  UIViewController *controller = [[UIViewController alloc] init];
  controller.view.backgroundColor = UIColor.systemOrangeColor;
  self.window.rootViewController = controller;
  [self.window makeKeyAndVisible];
  return YES;
}

@end

int main(int argc, char *argv[])
{
  @autoreleasepool {
    return UIApplicationMain(argc, argv, nil, NSStringFromClass(SigningProbeDelegate.class));
  }
}
