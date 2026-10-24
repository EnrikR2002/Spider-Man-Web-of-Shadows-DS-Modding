"""The documentation contract (reference/doc_contract.json) holds for the live docs."""
import unittest

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
