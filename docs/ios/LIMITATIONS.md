# Blender iOS limitations

The port currently has infrastructure only. No iOS configure, link, bundle,
launch, rendering, interaction, performance, or physical-device claim has been
proven yet.

Until the Workbench first-pixel gate is green, the reduced profile keeps Cycles,
OSL, USD, OpenVDB, Embree, OpenImageDenoise, complex media codecs, and optional
services out of the critical path. Features are enabled one at a time under a
named smoke test.

The unsigned device output is a future handoff format. It cannot run on a
physical iPad before owner-controlled signing and provisioning.

