#!/bin/sh
# Offline demo for this release. The javac fixture prints a source location.
# The saved SVG is generated from that text. It is not a screen recording.
set -eu
cd "$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
exec python3 scripts/diagnose.py --fixture javac-cannot-find-symbol-test
