# CLAUDE.md

## Project Overview

git-fit is a fitness tracker that runs via Git hooks. On `git commit`, the pre-commit hook triggers a randomized exercise routine, times the user, and logs results to CSV. It encourages physical activity during coding sessions by cycling through exercise categories.

## Tech Stack

- Python 3.6+ (stdlib only, no external dependencies)
- No build step required

## Running

```bash
python3 git_fit.py
```

The script is normally triggered automatically by the pre-commit hook. It can also be run directly for testing. It will only execute an exercise if the cooldown has elapsed and the current hour is within the configured active window.

## Project Structure

- `git_fit.py` — Core application logic (config, state, logging, TTS, exercise flow)
- `config.json` — Exercise categories, timing, routine selection
- `routines/` — Pluggable routine implementations (loaded dynamically via `importlib`)
  - `RandomCycle.py` — Active routine, cycles randomly through categories
  - `FourDaySplit.py` — Stub, not functional
- `hooks/` — Git hooks directory (set via `core.hookspath`)
- `.state.json` — Runtime state (gitignored)
- `log.csv` — Exercise history (gitignored)

## Hook Setup

To install the hooks, set the Git config to use this project's hooks directory:

```bash
git config --global core.hookspath /path/to/git-fit/hooks
```

The pre-commit hook skips amended commits and redirects IO to TTY for interactive prompts.

## Key Patterns

- **Dataclasses** for Config, State, ExerciseLog
- **Abstract base class** (`Routine`) for exercise routines — new routines extend this
- **Dynamic module loading** — routine class is resolved from `config.json` via `importlib`
- **Cross-platform TTS** — uses `say` on macOS, `espeak` on Linux, PowerShell on Windows
- **CSV logging** with headers: `[timestamp, category, exercise, reps]`
- **JSON state persistence** for tracking remaining categories/exercises per cycle
