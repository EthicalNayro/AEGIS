from django.urls import path

from . import views


app_name = "aegis_review"


urlpatterns = [
    path(
        "",
        views.findings_list,
        name="findings"
    ),

    path(
        "observability/",
        views.observability,
        name="observability"
    ),

    path(
        "grafana-auth/",
        views.grafana_auth,
        name="grafana_auth"
    ),

    path(
        "<str:incident_id>/",
        views.finding_detail,
        name="finding_detail"
    ),

    path(
        "<str:incident_id>/review/",
        views.review_finding,
        name="review_finding"
    ),
]
