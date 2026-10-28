"""The documentation contract (reference/doc_contract.json) holds for the live docs."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools import doc_contract


class DocumentContractTests(unittest.TestCase):
    """One test per rule family so a failure names the rule that drifted."""

    @classmethod
    def setUpClass(cls):
        cls.contract = doc_contract.load()

    def assertRuleHolds(self, rule):
        self.assertEqual(rule(self.contract), [])

    def test_fixed_core_document_set(self):
        self.assertRuleHolds(doc_contract.check_document_set)

    def test_only_a_registered_linked_checkout_has_its_own_document_contract(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'README.md').write_text('Source docs')
            nested = root/'.claude/worktrees/other'
            nested.mkdir(parents=True)
            (nested/'README.md').write_text('Other checkout docs')
            marker = nested/'.git'
            admin = root/'.git/worktrees/other'
            admin.mkdir(parents=True)
            marker.write_text('gitdir: '+str(admin))
            contract = {'documents': [{'path': 'README.md'}]}
            self.assertTrue(doc_contract.check_document_set(contract, root))
            (admin/'gitdir').write_text(str(marker))
            self.assertEqual(doc_contract.check_document_set(contract, root), [])
            (admin/'commondir').write_text('../..')
            child = nested/'child'
            child.mkdir()
            (child/'README.md').write_text('Third checkout docs')
            child_admin = root/'.git/worktrees/child'
            child_admin.mkdir()
            (child/'.git').write_text('gitdir: '+str(child_admin))
            (child_admin/'gitdir').write_text(str(child/'.git'))
            self.assertEqual(doc_contract.check_document_set(contract, nested), [])
            (root/'.claude/extra.md').write_text('Still outside the contract')
            self.assertEqual(doc_contract.check_document_set(contract, root),
                ['.claude/extra.md: Markdown file outside the contract'])

    def test_word_limits_headings_and_required_text(self):
        self.assertRuleHolds(doc_contract.check_documents)

    def test_local_links_and_anchors_resolve(self):
        self.assertRuleHolds(doc_contract.check_links)

    def test_one_current_version_everywhere(self):
        self.assertRuleHolds(doc_contract.check_versions)

    def test_changes_order_and_frozen_sections(self):
        self.assertRuleHolds(doc_contract.check_changes)

    def test_feedback_log_newest_first(self):
        self.assertRuleHolds(doc_contract.check_feedback_log)

    def test_2099_catalog_matches_roadmap(self):
        self.assertRuleHolds(doc_contract.check_suit_catalog)

    def test_no_run_together_words(self):
        self.assertRuleHolds(doc_contract.check_spacing)


if __name__ == '__main__':
    unittest.main()
