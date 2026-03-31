# iOS Branch - Agent Instructions

## Working Branch

- Branch: `ios-portingforward`
- Fork: `git@github.com:Shlok-Bhakta/blender-ios-build.git`

## Workflow Commands

### Dispatch ios-deps workflow
```bash
nix-shell -p gh --run 'gh workflow run build-blender-ios.yml -R Shlok-Bhakta/blender-ios-build --ref ios-portingforward -f mode=ios-deps'
```

### Poll workflow status
```bash
POLL_INTERVAL_SECONDS=60 nix-shell -p gh --run '.github/poll-build-run.sh build-blender-ios.yml ios-portingforward Shlok-Bhakta/blender-ios-build'
```

### View workflow logs
```bash
nix-shell -p gh --run 'gh run view <run-id> -R Shlok-Bhakta/blender-ios-build --log-failed'
```

### List recent runs
```bash
nix-shell -p gh --run 'gh run list -R Shlok-Bhakta/blender-ios-build --workflow build-blender-ios.yml --limit 5'
```

## Build Targets

- `ios-deps`: Build iOS target dependencies from source
- `ios-deps-basic`: Build basic iOS dependencies (simpler subset)

## CI Runner

- GitHub-hosted macOS ARM64 runner: `macos-15-arm64`
- Xcode: `16.4`
- iOS SDK: `iPhoneOS18.5.sdk`
