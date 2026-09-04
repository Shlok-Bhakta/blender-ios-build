/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup GHOST
 * Native iOS file-location picker controls.
 */

#pragma once

#ifdef __OBJC__

@class NSObject;
@class UIButton;
@class UIView;
@class UIViewController;

NSObject *GHOST_IOSFileAccess_createControls(UIView *input_view,
                                             UIViewController *view_controller,
                                             UIButton *close_button,
                                             const char *window_title);
void GHOST_IOSFileAccess_destroyControls(NSObject *controls);
bool GHOST_IOSFileAccess_containsView(NSObject *controls, UIView *view);

#endif
