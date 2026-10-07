#!/usr/bin/env python3
"""PSQL Playground: a project-local PostgreSQL for learning. Works on macOS, Linux and Windows.

Usage: python3 pg.py <command>      (on Windows: python pg.py <command>)
  watch            run any .sql file in this folder when it is saved; results go below each statement
  run <file.sql>   run a file, print the output and save it to logs/
  psql             interactive SQL shell
  log              follow the server log
  reset            drop and recreate the database
  start | stop | status
"""
import glob
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent
PORT = 5433                                                # not 5432, so it won't clash with another Postgres
DB = "learn"
DATA = ROOT / ".pgdata"
LOGS = ROOT / "logs"
MARK = "@@END@@"
BLOCK = re.compile(r"\n/\* ▶ [^\n]*\n.*?\n\*/", re.S)

# UTF-8 so ▶/✓ print on any Windows console; line buffering so output shows up live in VS Code tasks.
sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
os.environ.update(PGHOST="localhost", PGPORT=str(PORT), PGDATABASE=DB, PGUSER="postgres", PGCLIENTENCODING="UTF8")
if os.name == "nt" and not shutil.which("pg_ctl"):
    # The Windows installer doesn't put Postgres on PATH; use the newest version it installed.
    version = lambda p: [int(x) for x in re.findall(r"\d+", pathlib.Path(p).parent.name)]
    bins = sorted(glob.glob(r"C:\Program Files\PostgreSQL\*\bin"), key=version)
    if bins:
        os.environ["PATH"] = bins[-1] + os.pathsep + os.environ["PATH"]


def pg(*args, **kw):
    return subprocess.run(args, **kw)


def start(quiet=False):
    if not shutil.which("pg_ctl"):
        sys.exit("PostgreSQL not found. Install it (see README) and make sure pg_ctl is on your PATH.")
    LOGS.mkdir(exist_ok=True)
    if not DATA.exists():
        pg("initdb", "-D", str(DATA), "-U", "postgres", "--auth=trust", "-E", "UTF8", "--locale=C",
           check=True, stdout=subprocess.DEVNULL)
        with open(DATA / "postgresql.conf", "a", encoding="utf-8") as f:
            # Server log shows every statement, its duration, and errors.
            f.write(f"\nport = {PORT}\nlog_statement = 'all'\nlog_duration = on\nlog_line_prefix = '%m [%p] %u@%d '\n")
    if pg("pg_ctl", "-D", str(DATA), "status", stdout=subprocess.DEVNULL).returncode != 0:
        # DEVNULL, not a pipe: the server inherits it and a pipe would never close (hangs on Windows).
        pg("pg_ctl", "-D", str(DATA), "-l", str(LOGS / "server.log"), "-w", "start", check=True, stdout=subprocess.DEVNULL)
    found = pg("psql", "-X", "-d", "postgres", "-tAc", f"SELECT 1 FROM pg_database WHERE datname='{DB}'",
               capture_output=True, text=True).stdout.strip()
    if not found:
        pg("createdb", DB, check=True)
    if not quiet:
        print(f"Postgres running on port {PORT}, database '{DB}'")


