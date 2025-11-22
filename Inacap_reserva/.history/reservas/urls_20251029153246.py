from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    
    # API endpoints
    path('api/reservas/', views.get_user_reservas, name='get_reservas'),
    path('api/espacios/', views.get_espacios_disponibles, name='get_espacios'),
    path('api/notificaciones/', views.get_notificaciones, name='get_notificaciones'),
    path('api/incidencias/reportar/', views.reportar_incidencia, name='reportar_incidencia'),
    path('api/dashboard/stats/', views.get_dashboard_stats, name='dashboard_stats'),
    
    # Vistas simples
    path('espacios/', views.espacios_view, name='espacios'),
    path('reservas/', views.reservas_view, name='reservas'),
    path('notificaciones/', views.notificaciones_view, name='notificaciones'),
]