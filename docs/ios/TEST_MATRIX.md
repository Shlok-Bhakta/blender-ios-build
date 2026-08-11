# Blender iOS test matrix

| Test | Level | Configuration | Latest result | Artifact |
| --- | --- | --- | --- | --- |
| Environment doctor | T0 | macOS host | pending | — |
| Ledger/schema validation | T0 | macOS host | pending | — |
| Donor-map completeness | T0 | `v5.1.2..origin/ios` | pending | — |
| Dependency ABI auditor fixtures | T0/T3 | macOS host | pending | — |
| Bundle/signing auditor fixtures | T0/T3 | macOS host | pending | — |
| Xcode signing experiment | T2/T3 | sim + unsigned device | pending | — |

Only proven outcomes are recorded here. A download is not a built dependency, a
compiled library is not accepted before ABI audit, and a linked app is not a
successful launch.

