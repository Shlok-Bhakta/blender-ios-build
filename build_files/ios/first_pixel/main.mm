/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#import <Metal/Metal.h>
#import <QuartzCore/CAMetalLayer.h>
#import <UIKit/UIKit.h>

static NSString *const kFirstPixelLogPrefix = @"[BlenderFirstPixel]";

@interface BlenderMetalView : UIView
@property(nonatomic, strong) id<MTLCommandQueue> commandQueue;
@property(nonatomic, assign) BOOL presentedFirstFrame;
@end

@implementation BlenderMetalView

+ (Class)layerClass
{
  return [CAMetalLayer class];
}

- (instancetype)initWithFrame:(CGRect)frame
{
  self = [super initWithFrame:frame];
  if (self) {
    CAMetalLayer *metalLayer = (CAMetalLayer *)self.layer;
    metalLayer.device = MTLCreateSystemDefaultDevice();
    metalLayer.pixelFormat = MTLPixelFormatBGRA8Unorm;
    metalLayer.framebufferOnly = YES;
    metalLayer.contentsScale = UIScreen.mainScreen.scale;
    self.commandQueue = [metalLayer.device newCommandQueue];
    NSLog(@"%@ metal_ready device=%@", kFirstPixelLogPrefix, metalLayer.device.name);
  }
  return self;
}

- (void)layoutSubviews
{
  [super layoutSubviews];
  CAMetalLayer *metalLayer = (CAMetalLayer *)self.layer;
  const CGFloat scale = self.window.screen.scale ?: UIScreen.mainScreen.scale;
  metalLayer.drawableSize = CGSizeMake(self.bounds.size.width * scale,
                                       self.bounds.size.height * scale);
  [self presentFirstFrame];
}

- (void)didMoveToWindow
{
  [super didMoveToWindow];
  if (self.window) {
    dispatch_async(dispatch_get_main_queue(), ^{
      [self presentFirstFrame];
    });
  }
}

- (void)presentFirstFrame
{
  if (self.presentedFirstFrame || !self.window || !self.commandQueue) {
    return;
  }

  CAMetalLayer *metalLayer = (CAMetalLayer *)self.layer;
  id<CAMetalDrawable> drawable = [metalLayer nextDrawable];
  if (!drawable) {
    dispatch_async(dispatch_get_main_queue(), ^{
      [self presentFirstFrame];
    });
    return;
  }

  MTLRenderPassDescriptor *pass = [MTLRenderPassDescriptor renderPassDescriptor];
  pass.colorAttachments[0].texture = drawable.texture;
  pass.colorAttachments[0].loadAction = MTLLoadActionClear;
  pass.colorAttachments[0].storeAction = MTLStoreActionStore;
  pass.colorAttachments[0].clearColor = MTLClearColorMake(0.025, 0.055, 0.11, 1.0);

  id<MTLCommandBuffer> commandBuffer = [self.commandQueue commandBuffer];
  id<MTLRenderCommandEncoder> encoder = [commandBuffer
      renderCommandEncoderWithDescriptor:pass];
  [encoder endEncoding];
  [commandBuffer presentDrawable:drawable];
  [commandBuffer addCompletedHandler:^(__unused id<MTLCommandBuffer> completed) {
    NSLog(@"%@ first_frame", kFirstPixelLogPrefix);
  }];
  self.presentedFirstFrame = YES;
  [commandBuffer commit];
}

@end

@interface BlenderFirstPixelDelegate : UIResponder <UIApplicationDelegate>
@property(nonatomic, strong) UIWindow *window;
@end

@implementation BlenderFirstPixelDelegate

- (BOOL)application:(UIApplication *)application
    didFinishLaunchingWithOptions:(NSDictionary *)launchOptions
{
  (void)application;
  (void)launchOptions;
  NSLog(@"%@ boot", kFirstPixelLogPrefix);

  UIViewController *controller = [UIViewController new];
  BlenderMetalView *metalView = [[BlenderMetalView alloc] initWithFrame:UIScreen.mainScreen.bounds];
  metalView.autoresizingMask = UIViewAutoresizingFlexibleWidth | UIViewAutoresizingFlexibleHeight;
  controller.view = metalView;

  UILabel *label = [[UILabel alloc] initWithFrame:CGRectZero];
  label.translatesAutoresizingMaskIntoConstraints = NO;
  label.text = @"BLENDER iOS";
  label.textColor = [UIColor colorWithRed:1.0 green:0.42 blue:0.08 alpha:1.0];
  label.font = [UIFont systemFontOfSize:28.0 weight:UIFontWeightSemibold];
  label.accessibilityIdentifier = @"first_pixel";
  [controller.view addSubview:label];
  [NSLayoutConstraint activateConstraints:@[
    [label.centerXAnchor constraintEqualToAnchor:controller.view.centerXAnchor],
    [label.centerYAnchor constraintEqualToAnchor:controller.view.centerYAnchor],
  ]];

  self.window = [[UIWindow alloc] initWithFrame:UIScreen.mainScreen.bounds];
  self.window.rootViewController = controller;
  [self.window makeKeyAndVisible];
  return YES;
}

@end

int main(int argc, char *argv[])
{
  @autoreleasepool {
    return UIApplicationMain(argc,
                             argv,
                             nil,
                             NSStringFromClass(BlenderFirstPixelDelegate.class));
  }
}
