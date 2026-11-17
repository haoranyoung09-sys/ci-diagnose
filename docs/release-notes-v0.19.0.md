# ci-fail-classify 0.19.0

Clone, `uses:`, and the install curl URL stay on `haoranyoung09-sys/ci-diagnose`. The Action display name stays `ci-fail-classify`. Inputs, outputs, and branding are unchanged.

This is still diagnosis only. It does not build, sign, or host the app.

## What changed for someone reading a log

A log over 2MB used to keep only the start. The compiler or test failure at the end was dropped, and the report came back `unknown`. The CLI and the Action now keep the start and the end. The middle is not loaded. The report still says `truncated`. Evidence line numbers are positions in that window, not the original file.

These compiler lines are no longer `unknown`:

| What you see | Category | Fixture |
| --- | --- | --- |
| javac `error: cannot find symbol` | test | `javac-cannot-find-symbol-test` |
| `error CS` plus digits | test | `csharp-type-not-found-test` |
| `error TS` plus digits | test | `tsc-assignability-test` |
| clang undeclared identifier | test | `clang-undeclared-identifier-test` |
| gcc undeclared (first use) | test | `gcc-undeclared-identifier-test` |
| MSBuild `error MSB3644` | env | `msbuild-targeting-pack-missing-env` |

251 fixtures. Eval 251/251.

## Language choice

The slow path was Python applying about 200 regular expressions to every line. A Rust or Go binary would need a new build in the Action and in `install.sh`. A required-literal check in the same Python file removes most of those scans and keeps one runtime. `make bench` prints the timings. Do not treat a single laptop number as a guarantee on every runner.

Measured on Python 3.12.3 with `scripts/bench_classify.py` (3 repeats after one warmup, tracemalloc peak includes the log). Before is skill 0.18.0. After is this commit.

| Case | Before (0.18.0) | After (this commit) |
| --- | --- | --- |
| 20k warning lines, then `could not compile` (1,148,952 bytes) | 5736.9 ms, test, peak 2077 KB | 792.5 ms, test, peak 2077 KB |
| 80k warning lines, then `--- FAIL:` (4,628,919 bytes) | 9793.6 ms, unknown, peak 6475 KB | 1394.6 ms, test, peak 8940 KB |
| 60k warning lines, then `cannot find symbol` (3,468,958 bytes) | 9870.0 ms, unknown, peak 5570 KB | 1379.1 ms, test, peak 7807 KB |

The before run kept only the start of a log, so the Go and javac failures were past the cut. The after run keeps the tail, which is why those two are `test`. Peak for the larger cases includes the input string the bench already held plus the window copy. A file read does not load the middle. Re-run `make bench` on your machine if you need a number for that host.

## Limits

The omitted middle can still hide a signal. `truncated: true` means that. Rust `could not compile`, Go `--- FAIL`, and pytest `FAILED` were already classified. A second runtime was not added.

## Install

After tag `v0.19.0` is on the public mirror:

```bash
curl -fsSL https://raw.githubusercontent.com/haoranyoung09-sys/ci-diagnose/v0.19.0/scripts/install.sh | bash
```

```yaml
- uses: haoranyoung09-sys/ci-diagnose@v1
```

## 中文

clone、`uses:` 和安装 curl 仍是 `haoranyoung09-sys/ci-diagnose`。Action 显示名仍是 `ci-fail-classify`。输入、输出和 branding 不变。

超过 2MB 的日志以前只留开头，结尾的编译或测试失败会被丢掉，报告变成 `unknown`。现在保留开头和结尾，中间不读入。报告仍标 `truncated`。证据行号是这段窗口里的位置。

javac `cannot find symbol`、`error CS`、`error TS`、C/C++ 未声明的名字是 `test`。`error MSB3644` 是 `env`。251 条 fixture，eval 251/251。

慢的部分是 Python 对每一行跑约 200 条正则。没有为了速度再加一套 Rust 或 Go 运行时。先用字面量判断能不能跳过正则。`make bench` 打印时间。上面的表是 0.18.0 的测量；这一版的时间以同一次 `make bench` 为准。中间被省略的信号仍然可能看不到。
