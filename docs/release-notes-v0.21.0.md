# ci-fail-classify 0.21.0

This published release is 0.21.0. `uses: haoranyoung09-sys/ci-diagnose@v1` includes these features once the `v1` tag points at this commit. The install pin is:

```bash
curl -fsSL https://raw.githubusercontent.com/haoranyoung09-sys/ci-diagnose/v0.21.0/scripts/install.sh | bash
```

Action inputs, outputs, and branding are unchanged. The display name stays `ci-fail-classify`. The path stays `haoranyoung09-sys/ci-diagnose`.

## What changed

ASCII logs larger than 2MB are split into a head and a tail without encoding a second copy of the whole log. `log_line` is still the original line number. `source` is still the compiler file, line, and column. A unit test checks the ASCII window against the byte window.

The English and 中文 READMEs separate the Python 3.9+ runtime from languages whose logs are recognized. Ecosystem badges have no version numbers, and they are on this tag. A checked demo, `sh scripts/demo_offline.sh`, prints the javac report, including the source location. The picture [`docs/demo-source-location.svg`](demo-source-location.svg) is generated from that text. It is not a screen recording.

251 fixtures. Eval 251/251.

## Benchmarks

Same host, Python 3.12.3, five runs each, one warmup excluded from the five. `tracemalloc` peak is allocations during `classify`, not the input string created before the timer. Median is the third of the five sorted times.

| Case | 0.19.0 min / med / max | 0.20.0 min / med / max | This commit min / med / max |
| --- | --- | --- | --- |
| 20k warnings, then `could not compile` (1,148,952 bytes, not truncated) | 794.1 / 801.7 / 827.5 ms, peak 2076 KB, test | 842.5 / 846.5 / 847.9 ms, peak 2078 KB, test | 806.5 / 818.6 / 838.5 ms, peak 2078–2080 KB, test |
| 80k warnings, then `--- FAIL:` (4,628,919 bytes, truncated) | 1403.9 / 1407.8 / 1436.4 ms, peak 8939 KB, test | 1486.5 / 1491.9 / 1496.7 ms, peak 12001 KB, test | 1431.0 / 1460.5 / 1508.6 ms, peak 5534–5535 KB, test |
| 60k warnings, then `cannot find symbol` (3,468,958 bytes, truncated) | 1385.5 / 1400.4 / 1430.6 ms, peak 7806 KB, test | 1492.1 / 1495.3 / 1503.2 ms, peak 10869 KB, test | 1415.9 / 1441.7 / 1472.9 ms, peak 5534 KB, test, source `src/App.java:10`, log line 60001, window line 34582 |

Memory on the two windowed logs is lower than both 0.19.0 and 0.20.0. Wall time is a little under 0.20.0. It is still a few percent above the 0.19.0 medians. The 20k case overlaps the 0.19.0 range (this commit's minimum is 806.5 ms; 0.19.0's maximum is 827.5 ms). This is not a claim that the tool is faster than 0.19.0.

The javac location survived the change: path `src/App.java`, source line 10, original log line 60001, window line 34582.

## Limits

A file read still scans the omitted middle once to count newlines. That scan is not in the in-memory bench above. The middle is still not scored. The CLI is still Python.

## 中文

公开发布的就是 0.21.0。`uses: haoranyoung09-sys/ci-diagnose@v1` 在 `v1` 指向这次提交之后包含这些功能。安装钉在 `v0.21.0`：`https://raw.githubusercontent.com/haoranyoung09-sys/ci-diagnose/v0.21.0/scripts/install.sh`。

ASCII 且超过 2MB 的日志不再为了算原始行号而把整段日志再编码一份。`log_line` 和 `source` 都还在。同一台机器、各五次：大日志的峰值内存低于 0.19.0 和 0.20.0；耗时略低于 0.20.0，仍比 0.19.0 的中位数高几个百分点。20k 那组的范围和 0.19.0 重叠。不要把这说成比 0.19.0 更快。

javac 的位置还在：`src/App.java` 第 10 行，原始日志第 60001 行，窗口第 34582 行。

英文和中文 README 把 Python 3.9+ 运行时和“认得哪些日志”分开。生态徽章不写编译器版本，并且就在这个标签上。`sh scripts/demo_offline.sh` 打印带源文件位置的 javac 报告。图由这段真实输出生成，不是录屏。

读文件时仍会把省略的中间扫一遍，只为了数换行。中间内容仍然不计分。命令行仍是 Python。
