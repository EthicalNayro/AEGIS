import hashlib
import logging
import math
from datetime import timedelta

from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
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
RADAR_SCAN_SECONDS = 5.5


def build_sparkline(values, width=160, height=48, padding=4):
    """Return SVG polyline points for a compact, data-backed chart."""

    values = list(values) or [0, 0]
    if len(values) == 1:
        values = values * 2

    minimum = min(values)
    maximum = max(values)
    horizontal_range = width - padding * 2
    vertical_range = height - padding * 2
    points = []

    for index, value in enumerate(values):
        x = padding + index / (len(values) - 1) * horizontal_range
        y = (
            height / 2
            if maximum == minimum
            else padding + (maximum - value) / (maximum - minimum) * vertical_range
        )
        points.append(f'{x:.1f},{y:.1f}')

    return ' '.join(points)


def build_daily_activity(queryset, date_field, days=7):
    """Aggregate a queryset into a complete rolling daily series."""

    today = timezone.localdate()
    first_day = today - timedelta(days=days - 1)
    rows = (
        queryset
        .filter(**{f'{date_field}__date__gte': first_day})
        .annotate(day=TruncDate(date_field))
        .values('day')
        .annotate(total=Count('pk'))
        .order_by('day')
    )
    totals = {row['day']: row['total'] for row in rows}
    return [
        totals.get(first_day + timedelta(days=offset), 0)
        for offset in range(days)
    ]


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
            'reveal_delay': round(
                angle / math.tau * RADAR_SCAN_SECONDS,
                2,
            ),
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
        'aegis_confidence_points': build_sparkline([]),
        'aegis_average_confidence': 0,
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
    confidence_values = [
        finding['confidence_percent']
        for finding in findings[:8]
        if finding.get('confidence_percent') is not None
    ]
    context['aegis_confidence_points'] = build_sparkline(
        reversed(confidence_values)
    )
    context['aegis_average_confidence'] = (
        round(sum(confidence_values) / len(confidence_values))
        if confidence_values
        else 0
    )

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
        incident_activity = build_daily_activity(
            Incident.objects.all(),
            'created',
        )

        context = {
            'open_incidents': open_incidents.count(),
            'open_maintenances': open_maintenances.count(),
            'upcoming_maintenances': upcoming_maintenances.count(),
            'incident_activity_count': sum(incident_activity),
            'incident_activity_points': build_sparkline(incident_activity),
            'component_total_count': 0,
            'component_impacted_count': 0,
            'component_health_percent': 100,
            'component_health_points': build_sparkline([]),
            'audit_activity_count': 0,
            'audit_activity_points': build_sparkline([]),
        }

        if request.user.has_perm('components.view_component'):
            from components.choices import ComponentStatusChoices
            from components.models import Component

            component_statuses = list(
                Component.objects.values_list('status', flat=True)
            )
            status_scores = {
                ComponentStatusChoices.OPERATIONAL: 100,
                ComponentStatusChoices.MAINTENANCE: 72,
                ComponentStatusChoices.DEGRADED_PERFORMANCE: 58,
                ComponentStatusChoices.PARTIAL_OUTAGE: 32,
                ComponentStatusChoices.MAJOR_OUTAGE: 12,
                ComponentStatusChoices.UNKNOWN: 0,
            }
            operational_count = component_statuses.count(
                ComponentStatusChoices.OPERATIONAL
            )
            context['component_total_count'] = len(component_statuses)
            context['component_impacted_count'] = (
                len(component_statuses) - operational_count
            )
            context['component_health_percent'] = (
                round(operational_count / len(component_statuses) * 100)
                if component_statuses
                else 100
            )
            context['component_health_points'] = build_sparkline([
                status_scores.get(status, 0)
                for status in component_statuses
            ])

        if request.user.has_perm('extras.view_objectchange'):
            from extras.models import ObjectChange

            audit_activity = build_daily_activity(
                ObjectChange.objects.restrict(request.user, 'view'),
                'time',
            )
            context['audit_activity_count'] = sum(audit_activity)
            context['audit_activity_points'] = build_sparkline(
                audit_activity
            )

        context.update(get_aegis_dashboard_context(request))

        return render(request, self.template_name, context)
