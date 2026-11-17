"""Report 5-hour and weekly plan usage so a lead agent knows when to stop.

Plan limits are account-wide, so the newest reading from any session counts.
Codex: the newest `rate_limits` record in $CODEX_HOME/sessions rollout files
(default ~/.codex). Claude Code CLI: the dump this script writes when it runs
as the status line command (`--statusline`). In the Claude desktop app call
the `get_usage` tool instead; this script cannot see that.

    python tools/usage_limit.py               # readings with a verdict each
    python tools/usage_limit.py --statusline  # Claude Code statusLine command

Claude Code CLI setup, in the project's .claude/settings.json (it replaces any
other status line in that project):
    "statusLine": {"type": "command", "command": "python tools/usage_limit.py --statusline"}
"""
import argparse
import calendar
import json
import os
from pathlib import Path
import sys
import tempfile
import time

NO_NEW_WORK = 80  # 5-hour percent: start no new workers
STOP = 85         # 5-hour percent: checkpoint and end the turn
WEEKLY_STOP = 95  # weekly percent; below it keep delegating, the cheaper path
CLAUDE_DUMP = Path(tempfile.gettempdir()) / 'claude-plan-usage.json'
TAIL = 4 << 20    # rollout files grow large; the newest record is near the end
LABELS = {300: '5h', 10080: 'weekly'}


def codex_reading(sessions=None, files=5):
    """Newest Codex reading as {'source', 'at', 'windows': {label: (percent, resets_at)}}."""
    home = Path(os.environ.get('CODEX_HOME') or Path.home() / '.codex')
    sessions = Path(sessions or home / 'sessions')
    if not sessions.is_dir():
        return None
    paths = sorted(sessions.rglob('rollout-*.jsonl'), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in paths[:files]:
        with open(path, 'rb') as f:
            f.seek(max(0, f.seek(0, 2) - TAIL))
            lines = f.read().splitlines()
        for line in reversed(lines):
            if b'"used_percent"' not in line:
                continue
            try:
                record = json.loads(line)
            except ValueError:
                continue  # the first line of the tail may be cut
            limits = (record.get('payload') or {}).get('rate_limits') or {}
            windows = {LABELS.get(w['window_minutes'], f"{w['window_minutes']}min"):
                       (float(w['used_percent']), w.get('resets_at'))
                       for w in limits.values()
                       if isinstance(w, dict) and 'used_percent' in w and 'window_minutes' in w}
            if windows:
                at = record.get('timestamp')
                at = calendar.timegm(time.strptime(at[:19], '%Y-%m-%dT%H:%M:%S')) if at else path.stat().st_mtime
                return {'source': 'codex', 'at': at, 'windows': windows}
    return None


def statusline(stdin_text, dump=CLAUDE_DUMP, now=None):
    """Save Claude Code's status line rate limits and return the line to show."""
    limits = (json.loads(stdin_text or '{}').get('rate_limits')) or {}
    if not limits:
        return 'usage: waiting for first reply'
    Path(dump).write_text(json.dumps({'at': now or time.time(), 'rate_limits': limits}), encoding='utf-8')
    return ' · '.join(f"{label} {limits[key]['used_percentage']:.0f}%"
                      for key, label in (('five_hour', '5h'), ('seven_day', 'weekly'))
                      if limits.get(key, {}).get('used_percentage') is not None)


def claude_reading(dump=CLAUDE_DUMP):
    """Reading saved by --statusline, in the same shape as codex_reading."""
    try:
        saved = json.loads(Path(dump).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    windows = {label: (float(w['used_percentage']), w.get('resets_at'))
               for key, label in (('five_hour', '5h'), ('seven_day', 'weekly'))
               if (w := saved['rate_limits'].get(key)) and w.get('used_percentage') is not None}
    return {'source': 'claude', 'at': saved['at'], 'windows': windows} if windows else None


def verdict(reading, now=None):
    """Advice for the lead. A window past its reset counts as 0."""
    now = now or time.time()
    live = {label: pct if not resets or resets > now else 0.0
            for label, (pct, resets) in reading['windows'].items()}
    short = max((pct for label, pct in live.items() if label != 'weekly'), default=0.0)
    if short >= STOP or live.get('weekly', 0.0) >= WEEKLY_STOP:
        return 'STOP: checkpoint now (finish or stop workers, commit, refresh the handoff, end the turn)'
    if short >= NO_NEW_WORK:
        return 'WRAP UP: start no new workers; finish the units in flight'
    return 'OK'


def describe(reading, now=None):
    now = now or time.time()
    parts = []
    for label, (pct, resets) in reading['windows'].items():
        if resets and resets <= now:
            parts.append(f'{label} {pct:.0f}% (reset since this reading)')
        elif resets:
            left = int(resets - now) // 60
            parts.append(f"{label} {pct:.0f}% (resets {time.strftime('%H:%M', time.localtime(resets))}, "
                         f'in {left // 60}h{left % 60:02d}m)')
        else:
            parts.append(f'{label} {pct:.0f}%')
    advice = verdict(reading, now)
    age = int(now - reading['at']) // 60
    age = f'{age} min' if age < 120 else f'{age // 60} h'
    return f"{reading['source']}: {', '.join(parts)}; read {age} ago\n  -> {advice}"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--statusline', action='store_true',
                        help='act as the Claude Code status line command (reads its JSON on stdin)')
    args = parser.parse_args(argv)
    if args.statusline:
        print(statusline(sys.stdin.read()))
        return
    readings = [r for r in (codex_reading(), claude_reading()) if r]
    for reading in readings:
        print(describe(reading))
    if not readings:
        print('No reading. Claude desktop app: call get_usage. Claude CLI: set up the status line '
              '(see --help). Codex: no rollout with rate limits yet. Otherwise ask the user.')


if __name__ == '__main__':
    main()
