from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
class Issue(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    date_posted = models.DateTimeField(default=timezone.now)
    priority = models.CharField(max_length=15,
    choices = (
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High")))
    severity = models.CharField(max_length=15,
    choices = (
        ("critical", "Critical"),
        ("major", "Major"),
        ("moderate", "Moderate"),
        ("minor", "Minor"),
        ("cosmetic", "Cosmetic")))
    status = models.CharField(max_length=15,
                                choices=(
                                    ("active", "Active"),
                                    ("resolved", "Resolved")))
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='creator')
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned')

    def __str__(self):
        return self.title


