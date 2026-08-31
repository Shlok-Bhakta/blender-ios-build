#!/usr/bin/env python3

from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]
POINTER_HEADER = REPOSITORY / "intern" / "ghost" / "intern" / "GHOST_IOSVirtualPointer.hh"
POINTER_STATE_HEADER = (
    REPOSITORY / "intern" / "ghost" / "intern" / "GHOST_IOSVirtualPointerState.hh"
)
POINTER_SOURCE = REPOSITORY / "intern" / "ghost" / "intern" / "GHOST_IOSVirtualPointer.mm"
WINDOW_SOURCE = REPOSITORY / "intern" / "ghost" / "intern" / "GHOST_WindowIOS.mm"
SYSTEM_SOURCE = REPOSITORY / "intern" / "ghost" / "intern" / "GHOST_SystemIOS.mm"
GHOST_CMAKE = REPOSITORY / "build_files" / "ios" / "cmake" / "ghost_ios.cmake"


class GhostVirtualPointerStateTests(unittest.TestCase):
    def test_pointer_state_supports_relative_absolute_and_warped_motion(self) -> None:
        harness = textwrap.dedent(
            r"""
            #include "GHOST_IOSVirtualPointerState.hh"

            #include <cassert>

            int main()
            {
              GHOST_IOSVirtualPointerState state;
              state.initialize(200.0, 100.0);
              assert(state.x() == 100.0);
              assert(state.y() == 50.0);

              state.beginRelative(900.0, 700.0);
              state.moveRelativeTo(908.0, 697.0);
              assert(state.x() == 108.0);
              assert(state.y() == 47.0);
              state.endRelative();

              /* Repositioning a finger must not move or click the Blender cursor. */
              state.beginRelative(5.0, 5.0);
              assert(state.x() == 108.0);
              assert(state.y() == 47.0);
              assert(!state.buttonDown(GHOST_IOSPointerButton::Left));
              state.moveRelativeTo(3.0, 9.0);
              assert(state.x() == 106.0);
              assert(state.y() == 51.0);
              state.endRelative();

              state.moveAbsolute(25.0, 30.0, GHOST_IOSPointerSource::Pencil);
              assert(state.x() == 25.0);
              assert(state.y() == 30.0);
              assert(!state.visible());

              state.setSource(GHOST_IOSPointerSource::Finger);
              assert(state.visible());
              assert(state.x() == 25.0);
              assert(state.y() == 30.0);

              state.warp(10.0, 12.0);
              state.beginRelative(999.0, 999.0);
              state.moveRelativeTo(1002.0, 1005.0);
              assert(state.x() == 13.0);
              assert(state.y() == 18.0);

              state.moveAbsolute(77.0, 44.0, GHOST_IOSPointerSource::Hardware);
              assert(state.x() == 77.0);
              assert(state.y() == 44.0);
              assert(state.visible());

              state.setButton(GHOST_IOSPointerButton::Left, true);
              assert(state.buttonDown(GHOST_IOSPointerButton::Left));
              state.setButton(GHOST_IOSPointerButton::Left, false);
              assert(!state.buttonDown(GHOST_IOSPointerButton::Left));

              state.setBlenderVisibility(false);
              assert(!state.visible());
              state.setBlenderVisibility(true);
              assert(state.visible());
              return 0;
            }
            """
        )

        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            source = temporary / "virtual_pointer_test.cc"
            executable = temporary / "virtual_pointer_test"
            source.write_text(harness)
            compile_result = subprocess.run(
                [
                    "xcrun",
                    "clang++",
                    "-std=c++17",
                    "-I",
                    str(POINTER_STATE_HEADER.parent),
                    str(source),
                    "-o",
                    str(executable),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(compile_result.returncode, 0, compile_result.stderr)
            subprocess.run([str(executable)], check=True)


class GhostVirtualPointerIntegrationTests(unittest.TestCase):
    def test_ios_build_owns_the_pointer_shim(self) -> None:
        cmake = GHOST_CMAKE.read_text()
        self.assertIn("intern/GHOST_IOSVirtualPointer.hh", cmake)
        self.assertIn("intern/GHOST_IOSVirtualPointer.mm", cmake)

    def test_finger_motion_is_relative_and_does_not_hold_a_button(self) -> None:
        source = WINDOW_SOURCE.read_text()
        handler = source[source.rindex("- (void)handlePan:") : source.rindex("- (void)handlePan2f:")]
        self.assertIn("moveRelativeTo", handler)
        self.assertIn("getScaledTouchPoint", handler)
        self.assertNotIn("LEFT_BUTTON_DOWN", handler)
        self.assertNotIn("LEFT_BUTTON_UP", handler)

    def test_finger_tap_clicks_without_repositioning_the_cursor(self) -> None:
        source = WINDOW_SOURCE.read_text()
        handler = source[source.rindex("- (void)handleTap:") : source.rindex("- (void)handleTripleTap:")]
        direct_branch = handler[handler.index("else {") :]
        self.assertIn("virtual_pointer->click(GHOST_kButtonMaskLeft", handler)
        self.assertNotIn("getScaledTouchPoint", direct_branch)
        self.assertNotIn("moveAbsolute", direct_branch)

    def test_double_tap_hold_has_an_explicit_left_drag_lifetime(self) -> None:
        source = WINDOW_SOURCE.read_text()
        self.assertIn("double_tap_drag_gesture_recognizer.numberOfTapsRequired = 1;", source)
        handler = source[
            source.rindex("- (void)handleDoubleTapDrag:") : source.rindex("- (void)handleMouseButtonTap:")
        ]
        self.assertIn("button(GHOST_kButtonMaskLeft, true", handler)
        self.assertIn("moveRelativeTo", handler)
        self.assertIn("button(GHOST_kButtonMaskLeft, false", handler)

    def test_two_finger_tap_is_right_click_at_virtual_cursor(self) -> None:
        source = WINDOW_SOURCE.read_text()
        handler = source[source.index("- (void)handleTap2F:") : source.index("- (void)handleTap3F:")]
        self.assertIn("click(GHOST_kButtonMaskRight", handler)
        self.assertNotIn("generateUndoRedoShortcut", handler)

    def test_pencil_and_hardware_pointer_feed_the_same_cursor(self) -> None:
        source = WINDOW_SOURCE.read_text()
        self.assertIn("handlePencilDrag:", source)
        self.assertIn("GHOST_IOSPointerSource::Pencil", source)
        self.assertIn("GHOST_IOSPointerSource::Hardware", source)
        self.assertIn("moveAbsolute", source)

    def test_system_cursor_polling_and_warp_use_the_pointer_shim(self) -> None:
        source = SYSTEM_SOURCE.read_text()
        self.assertIn("virtual_pointer_->getCursorPosition", source)
        self.assertIn("virtual_pointer_->warp", source)
        self.assertIn("virtual_pointer_->getButtons", source)

    def test_virtual_pointer_advertises_real_cursor_warp_support(self) -> None:
        source = SYSTEM_SOURCE.read_text()
        capabilities = source[
            source.index("GHOST_TCapabilityFlag GHOST_SystemIOS::getCapabilities()") :
            source.index("#pragma mark Event handlers")
        ]
        self.assertIn("GHOST_kCapabilityCursorWarp", capabilities)

    def test_hidden_modal_grab_restores_the_virtual_cursor(self) -> None:
        source = WINDOW_SOURCE.read_text()
        grab = source[
            source.index("GHOST_TSuccess GHOST_WindowIOS::setWindowCursorGrab") :
            source.index("GHOST_TSuccess GHOST_WindowIOS::setWindowCursorShape")
        ]
        self.assertIn("cursor_grab_init_pos_", grab)
        self.assertIn("system_ios_->getCursorPosition", grab)
        self.assertIn("system_ios_->setCursorPosition", grab)
        self.assertIn("cursor_grab_ == GHOST_kGrabHide", grab)

    def test_cursor_is_rendered_and_the_system_pointer_is_suppressed(self) -> None:
        source = POINTER_SOURCE.read_text()
        self.assertIn("CAShapeLayer", source)
        self.assertIn("hiddenPointerStyle", source)
        self.assertNotIn("node editor", source.lower())
        self.assertNotIn("space_node", source)


if __name__ == "__main__":
    unittest.main()
