"""Launcher for the GBM-AI Streamlit dashboard skeleton."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def dashboard_app_path() -> Path:
    return Path(__file__).with_name("app.py")


def build_streamlit_command(*, host: str, port: int) -> list[str]:
    return [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(dashboard_app_path()),
        "--server.address",
        host,
        "--server.port",
        str(port),
    ]


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch the GBM-AI Streamlit dashboard skeleton.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8501)
    parser.add_argument("--print-command", action="store_true", help="Print the Streamlit command without running it.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    command = build_streamlit_command(host=args.host, port=args.port)
    if args.print_command:
        print(" ".join(command))
        return 0
    try:
        import streamlit  # noqa: F401
    except ImportError:
        parser.error('Streamlit is not installed. Install it with: pip install -e ".[dashboard]"')
    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main())
