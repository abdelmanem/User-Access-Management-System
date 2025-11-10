from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

def test_login(request):
    """Test view to verify authentication is working."""
    if request.user.is_authenticated:
        return HttpResponse(f"Hello {request.user.username}! You are logged in. <a href='/accounts/logout/'>Logout</a>")
    else:
        return HttpResponse("You are not logged in. <a href='/accounts/login/'>Login</a>")

@login_required
def test_protected(request):
    """Test protected view."""
    return HttpResponse(f"This is a protected page. Hello {request.user.username}! <a href='/accounts/logout/'>Logout</a>")