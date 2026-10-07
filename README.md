# PSQL Playground

A small project for learning PostgreSQL. Write SQL in a `.sql` file and save it. The file runs, and each statement's result appears right below it, like a notebook.

It works on **macOS, Windows and Linux**. The database is private to this folder and doesn't touch any other Postgres on your machine.

## Requirements

You need PostgreSQL (any recent version), Python 3.9 or newer and VS Code.

**macOS**

```sh
brew install postgresql@18      # needs Homebrew: https://brew.sh
python3 --version               # macOS already has Python 3.9+; if it asks to install developer tools, accept
```

**Windows**

1. Install PostgreSQL with the [EDB installer](https://www.postgresql.org/download/windows/). Its defaults are fine. You can skip Stack Builder at the end. Remember the password it asks for; this project doesn't use it.
2. Install Python from [python.org](https://www.python.org/downloads/windows/), and tick **"Add python.exe to PATH"** on the first screen.
3. Check it in a new terminal: `python --version`

You don't need to add Postgres to your PATH: `pg.py` finds it in `C:\Program Files\PostgreSQL`.

**Linux**

Install `postgresql` and `python3` with your package manager. Make sure `initdb` and `pg_ctl` are on your `PATH`; on Debian/Ubuntu they're in `/usr/lib/postgresql/<version>/bin`.

> **Commands below use `python3`. On Windows, type `python` instead.**

## Quick start

```sh
git clone <repo-url> PSQL
cd PSQL
code .            # open in VS Code
```

There's no setup step. The first command you run creates a private database in `.pgdata/`.

1. Start the watcher: **Cmd/Ctrl+Shift+P** → *Tasks: Run Task* → **Postgres: run SQL on save (watch)**. Or run `python3 pg.py watch` in a terminal.
2. Open `test.sql`, change something, and press **Cmd/Ctrl+S**.

Every save fills in the results:

```sql
SELECT * FROM person;
/* ▶ ✓ · 0.199 ms
 id |     name     |   address   | date_of_birth
----+--------------+-------------+---------------
  1 | Jahidun Nur  | 123 Main St | 1999-02-01
  2 | John Doe     | 456 Elm St  | 1985-07-15
  3 | Harry potter | 789 Oak St  | 2000-12-31
(3 rows)
*/
```

### Start the watcher automatically

Do this once: **Cmd/Ctrl+Shift+P** → *Tasks: Manage Automatic Tasks* → **Allow Automatic Tasks**, then *Developer: Reload Window*. From then on, the watcher starts whenever you open this folder.

You can tell it's running if a terminal panel says `Watching ./*.sql`. If there isn't one, saving won't update results.

## How results work

- **Each save runs the whole file, top to bottom**, and refreshes every result. Start each file with `DROP TABLE IF EXISTS ...;` so the reruns start from the same data. Without it, `CREATE TABLE` fails because the table already exists.
- **Every `.sql` file in this folder is watched**, so new files work right away.
- **End each statement with `;`**. Without it, the statement merges into the next one.
- **An error gets a `✗ error` block** with the message. Statements below it don't run, so they get no results.
- **Results are replaced on every save.** Don't type your own notes inside a `/* ▶ ... */` block, because they'll be overwritten.
- **Results are ordinary SQL comments**, so the file still runs anywhere.
- **Your cursor stays where it is** when the results are written in.
- **To remove all results**, use VS Code's find and replace with regex `\n/\* ▶[\s\S]*?\n\*/` and an empty replacement.

## Commands

| Command                         | What it does                                                         |
|---------------------------------|----------------------------------------------------------------------|
| `python3 pg.py watch`           | Run any `.sql` file in this folder when you save it, with results inline (Ctrl+C stops) |
| `python3 pg.py run <file.sql>`  | Run a file and print the output in the terminal (also saved to `logs/`) |
| `python3 pg.py psql`            | Open an interactive SQL shell                                        |
| `python3 pg.py log`             | Follow the server log live (every statement and its duration)        |
| `python3 pg.py reset`           | Delete the `learn` database and recreate it empty                    |
| `python3 pg.py start` / `stop` / `status` | Start, stop, or check the server (the other commands start it for you) |

## VS Code

| Action                                  | How                                                        |
|-----------------------------------------|------------------------------------------------------------|
| Results inline on save                  | Task *Postgres: run SQL on save (watch)*, then **Cmd/Ctrl+S** |
| Run the open file in the terminal       | **Cmd/Ctrl+Shift+B** (errors also show in the **Problems** panel) |
| Shell, live server log, reset database  | **Cmd/Ctrl+Shift+P** → *Tasks: Run Task* → pick a `Postgres:` task |

The tasks use `python3` on macOS/Linux and `python` on Windows automatically.

## Debugging SQL

### 1. Read the error

```sql
SELECT * FROM personss;
/* ▶ ✗ error · 0.577 ms
ERROR:  relation "personss" does not exist
LINE 1: SELECT * FROM personss;
                      ^
*/
```

- The `^` points at the exact spot.
- "Relation" is Postgres's word for a table (or view).
- For the full error code (SQLSTATE), run the file with **Cmd/Ctrl+Shift+B**. Search the code in the [list of error codes](https://www.postgresql.org/docs/current/errcodes-appendix.html) to learn more.

### 2. See what the server received

Run `python3 pg.py log` in a second terminal. It prints every statement the server receives, with how long it took.

### 3. See how a query runs

Put `EXPLAIN ANALYZE` in front of a query:

```sql
EXPLAIN ANALYZE SELECT * FROM person WHERE name = 'John Doe';
```

This shows the plan Postgres chose and the real time each step took. For example, `Seq Scan` means it read every row; after you add an index you may see `Index Scan` instead.

### 4. Try things safely

Wrap experiments in a transaction and roll them back:

```sql
BEGIN;
DELETE FROM person;
SELECT * FROM person;   -- empty
ROLLBACK;
SELECT * FROM person;   -- the rows are back
```

## Useful psql commands

These work inside `python3 pg.py psql`, and also as lines in a `.sql` file:

| Command           | What it does                      |
|-------------------|-----------------------------------|
| `\dt`             | List tables                       |
| `\d person`       | Show a table's columns and types  |
| `\l`              | List databases                    |
| `\x`              | Toggle expanded (vertical) output |
| `\?`              | Help for psql commands            |
| `\h CREATE TABLE` | SQL syntax help                   |
| `\q`              | Quit the shell                    |

## Connecting from other tools

You can connect a GUI client (VS Code PostgreSQL extension, DBeaver, TablePlus) with these settings:

| Setting  | Value       |
|----------|-------------|
| Host     | `localhost` |
| Port     | `5433`      |
| Database | `learn`     |
| User     | `postgres`  |
| Password | *(none)*    |

Connection URL: `postgresql://postgres@localhost:5433/learn`

## Project layout

```
.
├── pg.py               # everything: run-on-save watcher, runner, shell, log, reset, start/stop
├── test.sql            # your SQL practice file
├── .vscode/
│   ├── tasks.json      # VS Code tasks (watcher, Cmd/Ctrl+Shift+B, shell, log, reset)
│   └── settings.json   # save the file before a task runs
├── .pgdata/            # database files (created on first start, git-ignored)
└── logs/               # server.log + one log per `run` (git-ignored)
```

## Tips

- Make one `.sql` file per topic (`01_select.sql`, `02_joins.sql`, …).
- Messed something up? Run `python3 pg.py reset`.
- To start over completely, run `python3 pg.py stop`, then delete the `.pgdata` and `logs` folders.

## Troubleshooting

| Problem                               | Fix                                                             |
|---------------------------------------|-----------------------------------------------------------------|
| Saving doesn't update results         | The watcher isn't running. Start it (see Quick start).          |
| Results look stale after editing `pg.py` | Stop the watcher and start it again                         |
| `PostgreSQL not found`                | macOS: `brew install postgresql@18`, then `brew link postgresql@18`. Windows: install with the EDB installer (see Requirements). |
| Windows: `python` opens the Microsoft Store | Python isn't on PATH. Reinstall from python.org and tick **"Add python.exe to PATH"**. |
| Port 5433 already in use              | Change `PORT = 5433` at the top of `pg.py`, then delete `.pgdata` |
| Server won't start                    | Check `logs/server.log`                                         |
