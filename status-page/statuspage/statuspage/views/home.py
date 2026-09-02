from itertools import chain

from django.db.models import Prefetch, Q
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from components.choices import ComponentStatusChoices
from components.models import ComponentGroup, Component
from incidents.choices import IncidentStatusChoices
from incidents.models import Incident
from maintenances.choices import MaintenanceStatusChoices
from maintenances.models import Maintenance
from metrics.models import Metric
from statuspage.config import get_config
from statuspage.views import BaseView


__all__ = (
    'HomeView',
)


def build_public_status_summary(components, open_incidents, open_maintenances):
    """Build a public-safe platform summary from public records only."""
    component_statuses = [component.status for component in components]
    incident_impacts = [incident.impact for incident in open_incidents]

    if (
        ComponentStatusChoices.MAJOR_OUTAGE in component_statuses
        or 'critical' in incident_impacts
    ):
        return {
            'key': 'major-outage',
            'title': 'Major service disruption',
            'summary': 'A critical service-impacting incident is under active investigation.',
            'icon': 'mdi-alert-octagon-outline',
        }
    if (
        ComponentStatusChoices.PARTIAL_OUTAGE in component_statuses
        or 'major' in incident_impacts
    ):
        return {
            'key': 'partial-outage',
            'title': 'Partial service disruption',
            'summary': 'Some public AEGIS services are currently impacted.',
            'icon': 'mdi-alert-circle-outline',
        }
    if (
        ComponentStatusChoices.DEGRADED_PERFORMANCE in component_statuses
        or 'minor' in incident_impacts
    ):
        return {
            'key': 'degraded',
            'title': 'Degraded performance',
            'summary': 'Core services remain available while performance is being investigated.',
            'icon': 'mdi-speedometer-slow',
        }
    if (
        ComponentStatusChoices.MAINTENANCE in component_statuses
        or open_maintenances
    ):
        return {
            'key': 'maintenance',
            'title': 'Maintenance in progress',
            'summary': 'Planned platform work is currently underway.',
            'icon': 'mdi-wrench-clock-outline',
        }
    if not components:
        return {
            'key': 'unconfigured',
            'title': 'Public monitoring is coming online',
            'summary': 'No public service components have been configured yet.',
            'icon': 'mdi-radar',
        }
    if ComponentStatusChoices.UNKNOWN in component_statuses:
        return {
            'key': 'unknown',
            'title': 'Status verification in progress',
            'summary': 'One or more public services are awaiting a current health signal.',
            'icon': 'mdi-help-circle-outline',
        }
    return {
        'key': 'operational',
        'title': 'All systems operational',
        'summary': 'All monitored public AEGIS services are operating normally.',
        'icon': 'mdi-shield-check-outline',
    }


