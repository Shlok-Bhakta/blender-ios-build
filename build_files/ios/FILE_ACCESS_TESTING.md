# File location regression tests

The folder button must return control to Blender after a selection, even when a
Files provider stalls during bookmark creation or restoration. Repeated grants
must produce one System entry, and saved locations must return after relaunch.
The temporary security scope must be claimed during the picker delegate callback
before bookmark and provider work moves to a worker queue.
The native picker uses Apple's documented single-directory configuration. The
simulator reproduction separately times out if tapping Open never enters the
delegate, so successful post-selection work cannot hide a stuck Files sheet.

Run the host suite on macOS:

```sh
python3 -m unittest discover -s build_files/ios/tests -p 'test_*.py'
```

`test_file_access_runtime.py` compiles the production `fsmenu_system_ios.mm` shim
against Foundation. It uses real temporary folders, NSURL bookmarks and isolated
NSUserDefaults suites. It pauses bookmark creation or resolution, requires a
responsive main queue, refreshes the menu while paused, then checks persistence,
duplicate grants and malformed saved data. Blender's menu and notifier functions
are test substitutes that reject calls from a worker thread.

Set `FMT_INCLUDE_DIR` if the fmt headers are outside
`lib/macos_arm64/fmt/include`. CI uses its harvested iOS dependency prefix and
runs these tests before the full app build.

For the full app, boot an iPhone or iPad simulator, build the simulator app, then:

```sh
python3 build_files/ios/simulator_file_access.py \
  --app /path/to/Blender.app \
  --output /tmp/blender-file-access \
  --slow-provider
```

Use `--device <UDID>` to select one booted device. Without that argument, the
script runs each booted iPhone and iPad sequentially. Omit `--slow-provider` to
exercise ordinary provider timing.

The script starts from a clean app container and creates a folder with 90
top-level items and nested directories in Files' local storage outside Blender's
sandbox. Its test-only dylib sets the native picker's starting directory, records
entry into the picker callback, records that the selected URL's security scope is
claimed on the main thread during that callback, and, when requested, holds the
real NSURL bookmark operation until the host releases it. Nothing in the
production app loads this dylib. Maestro taps the real folder button and native
Open button three times, then closes the file browser. A bpy timer verifies fresh
main-loop ticks and one System entry. A loopback HTTP probe asserts those ticks
inside the Maestro flow, before its runner can background the app. The script
then verifies successful restoration after terminating and relaunching the app.
Failed runs preserve logs and state.

The iOS 26.5 remote Files view does not expose its Open button reliably to XCTest.
The flow uses a coordinate fallback for that button on iPhone landscape and iPad
portrait; Blender's controls use accessibility identifiers. The generated flow
requires the script's fixture and should not be run alone.

Live iCloud and network-provider access still needs an account configured on a
real device. The controlled stall covers responsiveness independently of provider
latency; it does not claim to authenticate or exercise those services.
