from types import SimpleNamespace

from django.test import SimpleTestCase
from django.template.loader import get_template

from components.choices import ComponentStatusChoices
from statuspage.views.home import build_public_status_summary


class PublicStatusSummaryTests(SimpleTestCase):
    def test_public_home_template_compiles(self):
        self.assertIsNotNone(get_template('home.html'))

    def component(self, status):
        return SimpleNamespace(status=status)

    def incident(self, impact):
        return SimpleNamespace(impact=impact)

    def test_missing_public_components_is_not_reported_as_operational(self):
        summary = build_public_status_summary([], [], [])

        self.assertEqual(summary['key'], 'unconfigured')
        self.assertEqual(
            summary['title'],
            'Public monitoring is coming online',
        )

    def test_public_operational_components_report_healthy(self):
        summary = build_public_status_summary(
            [self.component(ComponentStatusChoices.OPERATIONAL)],
            [],
            [],
        )

        self.assertEqual(summary['key'], 'operational')

    def test_public_incident_takes_priority_over_component_health(self):
        summary = build_public_status_summary(
            [self.component(ComponentStatusChoices.OPERATIONAL)],
            [self.incident('critical')],
            [],
        )

        self.assertEqual(summary['key'], 'major-outage')

    def test_active_public_maintenance_is_visible_in_summary(self):
        summary = build_public_status_summary(
            [self.component(ComponentStatusChoices.OPERATIONAL)],
            [],
            [SimpleNamespace()],
        )

        self.assertEqual(summary['key'], 'maintenance')
