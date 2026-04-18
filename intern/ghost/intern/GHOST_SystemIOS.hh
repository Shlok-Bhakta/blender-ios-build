/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup GHOST
 * Declaration of GHOST_SystemIOS class.
 */

#pragma once

#ifndef __APPLE__
#  error Apple only!
#endif

#include "GHOST_System.hh"

class GHOST_WindowIOS;

class GHOST_SystemIOS : public GHOST_System {
 public:
  GHOST_SystemIOS();
  ~GHOST_SystemIOS() override;

  uint64_t getMilliSeconds() const override;

  uint8_t getNumDisplays() const override;
  void getMainDisplayDimensions(uint32_t &width, uint32_t &height) const override;
  void getAllDisplayDimensions(uint32_t &width, uint32_t &height) const override;

  GHOST_IWindow *createWindow(const char *title,
                              int32_t left,
                              int32_t top,
                              uint32_t width,
                              uint32_t height,
                              GHOST_TWindowState state,
                              GHOST_GPUSettings gpu_settings,
                              const bool exclusive = false,
                              const bool is_dialog = false,
                              const GHOST_IWindow *parent_window = nullptr) override;

  GHOST_IContext *createOffscreenContext(GHOST_GPUSettings gpu_settings) override;
  GHOST_TSuccess disposeContext(GHOST_IContext *context) override;
  GHOST_IWindow *getWindowUnderCursor(int32_t x, int32_t y) override;

  bool processEvents(bool waitForEvent) override;

  GHOST_TSuccess getCursorPosition(int32_t &x, int32_t &y) const override;
  GHOST_TSuccess setCursorPosition(int32_t x, int32_t y) override;
  GHOST_TSuccess getModifierKeys(GHOST_ModifierKeys &keys) const override;
  GHOST_TSuccess getButtons(GHOST_Buttons &buttons) const override;
  GHOST_TCapabilityFlag getCapabilities() const override;
  char *getClipboard(bool selection) const override;
  void putClipboard(const char *buffer, bool selection) const override;

  GHOST_TSuccess handleWindowEvent(GHOST_TEventType event_type, GHOST_WindowIOS *window);

 protected:
  GHOST_TSuccess init() override;

 private:
  bool external_event_processed_;
};
