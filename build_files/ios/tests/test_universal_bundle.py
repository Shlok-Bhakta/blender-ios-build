# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

from pathlib import Path
import plistlib
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]
PRODUCT_INFO_PLIST = REPOSITORY / "release" / "ios" / "Blender.app" / "Info.plist"

IPHONE_FAMILY = 1
IPAD_FAMILY = 2
IPAD_ORIENTATIONS = {
    "UIInterfaceOrientationLandscapeLeft",
    "UIInterfaceOrientationLandscapeRight",
    "UIInterfaceOrientationPortrait",
    "UIInterfaceOrientationPortraitUpsideDown",
}


class UniversalBundlePlistTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with PRODUCT_INFO_PLIST.open("rb") as handle:
            cls.plist = plistlib.load(handle)

    def test_bundle_id_is_the_single_ios_product(self) -> None:
        self.assertEqual(
            self.plist["CFBundleIdentifier"],
            "org.blenderfoundation.blender.ios",
        )

    def test_declares_iphone_and_ipad_device_families(self) -> None:
        families = {int(value) for value in self.plist["UIDeviceFamily"]}
        self.assertEqual(families, {IPHONE_FAMILY, IPAD_FAMILY})

    def test_ipad_orientations_include_portrait_and_landscape(self) -> None:
        orientations = set(self.plist["UISupportedInterfaceOrientations~ipad"])
        self.assertEqual(orientations, IPAD_ORIENTATIONS)

    def test_iphone_orientations_remain_landscape_only(self) -> None:
        orientations = set(self.plist["UISupportedInterfaceOrientations"])
        self.assertEqual(
            orientations,
            {
                "UIInterfaceOrientationLandscapeLeft",
                "UIInterfaceOrientationLandscapeRight",
            },
        )
