# infra

The host ran out of memory, disk, or a process slot. Do not edit the assertion to absorb it.

## When to follow this

The CLI category is `infra`. Signals include "JavaScript heap out of memory", "Reached heap limit", `OOMKilled`, "No space left on device", "disk quota exceeded", "out of memory", and "runner process was killed" / shutdown.

Corpus: `node-heap-oom`, `runner-disk-full`, `generic-oom-without-heap`, `runner-killed-exit-137`.

`generic-oom-without-heap` has "out of memory" and no V8 heap line. `runner-killed-exit-137` has the killed-process line and no disk or heap line. Treat both as infra, and say when the evidence is a single host line rather than a full crash dump.

## Near misses

| What you see | What to do |
| --- | --- |
| A test timeout that passed on rerun, no host line | `flake`. |
| `AssertionError` leading, runner shutdown only in `alternates` | The CLI may keep `test` and cap confidence. Quote the shutdown line. Do not edit the assertion if the process was killed before the suite finished. If you cannot tell, ask. |
| `EACCES` on a cache directory with no OOM and no 403 (`cache-eacces-unknown`) | Not enough for infra or permissions. Stay `unknown`. |
| Exit code 137 with no "killed", "out of memory", or disk line | `unknown` until one of those phrases is in the log. |

## Recipe

1. Quote the host line (heap limit, "out of memory", `OOMKilled`, "No space left on device", "runner process was killed"). Quote the exit code only as support.
2. Suggest one resource change, matched to that line:
   - **Heap / generic OOM:** a smaller build, fewer parallel workers, or a heap cap. Do not raise the heap and also split the job in the same attempt.
   - **Disk:** fewer artifacts, a cleaned cache, or a larger runner class. Do not delete the test that was packing the artifact.
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

引用宿主那一行，不要改断言去吞掉它。堆或笼统的 out of memory：只改一处资源（更小的构建、更少并行，或堆上限）。磁盘满：减少产物或加大 runner。只有 “runner process was killed”（`runner-killed-exit-137`）时，无代码改动地重跑一次，并说明这是检查不是修复。第二次还是同一行宿主错误就停止。缓存目录 `EACCES` 证据不足，保持 `unknown`。
