# ci-diagnose 0.9.0

Same Action contract as 0.7.0 and 0.8.0. `action.yml` inputs, outputs, and branding are unchanged. `uses: haoranyoung09-sys/ci-diagnose@v1` keeps working after you move the `v1` tag to this commit.

## What changed

Failure lines that 0.8.0 left as `unknown`:

- Maven, SwiftPM, CocoaPods, and NuGet could not resolve a package (`deps`).
- Cargo could not reach crates-io (`flake`). rustc rejected the crate (`test`).
- Terraform could not acquire the state lock (`flake`). The provider had no credential sources (`env`). Do not force-unlock as the first step.
- kubectl timed out waiting for a condition (`flake`). The API server forbade the call (`permissions`).
- GitHub secondary rate limit (`flake`). Bad credentials (`permissions`).
- `java.lang.OutOfMemoryError` and Python `MemoryError` (`infra`).
- `Missing required environment variable NAME`, including an App Store Connect key id (`env`).

102 synthetic fixtures. `make eval` is 102/102. No new taxonomy id.

## Action

No new inputs. No renamed outputs. Log-path and fixture stay offline. A completed run still needs `actions: read`. `comment` still defaults to false.

## Tags

- `v0.9.0` — this release. Do not move it.
- `v1` — move this tag to this commit when you want `@v1` to install 0.9.0. Do not move it before the public mirror contains the commit.
