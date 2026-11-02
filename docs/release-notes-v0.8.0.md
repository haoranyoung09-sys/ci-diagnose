# ci-diagnose 0.8.0

Same Action contract as 0.7.0. `action.yml` inputs, outputs, and branding are unchanged. `uses: haoranyoung09-sys/ci-diagnose@v1` keeps working after you move the `v1` tag to this commit.

## What changed

The classifier covers failure lines that 0.7.0 left as `unknown` or could misread:

- Kernel `Killed` and exit 137, without a V8 heap line (`infra`).
- Node `engines` mismatch, and a setup-python/setup-node version the image does not have (`env`).
- Missing composite `action.yml` (`env`).
- Self-hosted runner lost communication (`infra`).
- `Filename too long` (`infra`).
- Image platform does not match the host, including `exec format error` (`infra`).
- Docker build layer missing (`infra`), and that line is not treated as a pytest failure.
- Bare `toomanyrequests` and Git LFS rate limit (`flake`). Cypress "Timed out retrying after Nms" (`flake`).
- `pnpm-lock.yaml` is not up to date (`deps`).
- A `continue-on-error` step is ignored so a later lockfile error stays `deps`.
- `toomanyrequests` together with `pull access denied` stays `unknown`.

87 synthetic fixtures. `make eval` is 87/87. No new taxonomy id.

## Action

No new inputs. No renamed outputs. Log-path and fixture stay offline. A completed run still needs `actions: read`. `comment` still defaults to false.

## Tags

- `v0.8.0` — this release. Do not move it.
- `v1` — move this tag to this commit when you want `@v1` to install 0.8.0. Do not move it before the public mirror contains the commit.

Marketplace: publish from the GitHub Release for `v0.8.0` if you want the listing updated. The 0.7.0 release notes still describe the Action setup.
