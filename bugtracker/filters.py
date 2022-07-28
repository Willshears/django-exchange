import django_filters

from .models import *

class IssueFilter(django_filters.FilterSet):
    class Meta:
        model = Issue
        fields = ['priority', 'severity', 'author', 'status', 'assigned_to']


