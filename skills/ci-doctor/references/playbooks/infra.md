# infra

The host ran out of memory, disk, or a process slot. Do not edit the assertion to absorb it.

## When to follow this

The CLI category is `infra`. Signals include "JavaScript heap out of memory", "Reached heap limit", `OOMKilled`, "No space left on device", "disk quota exceeded", "out of memory", "runner process was killed" / shutdown, "Cannot connect to the Docker daemon", and a registry pull the runner cannot reach: `dial tcp: lookup`, "no such host", "network is unreachable", "TLS handshake timeout", "i/o timeout", "egress blocked". That covers MCR (`mcr.microsoft.com`) and GHCR.

Corpus: `node-heap-oom`, `runner-disk-full`, `generic-oom-without-heap`, `runner-killed-exit-137`, `docker-build-disk-full`, `docker-daemon-unavailable`, `mcr-pull-egress-blocked`, `ghcr-pull-io-timeout`, `dns-name-resolution-infra`, `actions-cache-restore-corrupt`.

Also: `getaddrinfo` / "Temporary failure in name resolution" / "Could not resolve host", and `Failed to restore cache` / "Cache restore failed". A bare `EACCES: permission denied` on a cache path stays under the threshold.

`generic-oom-without-heap` has "out of memory" and no V8 heap line. `runner-killed-exit-137` has the killed-process line and no disk or heap line. Treat both as infra, and say when the evidence is a single host line rather than a full crash dump.

## Near misses

| What you see | What to do |
| --- | --- |
| A test timeout that passed on rerun, no host line | `flake`. |
| `AssertionError` leading, runner shutdown only in `alternates` | The CLI may keep `test` and cap confidence. Quote the shutdown line. Do not edit the assertion if the process was killed before the suite finished. If you cannot tell, ask. |
| `EACCES` on a cache directory with no OOM and no 403 (`cache-eacces-unknown`) | Not enough for infra or permissions. Stay `unknown`. |
| Exit code 137 with no "killed", "out of memory", or disk line | `unknown` until one of those phrases is in the log. |
| "out of memory" tied with "does not have permission" (`oom-and-permission-unknown`) | Stay `unknown`. Do not grant a scope and do not resize the runner in the same attempt. |
| MCR or GHCR pull: `dial tcp: lookup`, "no such host", "egress blocked", "TLS handshake timeout", or "i/o timeout" (`mcr-pull-egress-blocked`, `ghcr-pull-io-timeout`) | Infra. Quote the registry host. Do not change the image tag and do not `docker login` with a pasted token. One rerun checks whether egress is up. If the same line repeats, the fix is the runner's network path. |
| Docker Hub `toomanyrequests` that passed on the automatic rerun | `flake` (`docker-rate-limit-flake`), not this playbook. |
| Checkout "SSL certificate problem" or "server certificate verification failed" | `flake` (`checkout-tls-verify-flake`). Do not treat a certificate-verification line as a blocked registry pull. |
| Egress blocked and `remote: permission to … denied` in the same log (`egress-and-permission-unknown`) | Stay `unknown`. Do not open the network and grant a scope in one attempt. |
| `pull access denied` or `unauthorized: authentication required` with no DNS or egress line (`registry-pull-auth-denied`) | `permissions`. Do not call it a blocked registry. |
| Egress blocked and registry authentication denied in the same pull (`registry-auth-and-egress-unknown`) | Stay `unknown`. Do not open egress and mint a registry login in one attempt. |
| `getaddrinfo`, "Temporary failure in name resolution", or "Could not resolve host" with no auth line (`dns-name-resolution-infra`) | Infra. One rerun checks whether DNS recovered. Do not treat it as a 403 and do not grant a scope. |
| `Failed to restore cache` or "Cache restore failed" even if `npm ci` then says the lockfile is out of sync (`actions-cache-restore-corrupt`) | Infra. Quote the cache key. Do not edit the lockfile in that attempt. |
| Cache `EACCES` alone (`cache-eacces-unknown`) | Still under the threshold. Stay `unknown`. |
| Cache `EACCES` and a lockfile line (`cache-eacces-and-lockfile-unknown`) | Stay `unknown`. |

