/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup GHOST
 * Declaration of GHOST_WindowIOS class.
 */

#pragma once

#ifndef __APPLE__
#  error Apple only!
#endif

#include "GHOST_Window.hh"

#include <string>

@class CAMetalLayer;
@class UIView;
@class UIViewController;
@class UIWindow;

class GHOST_SystemIOS;

class GHOST_WindowIOS : public GHOST_Window {
 public:
  GHOST_WindowIOS(GHOST_SystemIOS *systemIOS,
                  const char *title,
                  int32_t left,
                  int32_t top,
                  uint32_t width,
                  uint32_t height,
                  GHOST_TWindowState state,
                  GHOST_TDrawingContextType type,
                  const GHOST_ContextParams &context_params,
                  bool is_dialog);

  ~GHOST_WindowIOS() override;

  bool getValid() const override;
  void *getOSWindow() const override;

  void setTitle(const char *title) override;
  std::string getTitle() const override;

  void getWindowBounds(GHOST_Rect &bounds) const override;
  void getClientBounds(GHOST_Rect &bounds) const override;

  GHOST_TSuccess setClientWidth(uint32_t width) override;
  GHOST_TSuccess setClientHeight(uint32_t height) override;
  GHOST_TSuccess setClientSize(uint32_t width, uint32_t height) override;

  void screenToClient(int32_t inX, int32_t inY, int32_t &outX, int32_t &outY) const override;
  void clientToScreen(int32_t inX, int32_t inY, int32_t &outX, int32_t &outY) const override;

  GHOST_TWindowState getState() const override;
  GHOST_TSuccess setModifiedState(bool is_unsaved_changes) override;
  GHOST_TSuccess setState(GHOST_TWindowState state) override;
  GHOST_TSuccess setOrder(GHOST_TWindowOrder order) override;
  GHOST_TSuccess hasCursorShape(GHOST_TStandardCursor cursor) override;
  GHOST_TSuccess invalidate() override;

  bool isDialog() const override;

  void updateDrawingSize();
  void notifyActivate();
  void notifyResize();
  void notifyUpdate();

 protected:
  GHOST_Context *newDrawingContext(GHOST_TDrawingContextType type) override;
  GHOST_TSuccess setWindowCursorVisibility(bool visible) override;
  GHOST_TSuccess setWindowCursorGrab(GHOST_TGrabCursorMode mode) override;
  GHOST_TSuccess setWindowCursorShape(GHOST_TStandardCursor shape) override;
  GHOST_TSuccess setWindowCustomCursorShape(const uint8_t *bitmap,
                                            const uint8_t *mask,
                                            const int size[2],
                                            const int hot_spot[2],
                                            bool can_invert_color) override;

 private:
  GHOST_SystemIOS *system_ios_;
  UIWindow *window_;
  UIViewController *root_view_controller_;
  UIView *metal_view_;
  CAMetalLayer *metal_layer_;
  std::string title_;
  bool is_dialog_;
};
