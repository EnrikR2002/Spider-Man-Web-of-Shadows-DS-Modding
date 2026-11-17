"""Plan usage readings for the lead agent's stop rule."""
import json
from pathlib import Path
import tempfile
import unittest

from tools import usage_limit


def token_count(stamp, five_hour, weekly, resets):
    return json.dumps({'timestamp': stamp, 'type': 'event_msg', 'payload': {
        'type': 'token_count', 'rate_limits': {
            'limit_id': 'codex',
            'primary': {'used_percent': five_hour, 'window_minutes': 300, 'resets_at': resets},
            'secondary': {'used_percent': weekly, 'window_minutes': 10080, 'resets_at': resets + 9999}}}})


class UsageLimitTests(unittest.TestCase):
    def test_codex_takes_the_newest_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            day = Path(tmp, '2026', '11', '16')
            day.mkdir(parents=True)
            (day / 'rollout-a.jsonl').write_text('\n'.join([
                token_count('2026-11-16T01:00:00.000Z', 50.0, 8.0, 2_000_000_000),
                token_count('2026-11-16T02:00:00.000Z', 86.0, 9.0, 2_000_000_000),
                '{"type":"response_item","payload":{}}']), encoding='utf-8')
            reading = usage_limit.codex_reading(tmp)
        self.assertEqual(reading['windows'], {'5h': (86.0, 2_000_000_000), 'weekly': (9.0, 2_000_009_999)})
        self.assertTrue(usage_limit.verdict(reading, now=1_900_000_000).startswith('STOP'))

    def test_claude_statusline_round_trip_and_reset_window(self):
        payload = {'rate_limits': {'five_hour': {'used_percentage': 82.4, 'resets_at': 1000},
                                   'seven_day': {'used_percentage': 40, 'resets_at': 5000}}}
        with tempfile.TemporaryDirectory() as tmp:
            dump = Path(tmp, 'usage.json')
            self.assertEqual(usage_limit.statusline(json.dumps(payload), dump, now=900), '5h 82% · weekly 40%')
            reading = usage_limit.claude_reading(dump)
            self.assertEqual(usage_limit.statusline('{}', dump), 'usage: waiting for first reply')
        self.assertEqual(usage_limit.verdict(reading, now=950)[:7], 'WRAP UP')
        self.assertEqual(usage_limit.verdict(reading, now=2000), 'OK')  # 5h window has reset
        self.assertIsNone(usage_limit.claude_reading(Path(tmp, 'missing.json')))

    def test_weekly_pressure_keeps_delegating_until_95(self):
        windows = {'5h': (2.0, None), 'weekly': (82.0, None)}
        self.assertEqual(usage_limit.verdict({'windows': windows}), 'OK')
        windows['weekly'] = (95.0, None)
        self.assertTrue(usage_limit.verdict({'windows': windows}).startswith('STOP'))


if __name__ == '__main__':
    unittest.main()
