# Repository guidance

Keep iOS-specific behavior in separate shim files; upstream Blender files should contain only the smallest necessary hook/call into those shims, with no iOS implementation logic unless unavoidable.

## Change workflow

Use this workflow for every feature, fix, or maintenance change in this port.

### Start from the current stack head

- Inspect the open pull requests before branching. Confirm the latest stacked PR, its head branch, its base branch, and its green commit.
- Branch from that exact head commit. Keep one change per stacked PR.
- Use a `story/`, `feat/`, or `refactor/` branch. The iOS preview workflow ignores other branch prefixes.
- When opening the PR, base the new PR on the previous PR branch, not Blender's default branch. State the parent PR in the description so reviewers can follow the stack.
- Do not create a GitHub issue unless the user asks for one. A normal change request can go straight into a branch and PR.
- Preserve unrelated work in the checkout. Stop if the intended edit overlaps unexplained local changes.

### Prove the behavior before fixing it

- Turn the reported behavior into a deterministic reproduction. Use the highest honest test layer available: device or simulator UI for interaction and lifecycle bugs, integration tests for system boundaries, and unit tests for isolated logic.
- Observe the regression fail before changing production code. A passing test written against broken code does not cover the bug.
- Source-text assertions are supporting checks. They do not replace a running reproduction for input, window lifecycle, rendering, threading, memory, or other user-visible behavior.
- Match the user's complete sequence, including repeated actions and timing-sensitive state. A test of the first open and close does not cover a bug that appears on the second close.
- Assert the final outcome. For example, require fresh main-loop ticks or a third successful window open instead of checking only that a callback exists.
- Keep reusable simulator or device reproductions in `build_files/ios/` and give their pure logic normal unit coverage under `build_files/ios/tests/`.

### Make the smallest isolated fix

- Keep UIKit, touch, Pencil, paths, clipboard, keyboard, and iOS window behavior inside iOS GHOST files or other iOS-owned files.
- Do not patch individual Blender editors when normal GHOST events or window state can express the behavior.
- Fix the state owner that is wrong. Do not hide a lifecycle bug by forcing a cursor, view, or flag back on at the end.
- Preserve working behavior outside the reproduction. Avoid unrelated cleanup in a fix PR.

### Verify red, green, and the build

- Run the same reproduction again after the fix and confirm that it passes.
- Run focused tests while iterating, then the complete `build_files/ios/tests` suite.
- Compile every changed Objective-C++ or C++ unit. Link the full simulator or device app when the change crosses GHOST, GPU, rendering, window, or application lifecycle code.
- Run the on-device or simulator path when interaction feel or platform lifecycle is the acceptance criterion. CI compilation alone cannot prove those behaviors.
- Check `git diff --check` and review the final diff before committing.

### Open and finish the stacked PR

- Commit and push only after local verification passes. Open a ready-for-review PR against the previous stack branch.
- Include the parent PR, the observed red failure, the fix, exact test commands, and results in the PR description.
- Fetch the new Actions run once, then wait with one silent watcher:

  ```sh
  gh run watch <run-id> --repo <owner/repo> --interval 1800 --exit-status >/dev/null 2>&1
  ```

- Do not poll CI in a loop. If the watcher fails, inspect the failed job once, fix a real failure, and attach one new watcher to the replacement run. Rerun a failed job unchanged only when the logs point to runner or GitHub infrastructure trouble.
- Do not hand off until CI is green. Report the PR, commit, test evidence, build result, and install artifact when the workflow publishes one.
