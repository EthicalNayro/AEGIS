from pathlib import Path
from unittest import TestCase


TEMPLATE_PATH = (
    Path(__file__).resolve().parents[1]
    / "templates"
    / "aegis_review"
    / "finding_detail.html"
)


class ReviewFormContractTests(TestCase):
    def test_verdict_survives_submit_button_disable(self):
        template = TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertIn('type="hidden" name="verdict"', template)
        self.assertIn('data-verdict="CORRECT"', template)
        self.assertIn('data-verdict="INCORRECT"', template)
        self.assertNotIn('type="submit" name="verdict"', template)

    def test_review_form_keeps_csrf_protection(self):
        template = TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertIn("{% csrf_token %}", template)
