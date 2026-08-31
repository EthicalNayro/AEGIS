from pathlib import Path
from unittest import TestCase


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
PLUGIN_ROOT = Path(__file__).resolve().parents[1]


class ObservabilityContractTests(TestCase):
    def test_nginx_requires_django_authorization_before_grafana(self):
        nginx = (
            REPOSITORY_ROOT / "gitops" / "eks-dev" / "nginx.conf"
        ).read_text(encoding="utf-8")

        self.assertIn("location = /plugins/aegis/grafana-auth/", nginx)
        self.assertIn("internal;", nginx)
        self.assertIn("auth_request /plugins/aegis/grafana-auth/;", nginx)
        self.assertIn("proxy_set_header X-WEBAUTH-USER", nginx)

    def test_grafana_stays_non_anonymous_and_viewer_only(self):
        values = (
            REPOSITORY_ROOT
            / "kubernetes"
            / "observability"
            / "kube-prometheus-stack-values.yaml"
        ).read_text(encoding="utf-8")

        self.assertIn("auth.proxy:", values)
        self.assertIn("auto_assign_org_role: Viewer", values)
        self.assertIn("auth.anonymous:\n      enabled: false", values)
        self.assertIn("ingress:\n    enabled: false", values)

    def test_observability_page_embeds_only_the_gateway(self):
        template = (
            PLUGIN_ROOT
            / "templates"
            / "aegis_review"
            / "observability.html"
        ).read_text(encoding="utf-8")

        self.assertIn('id="aegis-grafana-frame"', template)
        self.assertIn("{{ initial_dashboard.url }}", template)
        self.assertNotIn("aegis-monitoring-grafana.monitoring", template)
