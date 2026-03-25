the way you will interact is with github actions is
// runs the workflow
nix-shell -p gh --run 'gh workflow run build-blender-ios.yml --ref IOS5.1-round2'
// polls every 60 seconds to lyk when its done/failed
POLL_INTERVAL_SECONDS=60 nix-shell -p gh --run '.github/poll-build-run.sh build-blender-ios.yml IOS5.1-round2'
// to see how it failed for the next run
nix-shell -p gh --run 'gh run view 23421249851 --log-failed


do not use any other branches as I want to keep them fresh. if you must then force push to the branch above `IOS5.1-round2`
