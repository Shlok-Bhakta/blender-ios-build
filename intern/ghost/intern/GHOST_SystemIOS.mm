/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "GHOST_SystemIOS.hh"

#include "GHOST_Event.hh"
#include "GHOST_TimerManager.hh"
#include "GHOST_WindowIOS.hh"
#include "GHOST_WindowManager.hh"

#ifdef WITH_METAL_BACKEND
#  include "GHOST_ContextMTL.hh"
#endif

#import <UIKit/UIKit.h>

GHOST_SystemIOS::GHOST_SystemIOS() : external_event_processed_(false) {}

GHOST_SystemIOS::~GHOST_SystemIOS() = default;

GHOST_TSuccess GHOST_SystemIOS::init()
{
  return GHOST_System::init();
}

uint64_t GHOST_SystemIOS::getMilliSeconds() const
{
  return uint64_t([[NSProcessInfo processInfo] systemUptime] * 1000.0);
}

uint8_t GHOST_SystemIOS::getNumDisplays() const
{
  return 1;
}

void GHOST_SystemIOS::getMainDisplayDimensions(uint32_t &width, uint32_t &height) const
{
  const CGRect bounds = UIScreen.mainScreen.bounds;
  width = uint32_t(bounds.size.width);
  height = uint32_t(bounds.size.height);
}

void GHOST_SystemIOS::getAllDisplayDimensions(uint32_t &width, uint32_t &height) const
{
  getMainDisplayDimensions(width, height);
}

GHOST_IWindow *GHOST_SystemIOS::createWindow(const char *title,
                                             int32_t left,
                                             int32_t top,
                                             uint32_t width,
                                             uint32_t height,
                                             GHOST_TWindowState state,
                                             GHOST_GPUSettings gpu_settings,
                                             const bool /*exclusive*/,
                                             const bool is_dialog,
                                             const GHOST_IWindow * /*parent_window*/)
{
  const GHOST_ContextParams context_params = GHOST_CONTEXT_PARAMS_FROM_GPU_SETTINGS(gpu_settings);

  if (state == GHOST_kWindowStateFullScreen || width == 0 || height == 0) {
    getMainDisplayDimensions(width, height);
    left = 0;
    top = 0;
  }

  GHOST_IWindow *window = new GHOST_WindowIOS(this,
                                              title,
                                              left,
                                              top,
                                              width,
                                              height,
                                              state,
                                              gpu_settings.context_type,
                                              context_params,
                                              is_dialog);

  if (!window->getValid()) {
    delete window;
    return nullptr;
  }

  window_manager_->addWindow(window);
  window_manager_->setActiveWindow(window);
  pushEvent(std::make_unique<GHOST_Event>(getMilliSeconds(), GHOST_kEventWindowActivate, window));
  pushEvent(std::make_unique<GHOST_Event>(getMilliSeconds(), GHOST_kEventWindowSize, window));
  return window;
}

GHOST_IContext *GHOST_SystemIOS::createOffscreenContext(GHOST_GPUSettings gpu_settings)
{
  const GHOST_ContextParams context_params_offscreen =
      GHOST_CONTEXT_PARAMS_FROM_GPU_SETTINGS_OFFSCREEN(gpu_settings);

#ifdef WITH_METAL_BACKEND
  if (gpu_settings.context_type == GHOST_kDrawingContextTypeMetal) {
    GHOST_Context *context = new GHOST_ContextMTL(context_params_offscreen, nil, nil);
    if (context->initializeDrawingContext()) {
      return context;
    }
    delete context;
  }
#else
  (void)context_params_offscreen;
  (void)gpu_settings;
#endif

  return nullptr;
}

GHOST_TSuccess GHOST_SystemIOS::disposeContext(GHOST_IContext *context)
{
  delete context;
  return GHOST_kSuccess;
}

GHOST_IWindow *GHOST_SystemIOS::getWindowUnderCursor(int32_t /*x*/, int32_t /*y*/)
{
  return window_manager_ ? window_manager_->getActiveWindow() : nullptr;
}

bool GHOST_SystemIOS::processEvents(bool waitForEvent)
{
  bool any_processed = false;
  GHOST_TimerManager *timer_manager = getTimerManager();

  if (timer_manager->fireTimers(getMilliSeconds())) {
    any_processed = true;
  }

  if (waitForEvent && !any_processed && !external_event_processed_) {
    return false;
  }

  if (external_event_processed_) {
    external_event_processed_ = false;
    return true;
  }

  return any_processed;
}

GHOST_TSuccess GHOST_SystemIOS::getCursorPosition(int32_t &x, int32_t &y) const
{
  x = 0;
  y = 0;
  return GHOST_kFailure;
}

GHOST_TSuccess GHOST_SystemIOS::setCursorPosition(int32_t /*x*/, int32_t /*y*/)
{
  return GHOST_kFailure;
}

GHOST_TSuccess GHOST_SystemIOS::getModifierKeys(GHOST_ModifierKeys &keys) const
{
  keys.clear();
  return GHOST_kSuccess;
}

GHOST_TSuccess GHOST_SystemIOS::getButtons(GHOST_Buttons &buttons) const
{
  buttons.clear();
  return GHOST_kSuccess;
}

GHOST_TCapabilityFlag GHOST_SystemIOS::getCapabilities() const
{
  return GHOST_TCapabilityFlag(0);
}

char *GHOST_SystemIOS::getClipboard(bool /*selection*/) const
{
  return nullptr;
}

void GHOST_SystemIOS::putClipboard(const char * /*buffer*/, bool /*selection*/) const {}

GHOST_TSuccess GHOST_SystemIOS::handleWindowEvent(GHOST_TEventType event_type,
                                                  GHOST_WindowIOS *window)
{
  if (!validWindow(window)) {
    return GHOST_kFailure;
  }

  switch (event_type) {
    case GHOST_kEventWindowActivate:
      window_manager_->setActiveWindow(window);
      break;
    case GHOST_kEventWindowSize:
      window->updateDrawingSize();
      window->updateDrawingContext();
      break;
    case GHOST_kEventWindowUpdate:
      window->updateDrawingContext();
      break;
    default:
      break;
  }

  pushEvent(std::make_unique<GHOST_Event>(getMilliSeconds(), event_type, window));
  external_event_processed_ = true;
  return GHOST_kSuccess;
}
