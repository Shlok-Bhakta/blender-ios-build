/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup GHOST
 * Native iOS file-location picker controls.
 */

#include "GHOST_IOSFileAccess.hh"

#import <QuartzCore/QuartzCore.h>
#import <UIKit/UIKit.h>
#import <UniformTypeIdentifiers/UniformTypeIdentifiers.h>

#include <cstring>

static NSString *const GHOST_IOSFileLocationDidGrantAccess =
    @"GHOST_IOSFileLocationDidGrantAccess";

@interface GHOSTIOSFileAccessControls : NSObject <UIDocumentPickerDelegate>
{
  UIButton *button_;
  UIViewController *view_controller_;
  UIDocumentPickerViewController *picker_;
}

- (instancetype)initWithInputView:(UIView *)input_view
                   viewController:(UIViewController *)view_controller
                      closeButton:(UIButton *)close_button;
- (BOOL)containsView:(UIView *)view;
- (void)invalidate;

@end

@implementation GHOSTIOSFileAccessControls

- (instancetype)initWithInputView:(UIView *)input_view
                   viewController:(UIViewController *)view_controller
                      closeButton:(UIButton *)close_button
{
  self = [super init];
  if (self == nil) {
    return nil;
  }

  view_controller_ = view_controller;
  picker_ = nil;
  button_ = [[UIButton buttonWithType:UIButtonTypeSystem] retain];
  button_.translatesAutoresizingMaskIntoConstraints = NO;
  button_.accessibilityLabel = @"Add file location";
  button_.accessibilityHint = @"Choose a folder that Blender can access";
  button_.accessibilityIdentifier = @"blender_file_browser_add_location";
  button_.tintColor = UIColor.whiteColor;

  UIImageSymbolConfiguration *symbol_configuration = [UIImageSymbolConfiguration
      configurationWithPointSize:14.0f
                          weight:UIImageSymbolWeightSemibold];
  UIImage *image = [UIImage systemImageNamed:@"folder.badge.plus"
                           withConfiguration:symbol_configuration];

  if (@available(iOS 26.0, *)) {
    UIButtonConfiguration *configuration = [UIButtonConfiguration glassButtonConfiguration];
    configuration.cornerStyle = UIButtonConfigurationCornerStyleCapsule;
    configuration.baseForegroundColor = UIColor.whiteColor;
    configuration.image = image;
    button_.configuration = configuration;
  }
  else {
    button_.backgroundColor = [UIColor colorWithWhite:0.0f alpha:0.65f];
    button_.layer.cornerRadius = 22.0f;
    [button_ setImage:image forState:UIControlStateNormal];
  }

  [button_ addTarget:self
                action:@selector(showFolderPicker)
      forControlEvents:UIControlEventTouchUpInside];
  [input_view addSubview:button_];

  [NSLayoutConstraint activateConstraints:@[
    [button_.widthAnchor constraintEqualToConstant:44.0f],
    [button_.heightAnchor constraintEqualToConstant:44.0f],
    [button_.centerYAnchor constraintEqualToAnchor:close_button.centerYAnchor],
    [button_.trailingAnchor constraintEqualToAnchor:close_button.leadingAnchor constant:-8.0f],
  ]];

  return self;
}

- (void)showFolderPicker
{
  if (picker_ != nil || view_controller_ == nil || view_controller_.presentedViewController != nil)
  {
    return;
  }

  picker_ = [[UIDocumentPickerViewController alloc] initForOpeningContentTypes:@[ UTTypeFolder ]
                                                                        asCopy:NO];
  picker_.delegate = self;
  picker_.allowsMultipleSelection = YES;
  picker_.modalPresentationStyle = UIModalPresentationFormSheet;
  [view_controller_ presentViewController:picker_ animated:YES completion:nil];
}

- (void)documentPicker:(UIDocumentPickerViewController *)controller
    didPickDocumentsAtURLs:(NSArray<NSURL *> *)urls
{
  for (NSURL *url in urls) {
    if (url.isFileURL) {
      [[NSNotificationCenter defaultCenter]
          postNotificationName:GHOST_IOSFileLocationDidGrantAccess
                        object:url];
    }
  }

  if (controller == picker_) {
    picker_.delegate = nil;
    [picker_ dismissViewControllerAnimated:YES completion:nil];
    [picker_ release];
    picker_ = nil;
  }
}

- (void)documentPickerWasCancelled:(UIDocumentPickerViewController *)controller
{
  if (controller == picker_) {
    picker_.delegate = nil;
    [picker_ dismissViewControllerAnimated:YES completion:nil];
    [picker_ release];
    picker_ = nil;
  }
}

- (BOOL)containsView:(UIView *)view
{
  return button_ != nil && (view == button_ || [view isDescendantOfView:button_]);
}

- (void)invalidate
{
  if (picker_ != nil) {
    picker_.delegate = nil;
    [picker_ dismissViewControllerAnimated:NO completion:nil];
    [picker_ release];
    picker_ = nil;
  }

  if (button_ != nil) {
    [button_ removeTarget:self
                   action:@selector(showFolderPicker)
         forControlEvents:UIControlEventTouchUpInside];
    [button_ removeFromSuperview];
    [button_ release];
    button_ = nil;
  }
  view_controller_ = nil;
}

- (void)dealloc
{
  [self invalidate];
  [super dealloc];
}

@end

NSObject *GHOST_IOSFileAccess_createControls(UIView *input_view,
                                             UIViewController *view_controller,
                                             UIButton *close_button,
                                             const char *window_title)
{
  const bool is_file_browser = window_title != nullptr &&
                               (strcmp(window_title, "Blender File View") == 0 ||
                                strcmp(window_title, "File Browser") == 0);
  if (input_view == nil || view_controller == nil || close_button == nil || !is_file_browser) {
    return nil;
  }

  return [[GHOSTIOSFileAccessControls alloc] initWithInputView:input_view
                                                viewController:view_controller
                                                   closeButton:close_button];
}

void GHOST_IOSFileAccess_destroyControls(NSObject *controls)
{
  if (controls == nil) {
    return;
  }
  GHOSTIOSFileAccessControls *file_controls = (GHOSTIOSFileAccessControls *)controls;
  [file_controls invalidate];
  [file_controls release];
}

bool GHOST_IOSFileAccess_containsView(NSObject *controls, UIView *view)
{
  if (controls == nil || view == nil) {
    return false;
  }
  return [(GHOSTIOSFileAccessControls *)controls containsView:view] == YES;
}
