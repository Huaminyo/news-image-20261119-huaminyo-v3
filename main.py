#!/usr/bin/env python3
"""Entrypoint: copy the rendered newspaper to the output directory.

The image is drawn by render_v3.py (run at build time) and committed as
entry.png; this program only copies it, so it runs with the standard
library alone, with no network, and writes identical bytes every run.
"""
import os
import shutil


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    shutil.copyfile(os.path.join(here, "entry.png"),
                    os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()
