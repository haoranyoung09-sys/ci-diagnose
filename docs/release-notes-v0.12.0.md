# ci-diagnose 0.12.0

Same Action contract as 0.7.0 through 0.11.0. `action.yml` inputs, outputs, and branding are unchanged.

## How to install

The Action and the skill install are both first-class. This project does not run your builds.

Workflows keep moving with the Action tag:

```yaml
- uses: haoranyoung09-sys/ci-fail-classify@v1
  with:
    run-id: ${{ github.event.workflow_run.id }}
```

The skill and CLI pin a release tag. For 0.12.0:

```bash
curl -fsSL https://raw.githubusercontent.com/haoranyoung09-sys/ci-fail-classify/v0.12.0/scripts/install.sh | bash
```

From a checkout, `bash scripts/install.sh --user --cli` does the same without downloading. The script refuses to replace an existing install unless you pass `--force`. It does not send a token.

[docs/architecture.md](architecture.md) is the short map of Action, CLI, and skill.

## What changed in classification

Mobile and signing logs that 0.11.0 left as `unknown`:

- No Apple signing certificate, no provisioning profile, or an expired profile (`env`).
- fastlane match could not read a git username, or could not decrypt the repo (`env`). Do not print the passphrase.
- Android keystore missing, Android SDK location missing, or bundletool needs a newer JDK (`env`).
- adb device unauthorized, or notarization returned 401 (`permissions`).
- adb found no devices, or the iOS simulator failed to boot (`infra`).
- Notarization timed out (`flake`). Do not rotate the Apple credential for that line.
- A fastlane lane's expected/got mismatch, or a Metro `SyntaxError` (`test`).

146 synthetic fixtures. `make eval` is 146/146. No new taxonomy id.

## Action

No new inputs. No renamed outputs. Log-path and fixture stay offline. A completed run still needs `actions: read`. `comment` still defaults to false.

## Tags

- `v0.12.0` — this release. Do not move it. The curl install pins this tag.
- `v1` — move this tag to this commit when you want `@v1` to install 0.12.0. Do not move it before the public mirror contains the commit.
