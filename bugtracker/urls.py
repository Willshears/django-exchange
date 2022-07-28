from django.urls import path
from . import views
urlpatterns = [
    path('', views.home, name='bugtracker-home'),
    path('about', views.about, name='bugtracker-about'),
]
