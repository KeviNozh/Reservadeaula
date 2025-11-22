from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'perfiles', views.PerfilUsuarioViewSet)
router.register(r'espacios', views.EspacioViewSet)
router.register(r'reservas', views.ReservaViewSet)
router.register(r'notificaciones', views.NotificacionViewSet)
router.register(r'historial', views.HistorialAprobacionViewSet)
router.register(r'equipamientos', views.EquipamientoViewSet)
router.register(r'areas', views.AreaViewSet)


urlpatterns = [
    # Páginas principales - ESTAS DEBEN IR PRIMERO
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('api/', include(router.urls)),
    
    # API endpoints
    path('api/reservas/', views.get_user_reservas, name='get_reservas'),
    path('api/espacios/', views.get_espacios_disponibles, name='get_espacios'),
    path('api/notificaciones/', views.get_notificaciones_usuario, name='get_notificaciones'),
    path('api/incidencias/reportar/', views.reportar_incidencia, name='reportar_incidencia'),
    path('api/dashboard/stats/', views.get_dashboard_stats, name='dashboard_stats'),
    path('api/registro/', views.registro_usuario, name='registro_usuario'),
    path('api/reservas/<int:reserva_id>/cancelar/', views.cancelar_reserva_api, name='cancelar_reserva_api'),
    path('api/crear-reserva/', views.crear_reserva_api, name='crear_reserva_api'),
    
    # API de notificaciones
    path('api/notificaciones/', views.get_notificaciones_usuario, name='get_notificaciones'),
    path('api/notificaciones/contar/', views.contar_notificaciones_no_leidas, name='contar_notificaciones'),
    path('api/notificaciones/marcar-todas-leidas/', views.marcar_todas_leidas, name='marcar_todas_leidas'),
    path('api/notificaciones/<int:notificacion_id>/marcar-leida/', views.marcar_notificacion_leida, name='marcar_notificacion_leida'),
    path('api/reservas/<int:reserva_id>/aprobar/', views.aprobar_reserva_api, name='aprobar_reserva_api'),
    path('api/reservas/<int:reserva_id>/rechazar/', views.rechazar_reserva_api, name='rechazar_reserva_api'),
    # Vistas de páginas HTML
    path('espacios/', views.espacios_view, name='espacios'),
    path('reservas/', views.reservas_view, name='reservas'),
    path('notificaciones/', views.notificaciones_view, name='notificaciones'),
    path('calendario/', views.calendario_view, name='calendario'),
    path('crear-reserva/', views.crear_reserva_view, name='crear_reserva'),
    path('reserva-exitosa/', views.reserva_exitosa, name='reserva_exitosa'),
    path('detalle-reserva/', views.detalle_reserva_view, name='detalle_reserva'),
    path('cancelar-reserva/', views.cancelar_reserva_view, name='cancelar_reserva'),
    
    # Vistas de administración
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('solicitudes-pendientes/', views.solicitudes_pendientes_view, name='solicitudes_pendientes'),
    path('gestion-espacios/', views.gestion_espacios_view, name='gestion_espacios'),
    path('gestion-usuarios/', views.gestion_usuarios_view, name='gestion_usuarios'),
    path('reportes/', views.reportes_view, name='reportes'),
    path('revisar-solicitud/', views.revisar_solicitud_view, name='revisar_solicitud'),
    path('force-logout/', views.force_logout, name='force_logout'),
    
    # APIs para gestión de usuarios
    path('api/usuarios/<int:user_id>/', views.obtener_usuario_api, name='obtener_usuario_api'),
    path('api/usuarios/<int:user_id>/actualizar/', views.actualizar_usuario_api, name='actualizar_usuario_api'),
    path('api/usuarios/<int:user_id>/cambiar-estado/', views.cambiar_estado_usuario_api, name='cambiar_estado_usuario_api'),
    path('api/perfiles/', views.obtener_perfiles_usuario_api, name='obtener_perfiles_usuario_api'),
    
     # Vistas de páginas HTML
path('espacios/crear/', views.crear_espacio_view, name='crear_espacio'),
path('espacios/editar/', views.editar_espacio_view, name='editar_espacio'),
]