def run(path):
    """Run a file in the terminal. -e echoes each query; ON_ERROR_STOP halts at the first error with file:line."""
    start(quiet=True)
    out = pg("psql", "-X", "-e", "-v", "ON_ERROR_STOP=1", "-v", "VERBOSITY=verbose", "-c", r"\timing on", "-f", path,
             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", errors="replace")
    log = LOGS / f"run-{time.strftime('%Y%m%d-%H%M%S')}-{pathlib.Path(path).stem}.log"
    log.write_text(out.stdout, encoding="utf-8")
    print(f"{out.stdout}--- exit {out.returncode}, saved to {log.relative_to(ROOT)}")
    return out.returncode


def statement_ends(sql):
    """Offsets just past each statement: after a top-level ';' or a psql \\meta line."""
    ends, i, n, line_start = [], 0, len(sql), True
    while i < n:
        c = sql[i]
        if line_start and c == "\\":                      # psql meta-command: ends at newline
            j = sql.find("\n", i)
            i = n if j == -1 else j
            ends.append(i)
            continue
        line_start = c == "\n" or (line_start and c in " \t")
        if c in "'\"":                                     # 'string' or "identifier"
            j = i + 1
            while j < n and not (sql[j] == c and sql[j + 1:j + 2] != c):
                j += 2 if sql[j] == c else 1
            i = j + 1
        elif sql.startswith("--", i):
            j = sql.find("\n", i)
            i = n if j == -1 else j
        elif sql.startswith("/*", i):
            j = sql.find("*/", i + 2)
            i = n if j == -1 else j + 2
        elif c == "$" and (m := re.match(r"\$[A-Za-z_]*\$", sql[i:])):  # $$ body $$
            j = sql.find(m.group(), i + len(m.group()))
            i = n if j == -1 else j + len(m.group())
        elif c == ";":
            i += 1
            ends.append(i)
        else:
            i += 1
    if sql[ends[-1] if ends else 0:].strip():              # trailing statement without ';'
        ends.append(n)
    return ends


def run_inline(path):
    """Run a file and write each statement's result right below it, in a /* ▶ ... */ block."""
    with open(path, encoding="utf-8", newline="") as f:
        raw = f.read()
    nl = "\r\n" if "\r\n" in raw else "\n"                 # keep the file's own line endings (Windows: CRLF)
    sql = BLOCK.sub("", raw.replace("\r\n", "\n"))
    ends = statement_ends(sql)
    for k, e in enumerate(ends):                           # keep a same-line `-- note` above the result
        if m := re.match(r"[ \t]*(--[^\n]*)?(?=\n|$)", sql[e:]):
            ends[k] = e + m.end()
    chunks = [sql[a:b] for a, b in zip([0] + ends, ends)]

    script = "\\timing on\n" + "".join(f"{c}\n\\echo {MARK}\n" for c in chunks)
    out = pg("psql", "-X", "-v", "ON_ERROR_STOP=1", "-f", "-", input=script,
             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", errors="replace").stdout
    out = re.sub(r"^psql:<stdin>:\d+: ", "", out.replace("Timing is on.\n", "", 1), flags=re.M)
    results = out.split(MARK + "\n")

    parts = []
    for k, chunk in enumerate(chunks):
        parts.append(chunk)
        if k >= len(results):                              # psql stopped before this one
            continue
        times = re.findall(r"^Time: (.*)$", results[k], flags=re.M)
        body = re.sub(r"^Time: .*\n?", "", results[k], flags=re.M).rstrip()
        if not body and not times:
            continue
        head = ("✗ error" if "ERROR:" in body else "✓") + (f" · {times[-1]}" if times else "")
        body = body.replace("*/", "*\\/")                   # a "*/" in the data would end our comment early
        parts.append(f"\n/* ▶ {head}\n{body}\n*/" if body else f"\n/* ▶ {head}\n*/")
    parts.append(sql[ends[-1] if ends else 0:])

    # Atomic swap: a plain open("w") truncates first, VS Code can reload the empty file and the cursor jumps to the end.
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8", newline=nl) as f:
        f.write("".join(parts))
    for _ in range(10):
        try:
            os.replace(tmp, path)
            break
        except PermissionError:                            # Windows: the editor may hold the file for a moment
            time.sleep(0.1)
    else:
        os.replace(tmp, path)
    print(out.replace(MARK + "\n", ""), end="")


def watch():
    # ponytail: polls mtimes every 0.3s (stdlib, works on every OS); fine for a handful of files.
    start(quiet=True)
    seen = lambda: {f: f.stat().st_mtime for f in ROOT.glob("*.sql")}
    mtimes = seen()
    print(f"Watching {ROOT / '*.sql'} — save a file to run it. Ctrl+C to stop.")
    while True:
        time.sleep(0.3)
        for f, m in seen().items():
            if mtimes.get(f) != m:
                print(f"\n===== {f.name} · {time.strftime('%H:%M:%S')} =====")
                try:
                    run_inline(str(f))
                except Exception as e:                     # keep watching even if one run blows up
                    print(f"run failed: {e}")
        mtimes = seen()                                    # includes our own write, so no rerun loop


def follow_log():
    start(quiet=True)
    with open(LOGS / "server.log", encoding="utf-8", errors="replace") as f:
        print("".join(f.readlines()[-20:]), end="")
        while True:
            line = f.readline()
            print(line, end="") if line else time.sleep(0.3)


def reset():
    start(quiet=True)
    pg("dropdb", "--if-exists", DB, check=True)
    pg("createdb", DB, check=True)
    print(f"database '{DB}' recreated")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        if cmd == "run" and len(sys.argv) > 2:
            sys.exit(run(sys.argv[2]))
        elif cmd in ("stop", "status"):
            sys.exit(pg("pg_ctl", "-D", str(DATA), cmd).returncode)
        elif cmd == "psql":
            start(quiet=True)
            sys.exit(pg("psql", "-X").returncode)
        elif cmd in ("start", "watch", "reset", "log"):
            {"start": start, "watch": watch, "reset": reset, "log": follow_log}[cmd]()
        else:
            sys.exit(__doc__)
    except KeyboardInterrupt:
        pass