## Recipe

1. Quote the host line (heap limit, "out of memory", `OOMKilled`, "No space left on device", "runner process was killed"). Quote the exit code only as support.
2. Suggest one resource change, matched to that line:
   - **Heap / generic OOM:** a smaller build, fewer parallel workers, or a heap cap. Do not raise the heap and also split the job in the same attempt.
   - **Disk:** fewer artifacts, a cleaned cache, or a larger runner class. A Docker build that dies with "no space left on device" (`docker-build-disk-full`) is this case. Do not delete the Dockerfile or the test that was packing the artifact.
   - **Docker daemon unreachable** (`docker-daemon-unavailable`): one rerun is a check that the runner service is up. Do not rewrite the Dockerfile for that line.
   - **Registry or MCR pull blocked** (`mcr-pull-egress-blocked`, `ghcr-pull-io-timeout`): quote the host (`mcr.microsoft.com`, `ghcr.io`, or the name in the log). One rerun is a check that egress is up. Do not retag the image. Do not print or mint a registry token. If the same `no such host`, handshake timeout, or `egress blocked` line repeats, say the runner cannot reach that registry and stop.
   - **DNS** (`dns-name-resolution-infra`): quote the host from `getaddrinfo` or "Could not resolve host". One rerun is a check. Do not switch the job to a token.
   - **actions/cache restore** (`actions-cache-restore-corrupt`): quote the cache key and the corrupt or failed-restore line. One rerun, or dropping that cache key, is the hypothesis. Do not rewrite the lockfile to absorb it.
   - **Runner killed or shutdown, no second signal:** one rerun with no code change. Say the rerun is a check. If the underlying limit is unchanged, the rerun is not a fix.
3. Do not edit an assertion, skip a test, or bump a timeout to swallow the host line.

## Verify

- Re-run the failed job once. That is attempt 1. For a pure shutdown this may be the only action.
- Same failure: the same host line (same OOM phrase, same "no space left", same "runner process was killed").
- New failure: a real assertion after the host line is gone. Switch to `test`. That edit would be attempt 2.
- A green rerun after a shutdown does not prove the limit is gone. Say that.
- Fixture check only re-scores the saved log.

## Stop

- A second identical host line. Report `infra` and the single resource you would change. Do not start rewriting tests.
- You would need two resource changes at once (bigger runner and a heap cap and a cache purge). Pick one or stop.
- The log never named heap, disk, or a killed runner. Do not spend the attempt on a hunch. Follow `unknown`.

## 中文

引用宿主那一行，不要改断言去吞掉它。磁盘满包括 Docker 构建（`docker-build-disk-full`）：减少产物或加大 runner，不要删 Dockerfile。连不上 Docker daemon（`docker-daemon-unavailable`）时只重跑一次作检查。MCR 或 GHCR 拉不动（`mcr-pull-egress-blocked`、`ghcr-pull-io-timeout`：`no such host`、`egress blocked`、TLS handshake timeout、`i/o timeout`）是网络路径，不要改镜像标签，也不要粘贴 registry token。`pull access denied` 或 `unauthorized: authentication required` 且没有 egress 行是 `permissions`（`registry-pull-auth-denied`）。两行同时在（`registry-auth-and-egress-unknown`）保持 `unknown`。`getaddrinfo` 或 “Temporary failure in name resolution”（`dns-name-resolution-infra`）是 DNS，不是 403。`Failed to restore cache`（`actions-cache-restore-corrupt`）先看缓存，不要先改锁文件。单独的缓存 `EACCES` 仍低于阈值。`EACCES` 加锁文件（`cache-eacces-and-lockfile-unknown`）保持 `unknown`。同一行再出现就停。Docker Hub `toomanyrequests` 且重跑已通过是 `flake`。checkout 证书校验失败是 `flake`，不是这类。`egress-and-permission-unknown` 与 `oom-and-permission-unknown` 都是打平，不要同时改网络和权限。只有 “runner process was killed” 时，无代码改动地重跑一次。第二次还是同一行宿主错误就停止。
