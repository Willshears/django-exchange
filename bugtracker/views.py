from django.shortcuts import render
from django.http import HttpResponse
from .models import Issue
from .filters import IssueFilter
from django.contrib import messages
# Create your views here.
issues = [
    {
        'author': 'Steve M',
        'title': 'Slower rendering than expected',
        'priority': 'Medium',
        'content': 'An error occurs when attempting to...',
        'date_posted': 'June 28, 2022'
    },
    {
        'author': 'Mike C',
        'title': 'HTTP request error',
        'priority': 'Critical',
        'content': 'An error occurs when attempting to...',
        'date_posted': 'June 27, 2022'
    }
]



def home(request):
    issues = Issue.objects.all()
    myFilter = IssueFilter(request.GET, queryset=issues)
    issues = myFilter.qs
    context = {
        'issues': issues,
        'myFilter':myFilter
    }
    if request.method == 'GET':
        if request.user.is_authenticated == False:
            messages.info(request, 'You need to register and log in to view your reports')

    return render(request, 'bugtracker/home.html', context)



def about(request):
    return render(request, 'bugtracker/about.html', {'title': 'About'})