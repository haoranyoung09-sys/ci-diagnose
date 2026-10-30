# ci-diagnose 0.10.0

Same Action contract as 0.7.0 through 0.9.0. `action.yml` inputs, outputs, and branding are unchanged. `uses: haoranyoung09-sys/ci-diagnose@v1` keeps working after you move the `v1` tag to this commit.

## What changed

- Bazel could not query the remote cache, the Nix store hash mismatched, apt's mirror returned 404, Homebrew failed to download a bottle, or the Rust linker ran out of memory (`infra`). Linker OOM still leads when cargo also says it could not compile.
- A Nix flake does not provide the attribute the job asked for, and Deno's lockfile is out of date (`deps`). The word flake in a Nix error is not treated as a rerun.
- apt `NO_PUBKEY`, Google application default credentials were not loaded, Composer requires a newer PHP, or a reusable workflow secret was not passed (`env`).
- AWS says the security token is invalid (`permissions`).
- `proxy.golang.org` returned 502, or the client saw `ECONNRESET` with no assertion (`flake`).
- `ECONNRESET` together with `AssertionError` stays `unknown`.

117 synthetic fixtures. `make eval` is 117/117. No new taxonomy id.

## Action

No new inputs. No renamed outputs. Log-path and fixture stay offline. A completed run still needs `actions: read`. `comment` still defaults to false.

## Tags

- `v0.10.0` — this release. Do not move it.
- `v1` — move this tag to this commit when you want `@v1` to install 0.10.0. Do not move it before the public mirror contains the commit.
