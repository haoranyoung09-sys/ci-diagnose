# ci-fail-classify 0.12.1

The public repository is now `haoranyoung09-sys/ci-fail-classify`. GitHub redirects the old name `haoranyoung09-sys/ci-diagnose`.

This is a rename and docs patch. Classification is unchanged. 146 fixtures. Eval 146/146. Taxonomy ids are unchanged. Skill metadata is 0.12.1.

## Action

Inputs, outputs, and branding are the same as 0.7.0 through 0.12.0. `@v1` stays compatible.

```yaml
- uses: haoranyoung09-sys/ci-fail-classify@v1
```

`uses: haoranyoung09-sys/ci-diagnose@v1` still resolves while GitHub redirects the old repository name. New workflows should use `ci-fail-classify`.

The Action display name in `action.yml` is `ci-fail-classify`. The README still calls the product CI Doctor.

## Install

The skill and CLI pin this release tag:

```bash
curl -fsSL https://raw.githubusercontent.com/haoranyoung09-sys/ci-fail-classify/v0.12.1/scripts/install.sh | bash
```

From a checkout, `bash scripts/install.sh --user --cli` does the same without downloading. The script refuses to replace an existing install unless you pass `--force`. It does not send a token.

The tag archive unpacks as `ci-fail-classify-*`. The local checkout stays `~/.local/share/ci-diagnose`.
