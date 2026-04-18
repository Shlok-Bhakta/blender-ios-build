/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "GHOST_WindowIOS.hh"

#include "GHOST_ContextMTL.hh"
#include "GHOST_SystemIOS.hh"

#import <Metal/Metal.h>
#import <QuartzCore/QuartzCore.h>
#import <UIKit/UIKit.h>

@interface GHOSTIOSMetalView : UIView {
 @public
  GHOST_WindowIOS *window_ios_;
}

- (instancetype)initWithWindowIOS:(GHOST_WindowIOS *)windowIOS frame:(CGRect)frame;

@end

@implementation GHOSTIOSMetalView

+ (Class)layerClass
{
  return [CAMetalLayer class];
}

- (instancetype)initWithWindowIOS:(GHOST_WindowIOS *)windowIOS frame:(CGRect)frame
{
  self = [super initWithFrame:frame];
  if (self) {
    window_ios_ = windowIOS;
    self.autoresizingMask = UIViewAutoresizingFlexibleWidth | UIViewAutoresizingFlexibleHeight;
    self.contentScaleFactor = UIScreen.mainScreen.scale;
    self.multipleTouchEnabled = NO;
    self.opaque = YES;
  }
  return self;
}

- (void)layoutSubviews
{
  [super layoutSubviews];
  if (window_ios_ != nullptr) {
    window_ios_->updateDrawingSize();
    window_ios_->notifyResize();
  }
}

- (void)didMoveToWindow
{
  [super didMoveToWindow];
  if (window_ios_ != nullptr && self.window != nil) {
    window_ios_->notifyActivate();
    window_ios_->notifyUpdate();
  }
}

@end

GHOST_WindowIOS::GHOST_WindowIOS(GHOST_SystemIOS *systemIOS,
                                 const char *title,
                                 int32_t left,
                                 int32_t top,
                                 uint32_t width,
                                 uint32_t height,
                                 GHOST_TWindowState state,
                                 GHOST_TDrawingContextType type,
                                 const GHOST_ContextParams &context_params,
                                 bool is_dialog)
    : GHOST_Window(width, height, state, context_params, false),
      system_ios_(systemIOS),
      window_(nil),
      root_view_controller_(nil),
      metal_view_(nil),
      metal_layer_(nil),
      title_(title ? title : ""),
      is_dialog_(is_dialog)
{
  @autoreleasepool {
    CGRect frame = CGRectMake(CGFloat(left), CGFloat(top), CGFloat(width), CGFloat(height));
    if (state == GHOST_kWindowStateFullScreen) {
      frame = UIScreen.mainScreen.bounds;
      full_screen_ = true;
    }

    window_ = [[UIWindow alloc] initWithFrame:frame];
    root_view_controller_ = [[UIViewController alloc] init];
    metal_view_ = [[GHOSTIOSMetalView alloc] initWithWindowIOS:this frame:window_.bounds];
    metal_layer_ = (CAMetalLayer *)metal_view_.layer;

    id<MTLDevice> metal_device = MTLCreateSystemDefaultDevice();
    if (metal_device != nil) {
      metal_layer_.device = metal_device;
      metal_layer_.opaque = YES;
      metal_layer_.framebufferOnly = YES;
      metal_layer_.presentsWithTransaction = NO;
      metal_layer_.pixelFormat = MTLPixelFormatRGBA16Float;
    }

    root_view_controller_.view = metal_view_;

    if (@available(iOS 13.0, *)) {
      for (UIScene *scene in UIApplication.sharedApplication.connectedScenes) {
        if ([scene isKindOfClass:[UIWindowScene class]] &&
            scene.activationState != UISceneActivationStateUnattached)
        {
          window_.windowScene = (UIWindowScene *)scene;
          break;
        }
      }
    }

    window_.rootViewController = root_view_controller_;
    [window_ makeKeyAndVisible];

    updateDrawingSize();
    setDrawingContextType(type);
    updateDrawingContext();
    activateDrawingContext();
  }
}

GHOST_WindowIOS::~GHOST_WindowIOS()
{
  @autoreleasepool {
    releaseNativeHandles();

    metal_layer_ = nil;

    if (metal_view_ != nil) {
      [metal_view_ release];
      metal_view_ = nil;
    }
    if (root_view_controller_ != nil) {
      [root_view_controller_ release];
      root_view_controller_ = nil;
    }
    if (window_ != nil) {
      [window_ release];
      window_ = nil;
    }
  }
}

bool GHOST_WindowIOS::getValid() const
{
  return GHOST_Window::getValid() && window_ != nil && metal_view_ != nil && metal_layer_ != nil;
}

void *GHOST_WindowIOS::getOSWindow() const
{
  return (void *)window_;
}

void GHOST_WindowIOS::setTitle(const char *title)
{
  title_ = title ? title : "";
}

std::string GHOST_WindowIOS::getTitle() const
{
  return title_;
}

void GHOST_WindowIOS::getWindowBounds(GHOST_Rect &bounds) const
{
  const CGRect frame = window_.frame;
  bounds.l_ = int32_t(frame.origin.x);
  bounds.r_ = int32_t(frame.origin.x + frame.size.width);
  bounds.t_ = int32_t(frame.origin.y);
  bounds.b_ = int32_t(frame.origin.y + frame.size.height);
}

