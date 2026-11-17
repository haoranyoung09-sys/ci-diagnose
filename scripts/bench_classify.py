#!/usr/bin/env python3
"""Reproducible classify timings. Stdlib only. Not part of make smoke.

Prints wall time and tracemalloc peak for three noisy logs. The two large
logs put the real compiler or test failure after the 2MB cap so a head-only
read would miss it.
"""

from __future__ import annotations

import importlib.util
import sys
import time
import tracemalloc
from pathlib import Path


def _load():
    path = Path(__file__).resolve().parent / "diagnose.py"
    spec = importlib.util.spec_from_file_location("diagnose", path)
    if spec is None or spec.loader is None:
        raise SystemExit("could not load diagnose.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["diagnose"] = module
    spec.loader.exec_module(module)
    return module


def _noise(lines: int, tail: str) -> str:
    return "".join(f"npm WARN optional skip optional dependency fsevents@{i}\n" for i in range(lines)) + tail


def main() -> int:
    diagnose = _load()
    cases = {
        "20k noise + rustc": _noise(
            20_000,
            "error[E0308]: mismatched types\nerror: could not compile `app`\n",
        ),
        "80k noise + go FAIL": _noise(80_000, "--- FAIL: TestHealth (0.01s)\n"),
        "javac at end": _noise(
            60_000,
            "src/App.java:10: error: cannot find symbol\n  symbol:   class Widget\n",
        ),
    }
    print(f"python {sys.version.split()[0]} rules {len(diagnose.COMPILED)}")
    for name, text in cases.items():
        tracemalloc.start()
        diagnose.classify(text)
        start = time.perf_counter()
        result = None
        for _ in range(3):
            result = diagnose.classify(text)
        elapsed = (time.perf_counter() - start) / 3
        _current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        assert result is not None
        print(
            f"{name}\tbytes={len(text.encode())}\ttruncated={result.truncated}\t"
            f"category={result.category}\tms={elapsed * 1000:.1f}\tpeak_kb={peak / 1024:.0f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
