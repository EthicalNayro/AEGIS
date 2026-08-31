from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, SimpleTestCase

from aegis_review.views import (
    grafana_auth,
    get_observability_dashboards,
    observability,
)


class GrafanaAuthTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def request_for(self, user):
        request = self.factory.get("/plugins/aegis/grafana-auth/")
        request.user = user
        return request

    def test_anonymous_users_are_rejected(self):
        response = grafana_auth(self.request_for(AnonymousUser()))

        self.assertEqual(response.status_code, 401)
        self.assertNotIn("X-WEBAUTH-USER", response)

    def test_non_staff_users_are_rejected(self):
        user = SimpleNamespace(
            is_authenticated=True,
            is_active=True,
            is_staff=False,
            pk=41,
        )

        response = grafana_auth(self.request_for(user))

        self.assertEqual(response.status_code, 403)
        self.assertNotIn("X-WEBAUTH-USER", response)

    def test_active_staff_receive_isolated_grafana_identity(self):
        user = SimpleNamespace(
            is_authenticated=True,
            is_active=True,
            is_staff=True,
            pk=41,
        )

        response = grafana_auth(self.request_for(user))

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response["X-WEBAUTH-USER"], "aegis-staff-41")
        self.assertEqual(response["Cache-Control"], "no-store")

    def test_dashboard_urls_stay_inside_the_authenticated_gateway(self):
        dashboards = get_observability_dashboards()

        self.assertGreaterEqual(len(dashboards), 5)
        self.assertTrue(
            all(
                dashboard["url"].startswith("/plugins/aegis/grafana/d/")
                for dashboard in dashboards
            )
        )
        self.assertTrue(
            any("var-namespace=aegis-system" in item["url"] for item in dashboards)
        )

    def test_staff_can_render_observability_workspace(self):
        user = SimpleNamespace(
            is_authenticated=True,
            is_active=True,
            is_staff=True,
            pk=41,
            username="analyst",
            config={},
            has_perm=lambda permission: False,
        )
        request = self.request_for(user)
        request.path = "/plugins/aegis/observability/"
        request.resolver_match = SimpleNamespace(url_name="observability")

        with patch(
            "statuspage.context_processors.get_config",
            return_value=SimpleNamespace(),
        ):
            response = observability(request)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Security platform observability")
        self.assertContains(response, "/plugins/aegis/grafana/d/")
