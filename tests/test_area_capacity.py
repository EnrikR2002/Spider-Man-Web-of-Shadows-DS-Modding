import json
from pathlib import Path
import tempfile
import unittest

import mod
from tools import area_capacity as a, midnight_chapter as ch


class ProposalTests(unittest.TestCase):
    def test_pool_excludes_each_existing_owner(self):
        self.assertEqual(a.unused_flags((140,), (141,), (142,), pool=(140, 141, 142, 143)), [143])

    def test_occupied_and_unaudited_flags_are_rejected(self):
        for flag in (150, 290):
            with self.subTest(flag=flag), self.assertRaisesRegex(ValueError, 'occupied or unaudited'):
                a.validate_proposal([{'room': 96, 'visited_flag': flag}], {}, (161,))

    def test_milestone_cannot_steal_a_room_visit(self):
        with self.assertRaisesRegex(ValueError, 'overlap'):
            a.validate_proposal([{'room': 96, 'visited_flag': 161}], {'won': 161}, (161,))

    def test_current_allocator_contract_is_required(self):
        with self.assertRaisesRegex(ValueError, 'allocator'):
            a.validate_proposal([{'room': 96, 'visited_flag': 160}], {}, (160, 161))

    def test_nine_rooms_and_four_milestones_fit_current_pool(self):
        rooms = [{'room': i, 'visited_flag': ch.visited(i)} for i in range(96, 105)]
        result = a.validate_proposal(rooms, {'crane': 140, 'grid': 141, 'roofs': 142, 'power': 143},
                                     (*range(140, 150), *range(152, 162), 245))
        self.assertEqual(result['flag_count'], 13)
        self.assertEqual(len(result['remaining_flags']), 8)

    def test_report_cannot_be_relabelled_as_another_rom(self):
        with tempfile.TemporaryDirectory() as d:
            rom, report = Path(d) / 'test.nds', Path(d) / 'report.json'
            rom.write_bytes(b'unrelated')
            report.write_text(json.dumps({'output_rom_sha256': 'wrong'}))
            with self.assertRaisesRegex(ValueError, 'exact ROM'):
                a.audit(rom, report)

    def test_hypothetical_visit_does_not_change_the_live_allocator(self):
        result = a.validate_proposal([{'room': 106, 'visited_flag': 149}], {}, (149,),
                                     visit_overrides={'106': 149})
        self.assertTrue(result['requires_visited_mapper_change'])
        with self.assertRaisesRegex(ValueError, 'exhausted'):
            ch.visited(106)

    def test_proposed_mapping_cannot_rewrite_a_released_visit(self):
        with self.assertRaisesRegex(ValueError, 'existing room'):
            a.validate_proposal([], {}, (140,), visit_overrides={95: 140})

    def test_proposed_mapping_still_rejects_occupied_storage(self):
        with self.assertRaisesRegex(ValueError, 'occupied or unaudited'):
            a.validate_proposal([{'room': 106, 'visited_flag': 151}], {}, (149,),
                                 visit_overrides={106: 151})


@unittest.skipUnless(mod.DEFAULT_ROM.exists() and
                     (mod.ROOT / 'build/version-0.15.0-final/Versioned.nds').exists(), 'Private release not present')
class PublishedBudgetTests(unittest.TestCase):
    def test_actual_roadmap_uses_only_the_audited_free_pool(self):
        plan = json.loads((mod.ROOT / 'reference/area_roadmap.json').read_text())
        report = mod.ROOT / f"build/version-{plan['baseline_release']}-final/Versioned.build.json"
        if not report.exists():
            self.skipTest('Planning baseline release not present')
        build = json.loads(report.read_text())
        self.assertEqual(plan['baseline_sha256'], build['output_rom_sha256'])
        free = a.unused_flags(build['midnight_line']['local_flags'].values(), ch.ROOM_FLAGS.values(),
                              (ch.visited(r.index) for r in ch.ROOMS))
        result = a.validate_proposal(plan['first_wave']['proposed_rooms'],
                                     plan['first_wave']['proposed_milestones'], free,
                                     visit_overrides=plan['first_wave'].get('proposed_visit_overrides'))
        self.assertEqual(result['room_count'], plan['first_wave']['target_room_count'])
        allocated = {r['name'] for r in plan['first_wave']['proposed_rooms']}
        selected = plan['first_wave'].get('area_ids', [area['id'] for area in plan['areas']])
        designed = [r['name'] for area in plan['areas'] if area['id'] in selected for r in area.get('rooms', ())]
        self.assertEqual(set(designed), allocated)
        self.assertEqual(len(designed), len(allocated))

    def test_release_roundtrip_and_growth_boundary(self):
        r = a.audit(mod.ROOT / 'build/version-0.15.0-final/Versioned.nds',
                    mod.ROOT / 'build/version-0.15.0-final/Versioned.build.json', (1, 3, 9))
        self.assertTrue(r['published_table_exact'])
        self.assertEqual(r['current_free_before_roof_adapter'], 128)
        trials = {(t['added_rooms'], t['reservation']): t for t in r['trials']}
        self.assertTrue(trials[1, 4096]['packed'])
        self.assertFalse(trials[3, 4096]['packed'])
        self.assertTrue(trials[9, 8192]['packed'])
        self.assertEqual(len(r['unused_audited_flags']), 21)


if __name__ == '__main__':
    unittest.main()
