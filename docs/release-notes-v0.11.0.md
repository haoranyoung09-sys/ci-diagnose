# ci-diagnose 0.11.0

Same Action contract as 0.7.0 through 0.10.0. `action.yml` inputs, outputs, and branding are unchanged. `uses: haoranyoung09-sys/ci-fail-classify@v1` keeps working after you move the `v1` tag to this commit.

## Install

From a checkout:

```bash
bash scripts/install.sh --user --cli
```

The script prints where the skill and the `diagnose` wrapper went. It will not replace an existing link, directory, or wrapper unless you pass `--force`. Python 3.9 or newer is required.

After this tag is on the public mirror:

```bash
curl -fsSL https://raw.githubusercontent.com/haoranyoung09-sys/ci-fail-classify/v0.11.0/scripts/install.sh | bash
```

That downloads the `v0.11.0` archive into `~/.local/share/ci-diagnose`. It does not send a token. `--project` links the skill into the current directory. `--claude` is only for Claude Code.

## What changed in classification

- Yarn Berry refuses an immutable install, Yarn PnP cannot see the project, pip's hash check fails, Coursier cannot resolve a module, pub version solving fails, Bun's lockfile is frozen, or a container tag is not found (`deps`).
- Poetry or uv wants a different Python, `actions/upload-artifact` finds no files, or `actions/download-artifact` cannot find that artifact name (`env`). A 403 from the integration token is still `permissions`.
- PyPI returns 503 and there is no hash or version line (`flake`).
- An image pull is not authorized (`permissions`). A missing tag is `deps`, not this.
- Ruff cannot parse a source file (`test`).

131 synthetic fixtures. `make eval` is 131/131. No new taxonomy id.

## Action

No new inputs. No renamed outputs. Log-path and fixture stay offline. A completed run still needs `actions: read`. `comment` still defaults to false.

## Tags

- `v0.11.0` — this release. Do not move it. The install one-liner pins this tag.
- `v1` — move this tag to this commit when you want `@v1` to install 0.11.0. Do not move it before the public mirror contains the commit.
