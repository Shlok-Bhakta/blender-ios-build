#!/usr/bin/env python3

from pathlib import Path
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]
WINDOW_SOURCE = REPOSITORY / "intern" / "ghost" / "intern" / "GHOST_WindowIOS.mm"
ACCESS_HEADER = REPOSITORY / "intern" / "ghost" / "intern" / "GHOST_IOSFileAccess.hh"
ACCESS_SOURCE = REPOSITORY / "intern" / "ghost" / "intern" / "GHOST_IOSFileAccess.mm"
FILE_MENU_SOURCE = (
    REPOSITORY / "source" / "blender" / "editors" / "space_file" / "fsmenu_system_ios.mm"
)
GHOST_CMAKE = REPOSITORY / "build_files" / "ios" / "cmake" / "ghost_ios.cmake"
PLATFORM_CMAKE = REPOSITORY / "build_files" / "ios" / "cmake" / "platform_ios.cmake"


class GhostFileAccessTests(unittest.TestCase):
    def test_file_access_ui_lives_in_an_ios_ghost_shim(self) -> None:
        window_source = WINDOW_SOURCE.read_text()
        access_source = ACCESS_SOURCE.read_text()
        cmake = GHOST_CMAKE.read_text()

        self.assertIn("GHOST_IOSFileAccess_createControls", window_source)
        self.assertIn("GHOST_IOSFileAccess_destroyControls", window_source)
        self.assertNotIn("UIDocumentPickerViewController", window_source)
        self.assertNotIn("startAccessingSecurityScopedResource", window_source)
        self.assertIn("intern/GHOST_IOSFileAccess.hh", cmake)
        self.assertIn("intern/GHOST_IOSFileAccess.mm", cmake)
        self.assertIn("UIDocumentPickerViewController", access_source)
        self.assertIn("-framework UniformTypeIdentifiers", PLATFORM_CMAKE.read_text())

    def test_control_only_appears_on_the_file_browser_window(self) -> None:
        window_source = WINDOW_SOURCE.read_text()
        access_source = ACCESS_SOURCE.read_text()

        self.assertIn('strcmp(window_title, "Blender File View")', access_source)
        self.assertIn('strcmp(window_title, "File Browser")', access_source)
        self.assertIn('accessibilityIdentifier = @"blender_file_browser_add_location";', access_source)
        self.assertIn('systemImageNamed:@"folder.badge.plus"', access_source)
        set_title = window_source[
            window_source.index("void GHOST_WindowIOS::setTitle") : window_source.index(
                "std::string GHOST_WindowIOS::getTitle"
            )
        ]
        self.assertIn("updateFileAccessControls", set_title)

    def test_control_is_a_small_circle_immediately_left_of_close(self) -> None:
        access_source = ACCESS_SOURCE.read_text()

        self.assertIn("glassButtonConfiguration", access_source)
        self.assertIn("constraintEqualToConstant:44.0f", access_source)
        self.assertIn("constraintEqualToAnchor:close_button.leadingAnchor", access_source)
        self.assertIn("constraintEqualToAnchor:close_button.centerYAnchor", access_source)

    def test_control_opens_the_system_folder_picker_without_copying(self) -> None:
        access_source = ACCESS_SOURCE.read_text()

        self.assertIn("initForOpeningContentTypes:@[ UTTypeFolder ]", access_source)
        self.assertIn("asCopy:NO", access_source)
        self.assertIn("allowsMultipleSelection = YES", access_source)

        cancel = access_source[
            access_source.rindex("documentPickerWasCancelled") : access_source.rindex(
                "- (BOOL)containsView"
            )
        ]
        self.assertIn("dismissViewControllerAnimated:YES", cancel)

    def test_control_touches_do_not_leak_into_blender(self) -> None:
        window_source = WINDOW_SOURCE.read_text()

        self.assertIn("GHOST_IOSFileAccess_containsView", window_source)

    def test_selected_directories_are_persisted_as_ios_bookmarks(self) -> None:
        file_menu_source = FILE_MENU_SOURCE.read_text()

        self.assertIn("NSURLBookmarkCreationMinimalBookmark", file_menu_source)
        self.assertIn("URLByResolvingBookmarkData", file_menu_source)
        self.assertIn("startAccessingSecurityScopedResource", file_menu_source)
        self.assertIn("stopAccessingSecurityScopedResource", file_menu_source)
        self.assertIn("NSUserDefaults", file_menu_source)

    def test_selected_directories_appear_as_blender_system_bookmarks(self) -> None:
        file_menu_source = FILE_MENU_SOURCE.read_text()

        self.assertIn("FS_CATEGORY_SYSTEM_BOOKMARKS", file_menu_source)
        self.assertIn("GHOST_IOSFileLocationDidGrantAccess", file_menu_source)
        self.assertIn("WM_main_add_notifier", file_menu_source)


if __name__ == "__main__":
    unittest.main()
