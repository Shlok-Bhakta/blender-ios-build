# Repository guidance

Keep iOS-specific behavior in separate shim files; upstream Blender files should contain only the smallest necessary hook/call into those shims, with no iOS implementation logic unless unavoidable.
