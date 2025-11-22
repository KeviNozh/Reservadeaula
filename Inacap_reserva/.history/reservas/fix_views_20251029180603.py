# reservas/fix_views.py
from django.shortcuts import redirect

def force_logout(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('login')