from django.urls import path, include
from django.contrib.auth import views as auth_views
from rest_framework.routers import DefaultRouter
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from . import views

# Configuración de documentación API
schema_view = get_schema_view(
   openapi.Info(
      title="Inacap Reservas API",
      default_version='v1',
      description="API para Sistema de Gestión de Reservas",
      contact=openapi.Contact(email="admin@inacap.cl"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

# Router para API REST
router = DefaultRouter()
router.register(r'espacios', views.EspacioViewSet)
router.register(r'reservas', views.ReservaViewSet)
router.register(r'perfiles', views.PerfilUsuarioViewSet)
router.register(r'equipamiento', views.EquipamientoViewSet)
router.register(r'areas', views.AreaViewSet)
router.register(r'notificaciones', views.NotificacionViewSet)
router.register(r'historial', views.HistorialAprobacionViewSet)

urlpatterns = [
    # Autenticación
    path('login/', auth_views.LoginView.as_view(template_name='reservas/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Vistas de Usuario
    path('', views.dashboard_usuario_view, name='dashboard'),
    path('calendario/', views.calendario_view, name='calendario'),
    path('notificaciones/', views.notificaciones_view, name='notificaciones'),
    path('reservar/nuevo/', views.crear_reserva_view, name='crear_reserva'),
    path('reserva/exito/<int:reserva_id>/', views.reserva_exitosa_view, name='reserva_exitosa'),
    path('reserva/detalle/<int:reserva_id>/', views.detalle_reserva_view, name='detalle_reserva'),
    path('reserva/cancelar/<int:reserva_id>/', views.cancelar_reserva_view, name='cancelar_reserva'),
    
    # Vistas de Administrador
    path('admin/dashboard/', views.dashboard_admin_view, name='admin_dashboard'),
    path('admin/usuarios/', views.gestion_usuarios_view, name='admin_usuarios'),
    path('admin/espacios/', views.gestion_espacios_view, name='admin_espacios'),
    path('admin/solicitudes/', views.solicitudes_pendientes_view, name='solicitudes_pendientes'),
    path('admin/solicitud/<int:reserva_id>/', views.revisar_solicitud_view, name='revisar_solicitud'),
    path('admin/reportes/', views.reportes_view, name='reportes'),
    path('admin/notificaciones/', views.notificaciones_admin_view, name='notificaciones_admin'),
    
    # API y Documentación
    path('api/', include(router.urls)),
    path('api/docs/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]