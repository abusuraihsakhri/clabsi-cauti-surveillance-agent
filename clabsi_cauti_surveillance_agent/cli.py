"""Installed console entry point.

The canonical surveillance commands live in the repository-level cli module.
This wrapper preserves the optional serve command for API users.
"""

import argparse
import sys

from cli import main as surveillance_main


def _serve(argv):
    parser = argparse.ArgumentParser(prog="clabsi-cauti-surveillance-agent serve")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)
    try:
        import uvicorn
    except ImportError:
        print(
            "FastAPI server dependencies are not installed. "
            "Run: pip install clabsi-cauti-surveillance-agent[server]",
            file=sys.stderr,
        )
        return 1

    from .server import create_app

    uvicorn.run(create_app(), host=args.host, port=args.port)
    return 0


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "serve":
        return _serve(args[1:])
    return surveillance_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
