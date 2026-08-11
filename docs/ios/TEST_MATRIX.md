# Blender iOS test matrix

| Test | Level | Configuration | Latest result | Artifact |
| --- | --- | --- | --- | --- |
| Environment doctor | T0 | macOS host + external volume | green | `/Volumes/BlenderBuild/blender-ios/artifacts/n900-doctor/env.json` |
| Ledger/schema validation | T0 | macOS host | green | `python3 -m json.tool docs/ios/STATUS.json` |
| Donor-map completeness | T0 | `v5.1.2..origin/ios` | green: 213/213 exact paths | `python3 build_files/ios/audit.py port-map docs/ios/PORT_MAP.tsv --repository . --base v5.1.2 --donor origin/ios` |
| Dependency ABI auditor fixtures | T0/T3 | arm64 macOS + iOS Simulator objects | green | `python3 -m unittest discover -s build_files/ios/tests -v` |
| Bundle/signing auditor fixtures | T0/T3 | simulator + unsigned device policies | green | `python3 -m unittest discover -s build_files/ios/tests -v` |
| Xcode signing experiment | T2/T3 | Xcode 26.5 arm64 sim + unsigned device | green | `/Volumes/BlenderBuild/blender-ios/artifacts/20260811T044431Z-8f74cae544cd-signing-probe/signing-report.json` |
| Dependency configure contract | T0/T2 | arm64 iOS Simulator 18.0 / SDK 26.5 | green; cold package fetch and content-addressed configure | `/Volumes/BlenderBuild/blender-ios/artifacts/20260811T051226Z-c141dbd31097-deps-configure/result.json` |
| Dependency target inventory | T0 | generated Ninja graph | green: 93 public targets / 286 edges | `docs/ios/DEPENDENCY_DAG.json` |
| Bootstrap dependency packet | T2/T3 | arm64 iOS Simulator 18.0 | green: 8/8 families; every static archive member is arm64 `IOSSIMULATOR` | `/Volumes/BlenderBuild/blender-ios/artifacts/n111-1ae9-bootstrap-summary.json` |
| FreeType dependency packet | T2/T3 | arm64 iOS Simulator 18.0 | green: FreeType + 8 inherited families under one cache key | `/Volumes/BlenderBuild/blender-ios/artifacts/n112-0edd-font-bootstrap-summary.json` |
| Text-shaping dependency packet | T2/T3 | arm64 iOS Simulator 18.0 | green: HarfBuzz, FriBidi, FreeType, Brotli, and zlib; every archive member is `IOSSIMULATOR` | `/Volumes/BlenderBuild/blender-ios/artifacts/n113-b034-text-stack-summary.json` |

Only proven outcomes are recorded here. A download is not a built dependency, a
compiled library is not accepted before ABI audit, and a linked app is not a
successful launch.