void GHOST_WindowIOS::getClientBounds(GHOST_Rect &bounds) const
{
  getWindowBounds(bounds);
}

GHOST_TSuccess GHOST_WindowIOS::setClientWidth(uint32_t width)
{
  GHOST_Rect bounds;
  getWindowBounds(bounds);
  return setClientSize(width, bounds.b_ - bounds.t_);
}

GHOST_TSuccess GHOST_WindowIOS::setClientHeight(uint32_t height)
{
  GHOST_Rect bounds;
  getWindowBounds(bounds);
  return setClientSize(bounds.r_ - bounds.l_, height);
}

GHOST_TSuccess GHOST_WindowIOS::setClientSize(uint32_t width, uint32_t height)
{
  CGRect frame = window_.frame;
  frame.size.width = CGFloat(width);
  frame.size.height = CGFloat(height);
  window_.frame = frame;
  metal_view_.frame = window_.bounds;
  updateDrawingSize();
  updateDrawingContext();
  return GHOST_kSuccess;
}

void GHOST_WindowIOS::screenToClient(int32_t inX,
                                     int32_t inY,
                                     int32_t &outX,
                                     int32_t &outY) const
{
  const CGRect frame = window_.frame;
  outX = inX - int32_t(frame.origin.x);
  outY = inY - int32_t(frame.origin.y);
}

void GHOST_WindowIOS::clientToScreen(int32_t inX,
                                     int32_t inY,
                                     int32_t &outX,
                                     int32_t &outY) const
{
  const CGRect frame = window_.frame;
  outX = int32_t(frame.origin.x) + inX;
  outY = int32_t(frame.origin.y) + inY;
}

GHOST_TWindowState GHOST_WindowIOS::getState() const
{
  return full_screen_ ? GHOST_kWindowStateFullScreen : GHOST_kWindowStateNormal;
}

GHOST_TSuccess GHOST_WindowIOS::setModifiedState(bool is_unsaved_changes)
{
  is_unsaved_changes_ = is_unsaved_changes;
  return GHOST_kSuccess;
}

GHOST_TSuccess GHOST_WindowIOS::setState(GHOST_TWindowState state)
{
  if (state == GHOST_kWindowStateFullScreen) {
    window_.frame = UIScreen.mainScreen.bounds;
    full_screen_ = true;
  }
  else {
    full_screen_ = false;
  }

  metal_view_.frame = window_.bounds;
  updateDrawingSize();
  updateDrawingContext();
  return GHOST_kSuccess;
}

GHOST_TSuccess GHOST_WindowIOS::setOrder(GHOST_TWindowOrder order)
{
  if (order == GHOST_kWindowOrderTop) {
    [window_ makeKeyAndVisible];
  }
  return GHOST_kSuccess;
}

GHOST_TSuccess GHOST_WindowIOS::hasCursorShape(GHOST_TStandardCursor /*cursor*/)
{
  return GHOST_kSuccess;
}

GHOST_TSuccess GHOST_WindowIOS::invalidate()
{
  [metal_view_ setNeedsLayout];
  notifyUpdate();
  return GHOST_kSuccess;
}

bool GHOST_WindowIOS::isDialog() const
{
  return is_dialog_;
}

void GHOST_WindowIOS::updateDrawingSize()
{
  const CGSize view_size = metal_view_.bounds.size;
  const CGFloat scale = window_.screen ? window_.screen.scale : UIScreen.mainScreen.scale;
  native_pixel_size_ = float(scale);
  metal_layer_.contentsScale = scale;
  metal_layer_.drawableSize = CGSizeMake(view_size.width * scale, view_size.height * scale);
}

void GHOST_WindowIOS::notifyActivate()
{
  system_ios_->handleWindowEvent(GHOST_kEventWindowActivate, this);
}

void GHOST_WindowIOS::notifyResize()
{
  system_ios_->handleWindowEvent(GHOST_kEventWindowSize, this);
}

void GHOST_WindowIOS::notifyUpdate()
{
  system_ios_->handleWindowEvent(GHOST_kEventWindowUpdate, this);
}

GHOST_Context *GHOST_WindowIOS::newDrawingContext(GHOST_TDrawingContextType type)
{
#ifdef WITH_METAL_BACKEND
  if (type == GHOST_kDrawingContextTypeMetal) {
    GHOST_Context *context = new GHOST_ContextMTL(want_context_params_, metal_view_, metal_layer_);
    if (context->initializeDrawingContext()) {
      return context;
    }
    delete context;
  }
#else
  (void)type;
#endif
  return nullptr;
}

GHOST_TSuccess GHOST_WindowIOS::setWindowCursorVisibility(bool /*visible*/)
{
  return GHOST_kSuccess;
}

GHOST_TSuccess GHOST_WindowIOS::setWindowCursorGrab(GHOST_TGrabCursorMode /*mode*/)
{
  return GHOST_kSuccess;
}

GHOST_TSuccess GHOST_WindowIOS::setWindowCursorShape(GHOST_TStandardCursor /*shape*/)
{
  return GHOST_kSuccess;
}

GHOST_TSuccess GHOST_WindowIOS::setWindowCustomCursorShape(const uint8_t * /*bitmap*/,
                                                           const uint8_t * /*mask*/,
                                                           const int /*size*/[2],
                                                           const int /*hot_spot*/[2],
                                                           bool /*can_invert_color*/)
{
  return GHOST_kFailure;
}
