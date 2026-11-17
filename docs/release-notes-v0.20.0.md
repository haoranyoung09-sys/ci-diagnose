# ci-fail-classify 0.20.0

Clone, `uses:`, and the install curl URL stay on `haoranyoung09-sys/ci-diagnose`. The Action display name stays `ci-fail-classify`. Inputs, outputs, and branding are unchanged.

## What you see in a report

A compiler line and a log line are different numbers. The report now keeps them apart.

| Field | What it is |
| --- | --- |
| `source.path`, `source.line`, `source.column` | Where the compiler says to look in the repo |
| `evidence[].line` | Line in the kept window. This is the old `L` number |
| `evidence[].log_line` | Line in the original log. It matches `line` when nothing was omitted. After a 2MB cut, tail lines are higher |
| `locations` | Up to three source locations found beside the evidence |

The first next step says to open the source location and says that it is not a log position. It does not emit a shell command. A path that contains a token or a URL is not reported as a source file.

Covered shapes: Python `File "…", line N`, Java `File.java:10:`, C# `File.cs(12,5):`, TypeScript `file.ts(3,5):` and `file.ts:3:5`, Rust `--> src/main.rs:10:9`, Go `file.go:12:`, C/C++ `file.cc:8:3:`, Kotlin `file.kt:10:5:` and `file:///src/App.kt:10:5:`, Swift `File.swift:9:7:`. Windows `C:\src\App.cs(12,5):` is included. ANSI color and a `gh` job/timestamp prefix are stripped first.

Kotlin `unresolved reference:` and Swift `cannot find 'name' in scope` are `test`. A `file://` URL was the kotlinc shape that the plain path rule missed.

251 fixtures. Eval 251/251. No new fixture was added. The locator is locked by unit tests, including a noisy truncated log, two locations at once, and a token inside a path.

## Benchmarks

Same script as 0.19.0: `python3 scripts/bench_classify.py`, Python 3.12.3, three repeats after one warmup. Before is skill 0.19.0 (`34d8d39`). After is this commit. The numbers are filled from the run recorded with this commit.

| Case | 0.19.0 | This commit |
| --- | --- | --- |
| 20k warning lines, then `could not compile` (1,148,952 bytes) | 792.5 ms, test, peak 2077 KB | 872.5 ms, test, peak 2088 KB |
| 80k warning lines, then `--- FAIL:` (4,628,919 bytes) | 1394.6 ms, test, peak 8940 KB | 1486.3 ms, test, peak 12009 KB |
| 60k warning lines, then `cannot find symbol` (3,468,958 bytes) | 1379.1 ms, test, peak 7807 KB | 1530.0 ms, test, peak 10870 KB |

This is a small slowdown, about 6–11% on these three cases, and a higher peak on the two logs that are windowed. The category stays `test`. It is not a speedup. The extra memory is the window plus the source-location objects on top of the input string the bench already holds. A file read still does not keep the middle text; it does scan that middle once to count newlines so `log_line` is real.

## Limits

The omitted middle still hides whatever was there. Original log line numbers for a file read count newlines in that middle and do not score it. A diagnostic with no file and no line stays a category only. The CLI is still Python.

## Install

After tag `v0.20.0` is on the public mirror:

```bash
curl -fsSL https://raw.githubusercontent.com/haoranyoung09-sys/ci-diagnose/v0.20.0/scripts/install.sh | bash
```

```yaml
- uses: haoranyoung09-sys/ci-diagnose@v1
```

## 中文

clone、`uses:` 和安装 curl 仍是 `haoranyoung09-sys/ci-diagnose`。Action 显示名仍是 `ci-fail-classify`。输入、输出和 branding 不变。

编译器说的文件位置和日志行号不是同一个数。`source` 是仓库里的文件、行、列。证据 `line` 是保留窗口里的行号，也就是原来的 `L`。`log_line` 是原始日志行号；没有截断时两者相同，截断后末尾的行号更大。下一步让你打开源文件位置，并写明那不是日志位置。不会输出 shell 命令。带 token 或 URL 的路径不会当成源文件。

Python、Java、C#、TypeScript、Rust、Go、C/C++、Kotlin、Swift 的常见位置写法都能解析，包括 Windows 路径、ANSI 颜色和 `gh` 时间戳前缀。Kotlin `unresolved reference:` 和 Swift `cannot find 'name' in scope` 是 `test`。没有新增 fixture，仍是 251 条，eval 251/251。

性能对照用同一条 `scripts/bench_classify.py`。这一版比 0.19.0 慢大约 6–11%，大日志的峰值内存也更高。类别仍是 `test`。这不是加速。读文件时中间文本不保留，但会扫一遍只为了数换行，这样 `log_line` 才是原始行号。中间被省略的内容仍然看不到。命令行仍是 Python。
