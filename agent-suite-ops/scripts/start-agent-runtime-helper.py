"""Start one Agent uvicorn process detached from the current shell."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

CREATE_NEW_PROCESS_GROUP = 0x00000200
DETACHED_PROCESS = 0x00000008


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", required=True)
    parser.add_argument("--workdir", required=True)
    parser.add_argument("--app", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", required=True)
    parser.add_argument("--stdout", required=True)
    parser.add_argument("--stderr", required=True)
    parser.add_argument("--pid-file", required=True)
    args = parser.parse_args()

    stdout_path = Path(args.stdout)
    stderr_path = Path(args.stderr)
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)

    stdout = stdout_path.open("ab", buffering=0)
    stderr = stderr_path.open("ab", buffering=0)
    run_code = (
        "import uvicorn; "
        f"uvicorn.run({args.app!r}, host={args.host!r}, port={int(args.port)!r})"
    )
    process = subprocess.Popen(
        [args.python, "-c", run_code],
        cwd=args.workdir,
        stdin=subprocess.DEVNULL,
        stdout=stdout,
        stderr=stderr,
        creationflags=CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS,
        close_fds=True,
    )
    Path(args.pid_file).write_text(str(process.pid), encoding="ascii")
    print(process.pid)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
