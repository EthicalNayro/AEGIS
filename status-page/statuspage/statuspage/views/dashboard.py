import hashlib
import logging
import math

from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils import timezone

from incidents.choices import IncidentStatusChoices
from incidents.models import Incident
from maintenances.choices import MaintenanceStatusChoices
from maintenances.models import Maintenance
from statuspage.views import BaseView


__all__ = (
    'DashboardHomeView',
)


logger = logging.getLogger(__name__)


RADAR_SEVERITY_BANDS = {
    'CRITICAL': (8, 16),
    'HIGH': (22, 31),
    'MEDIUM': (36, 44),
}


def build_radar_points(findings, limit=12):
    """Map pending findings to stable severity bands on the radar."""

    points = []

    for finding in findings:
        severity = finding.get('severity', '').upper()

        if (
            finding.get('review_status') != 'PENDING_REVIEW'
            or severity not in RADAR_SEVERITY_BANDS
        ):
            continue

        incident_id = str(finding.get('incident_id', 'Unknown finding'))
        digest = hashlib.sha256(
            f'{incident_id}:{severity}'.encode('utf-8')
        ).digest()
        angle = (
            int.from_bytes(digest[:2], 'big')
            / 65535
            * math.tau
        )
        minimum_radius, maximum_radius = RADAR_SEVERITY_BANDS[severity]
        radius = minimum_radius + (
            digest[2]
            / 255
            * (maximum_radius - minimum_radius)
        )

        points.append({
            'incident_id': incident_id,
            'severity': severity,
            'x': round(50 + math.cos(angle) * radius, 1),
            'y': round(50 + math.sin(angle) * radius, 1),
            'delay': round(-(digest[3] / 255 * 4), 2),
        })

        if len(points) >= limit:
            break

    return points


def get_aegis_dashboard_context(request):
    """Build a resilient, staff-only snapshot for the operations dashboard."""

    context = {
        'aegis_enabled': 'aegis_review' in settings.PLUGINS,
        'aegis_restricted': not (
            request.user.is_active and request.user.is_staff
        ),
        'aegis_data_available': False,
        'aegis_data_error': False,
        'aegis_total_count': 0,
        'aegis_pending_count': 0,
        'aegis_reviewed_count': 0,
        'aegis_critical_count': 0,
        'aegis_review_completion': 0,
        'aegis_recent_findings': [],
        'aegis_radar_points': [],
        'aegis_platform_dashboard': None,
    }

    if not context['aegis_enabled'] or context['aegis_restricted']:
        return context

    from aegis_review.views import (
        get_observability_dashboards,
        normalize_finding,
        scan_all_findings,
    )

    dashboards = get_observability_dashboards()
    if dashboards:
        context['aegis_platform_dashboard'] = dashboards[0]

    try:
        findings = [
            normalize_finding(item)
            for item in scan_all_findings()
        ]
    except (BotoCoreError, ClientError):
        logger.exception(
            'Unable to build the AEGIS dashboard snapshot from DynamoDB'
        )
        context['aegis_data_error'] = True
        return context

    findings.sort(
        key=lambda finding: finding['event_time'],
        reverse=True,
    )

    context['aegis_data_available'] = True
    context['aegis_total_count'] = len(findings)
    context['aegis_pending_count'] = sum(
        finding['review_status'] == 'PENDING_REVIEW'
        for finding in findings
    )
    context['aegis_reviewed_count'] = sum(
        finding['review_status'] == 'REVIEWED'
        for finding in findings
    )
    context['aegis_critical_count'] = sum(
        finding['severity'] == 'CRITICAL'
        for finding in findings
    )
    context['aegis_review_completion'] = (
        round(
            context['aegis_reviewed_count']
            / context['aegis_total_count']
            * 100
        )
        if context['aegis_total_count']
        else 100
    )
    context['aegis_recent_findings'] = findings[:5]
    context['aegis_radar_points'] = build_radar_points(findings)

    return context


class DashboardHomeView(BaseView):
    template_name = 'dashboard/home.html'

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect("login")

        open_incidents = Incident.objects.filter(
            ~Q(status=IncidentStatusChoices.RESOLVED)
        )
        open_maintenances = Maintenance.objects.filter(
            ~Q(status=MaintenanceStatusChoices.COMPLETED)
        )
        upcoming_maintenances = Maintenance.objects.filter(
            ~Q(status=MaintenanceStatusChoices.COMPLETED),
            scheduled_at__gte=timezone.now(),
        )

        context = {
            'open_incidents': open_incidents.count(),
            'open_maintenances': open_maintenances.count(),
            'upcoming_maintenances': upcoming_maintenances.count(),
        }
        context.update(get_aegis_dashboard_context(request))

        return render(request, self.template_name, context)
