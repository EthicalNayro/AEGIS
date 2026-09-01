import math
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from statuspage.views.dashboard import (
    build_radar_points,
    get_aegis_dashboard_context,
)


@override_settings(PLUGINS=["aegis_review"])
class AegisDashboardContextTests(SimpleTestCase):
    def staff_request(self):
        return SimpleNamespace(
            user=SimpleNamespace(
                is_active=True,
                is_staff=True,
            )
        )

    def test_staff_snapshot_uses_real_finding_counts_and_recent_order(self):
        findings = [
            {
                "incident_id": "INC-1",
                "event_time": "2026-08-30T12:00:00Z",
                "review_status": "REVIEWED",
                "severity": "CRITICAL",
            },
            {
                "incident_id": "INC-3",
                "event_time": "2026-09-01T12:00:00Z",
                "review_status": "PENDING_REVIEW",
                "severity": "HIGH",
            },
            {
                "incident_id": "INC-2",
                "event_time": "2026-08-31T12:00:00Z",
                "review_status": "REVIEWED",
                "severity": "CRITICAL",
            },
        ]

        with (
            patch(
                "aegis_review.views.get_observability_dashboards",
                return_value=[{"url": "/plugins/aegis/grafana/d/platform"}],
            ),
            patch(
                "aegis_review.views.scan_all_findings",
                return_value=findings,
            ),
            patch(
                "aegis_review.views.normalize_finding",
                side_effect=lambda finding: finding,
            ),
        ):
            context = get_aegis_dashboard_context(self.staff_request())

        self.assertTrue(context["aegis_data_available"])
        self.assertEqual(context["aegis_total_count"], 3)
        self.assertEqual(context["aegis_pending_count"], 1)
        self.assertEqual(context["aegis_reviewed_count"], 2)
        self.assertEqual(context["aegis_critical_count"], 2)
        self.assertEqual(context["aegis_review_completion"], 67)
        self.assertEqual(
            [
                finding["incident_id"]
                for finding in context["aegis_recent_findings"]
            ],
            ["INC-3", "INC-2", "INC-1"],
        )
        self.assertEqual(
            [point["incident_id"] for point in context["aegis_radar_points"]],
            ["INC-3"],
        )

    def test_non_staff_dashboard_never_scans_security_findings(self):
        request = SimpleNamespace(
            user=SimpleNamespace(
                is_active=True,
                is_staff=False,
            )
        )

        with patch("aegis_review.views.scan_all_findings") as scan:
            context = get_aegis_dashboard_context(request)

        scan.assert_not_called()
        self.assertTrue(context["aegis_restricted"])
        self.assertFalse(context["aegis_data_available"])

    def test_pending_findings_are_mapped_to_severity_distance_bands(self):
        findings = [
            {
                "incident_id": "INC-CRITICAL",
                "review_status": "PENDING_REVIEW",
                "severity": "CRITICAL",
            },
            {
                "incident_id": "INC-HIGH",
                "review_status": "PENDING_REVIEW",
                "severity": "HIGH",
            },
            {
                "incident_id": "INC-MEDIUM",
                "review_status": "PENDING_REVIEW",
                "severity": "MEDIUM",
            },
            {
                "incident_id": "INC-REVIEWED",
                "review_status": "REVIEWED",
                "severity": "CRITICAL",
            },
            {
                "incident_id": "INC-LOW",
                "review_status": "PENDING_REVIEW",
                "severity": "LOW",
            },
        ]

        points = build_radar_points(findings)

        self.assertEqual(len(points), 3)
        distances = {
            point["severity"]: math.hypot(
                point["x"] - 50,
                point["y"] - 50,
            )
            for point in points
        }
        self.assertLessEqual(distances["CRITICAL"], 16.2)
        self.assertGreaterEqual(distances["HIGH"], 21.8)
        self.assertLessEqual(distances["HIGH"], 31.2)
        self.assertGreaterEqual(distances["MEDIUM"], 35.8)
        self.assertTrue(all(
            0 <= point["reveal_delay"] <= 5.5
            for point in points
        ))