class HomeView(BaseView):
    template_name = 'home.html'

    def get(self, request):
        config = get_config()
        component_groups = ComponentGroup.objects.filter(visibility=True)\
            .prefetch_related(Prefetch('components', queryset=Component.objects.filter(visibility=True)),
                              Prefetch('components__incidents', queryset=Incident.objects.filter(visibility=True)))
        ungrouped_components = Component.objects.filter(component_group=None, visibility=True)\
            .prefetch_related(Prefetch('incidents', queryset=Incident.objects.filter(visibility=True)))

        open_incidents = list(Incident.objects.filter(
            ~Q(status=IncidentStatusChoices.RESOLVED),
            visibility=True,
        ).prefetch_related('updates', 'components'))
        open_maintenances = list(Maintenance.objects.filter(
            ~Q(status=MaintenanceStatusChoices.SCHEDULED),
            ~Q(status=MaintenanceStatusChoices.COMPLETED),
            visibility=True,
        ).prefetch_related('updates', 'components'))
        open_incidents_maintenances = list(chain(open_incidents, open_maintenances))

        upcoming_maintenances = Maintenance.objects.filter(
            status=MaintenanceStatusChoices.SCHEDULED,
            visibility=True,
        )

        datenow = timezone.now().replace(microsecond=0, second=0, minute=0, hour=0)
        datenow_end = timezone.now().replace(microsecond=0, second=59, minute=59, hour=23)
        daterange = datenow - timezone.timedelta(days=7)

        resolved_incidents = Incident.objects.filter(
            status=IncidentStatusChoices.RESOLVED,
            visibility=True,
            last_updated__range=(daterange, datenow_end),
        ).prefetch_related('updates', 'components')
        resolved_maintenances = Maintenance.objects.filter(
            status=MaintenanceStatusChoices.COMPLETED,
            visibility=True,
            last_updated__range=(daterange, datenow_end),
        ).prefetch_related('updates', 'components')

        resolved_incidents_maintenances = []

        date_begin = list(datenow - timezone.timedelta(days=n) for n in range(7))
        date_end = list(datenow_end - timezone.timedelta(days=n) for n in range(7))
        for count in range(7):
            local_list = []
            begin = date_begin[count]
            end = date_end[count]
            for incident in resolved_incidents.filter(created__range=(begin, end)):
                local_list.append(incident)
            for maintenance in resolved_maintenances.filter(created__range=(begin, end)):
                local_list.append(maintenance)

            resolved_incidents_maintenances.append((date_begin[count], local_list))

        public_components = list(
            Component.objects.filter(visibility=True)
            .filter(Q(component_group=None) | Q(component_group__visibility=True))
            .select_related('component_group')
        )
        degraded_components = list(filter(lambda c: c.status == ComponentStatusChoices.DEGRADED_PERFORMANCE, public_components))
        partial_components = list(filter(lambda c: c.status == ComponentStatusChoices.PARTIAL_OUTAGE, public_components))
        major_components = list(filter(lambda c: c.status == ComponentStatusChoices.MAJOR_OUTAGE, public_components))
        maintenance_components = list(filter(lambda c: c.status == ComponentStatusChoices.MAINTENANCE, public_components))

        if len(maintenance_components) > 0:
            status = ('bg-blue-200', 'text-blue-800', 'mdi-wrench text-blue-500', _('Some systems are undergoing '
                                                                                    'maintenance'))
        elif len(major_components) > 0:
            status = ('bg-red-200', 'text-red-800', 'mdi-alert-circle text-red-500', _('There is a major system outage'))
        elif len(partial_components) > 0:
            status = ('bg-orange-200', 'text-orange-800', 'mdi-alert-circle text-orange-500', _('There is a partial '
                                                                                                'system outage'))
        elif len(degraded_components) > 0:
            status = ('bg-yellow-200', 'text-yellow-800', 'mdi-alert-circle text-yellow-500', _('Some systems are '
                                                                                                'having perfomance '
                                                                                                'issues'))
        else:
            status = ('bg-green-200', 'text-green-800', 'mdi-check-circle text-green-500', _('All systems operational'))

        componentgroups_components = list(chain(component_groups, ungrouped_components))

        metrics = Metric.objects.filter(visibility=True)

        should_show_history = True
        incident_sum = sum(list(map(lambda x: len(x[1]), resolved_incidents_maintenances)))
        if incident_sum == 0 and config.HIDE_HISTORY_WHEN_EMPTY:
            should_show_history = False

        public_status = build_public_status_summary(
            public_components,
            open_incidents,
            open_maintenances,
        )
        operational_count = len(list(filter(
            lambda c: c.status == ComponentStatusChoices.OPERATIONAL,
            public_components,
        )))
        impacted_count = len(public_components) - operational_count
        latest_component_update = max(
            (component.last_updated for component in public_components if component.last_updated),
            default=None,
        )
        public_history_days = [
            {
                'date': date,
                'items': items,
                'has_events': bool(items),
            }
            for date, items in resolved_incidents_maintenances
        ]

        return render(request, self.template_name, {
            'component_groups': component_groups,
            'ungrouped_components': ungrouped_components,
            'status': status,
            'open_incidents_maintenances': open_incidents_maintenances,
            'componentgroups_components': componentgroups_components,
            'metrics': metrics,
            'upcoming_maintenances': upcoming_maintenances,
            'resolved_incidents_maintenances': resolved_incidents_maintenances,
            'should_show_history': should_show_history,
            'public_status': public_status,
            'public_components': public_components,
            'public_component_count': len(public_components),
            'public_operational_count': operational_count,
            'public_impacted_count': impacted_count,
            'public_latest_update': latest_component_update,
            'public_history_days': public_history_days,
            'public_history_has_events': incident_sum > 0,
        })
