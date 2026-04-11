# AGENTS.md

## Goal

- pass Apple `ios-simulator` deps step
- stop when iOS deps green
- do not chase later app/ghost issues

## Rules

- use GitHub Actions as truth
- small fix first blocker
- deps + CI plumbing only
- main gate: `.github/workflows/apple-port-build.yml`
- debug loop: `.github/workflows/apple-port-debug.yml`
- use subagents often
- push with `git push --no-verify` when CI loop active
- do not batch speculative fixes
- if user says pause polling, pause polling

## Loop

1. inspect latest run
2. find first real blocker
3. smallest fix
4. commit
5. push `--no-verify`
6. poll
7. repeat

## Commands

Main gate:

```bash
gh run list --workflow "Apple Port Build" --branch main-iosport --limit 10
gh run view <run_id>
gh run view <run_id> --log-failed
POLL_INTERVAL_SECONDS=30 .github/poll-build-run.sh "Apple Port Build" "main-iosport"
```

Single dep debug:

```bash
gh workflow run "Apple Port Debug" -f apple_target_device=ios-simulator -f dep_target=external_<dep> -f build_host_tools=false
gh run list --workflow "Apple Port Debug" --branch main-iosport --limit 10
gh run view <run_id>
gh run view <run_id> --log-failed
```

Notes:

- prefer poll script over `gh run watch`
- if logs truncate, use subagent
- `GNUmakefile` auto-detects cores when `NPROCS` omitted

## Heuristics

- Apple cross dep fail: first check host CLI/tests
- newer CMake reject upstream: prefer small shared compat fix
- nested CMake wrong target: verify `CMAKE_SYSTEM_NAME`, `CMAKE_SYSTEM_PROCESSOR`, `CMAKE_OSX_ARCHITECTURES`, sysroot, min-version flags
- prefer shared fix only when safe; else per-dep fix
- old `port-patches/done/` need behavior match, not text match

## Current State

Progress moved downstream before latest pause:

- `openal -> png -> jpeg -> blosc -> deflate -> brotli -> alembic -> nasm -> lzma -> tiff -> ffi -> sqlite -> openpgl -> aom -> embree -> gmp -> fftw -> lame -> opus -> x264 -> x265 -> flac -> manifold`

Already landed in branch:

- Apple dep target flags fixed
- workflow quoting fixed
- nested Apple processor propagation fixed
- `-DCMAKE_POLICY_VERSION_MINIMUM=3.5` added
- Brotli Apple cross fix
- Alembic Imath fix
- NASM host-tool fix
- LZMA / TIFF / FFI / SQLite Apple fixes
- GMP / FFTW / LAME / Opus Apple cross configure fixes
- x264 asm off for Apple cross
- x265 Apple iOS patch + CMake/C++17 fixes
- FLAC cross configure + Ogg wiring
- manifold TBB package discovery fix committed/pushed: add `TBB_DIR`

Latest inspected failure:

- run `24286736627`
- first blocker: `external_manifold`
- error: `Package 'tbb' not found`
- likely fixed by commit `161072de61b` (`Fix manifold TBB package discovery`)

Current local-only work:

- new manual debug workflow: `.github/workflows/apple-port-debug.yml`
- main workflow now uses auto core detect, no forced `NPROCS=3`
- `.gitignore` exception for `.github/workflows/*.yml`
- this file trimmed for token save

## First Step After Compaction

1. check local changes
2. commit workflow/debug updates if wanted
3. if user wants CI, push `--no-verify`
4. use `Apple Port Debug` for one dep repro
5. use `Apple Port Build` for full validation
