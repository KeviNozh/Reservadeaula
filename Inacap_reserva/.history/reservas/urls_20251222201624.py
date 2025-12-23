from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'perfiles', views.PerfilUsuarioViewSet)
router.register(r'reservas', views.ReservaViewSet)
router.register(r'notificaciones', views.NotificacionViewSet)
router.register(r'historial', views.HistorialAprobacionViewSet)
router.register(r'equipamientos', views.EquipamientoViewSet)
router.register(r'areas', views.AreaViewSet)

urlpatterns = [
    # === PÁGINAS PRINCIPALES ===
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),  # <-- IMPORTANTE: URL separada
    path('logout/', views.logout_view, name='logout'),
    
    # === VISTAS DE USUARIO ===
    path('espacios/', views.espacios_view, name='espacios'),
    path('reservas/', views.reservas_view, name='reservas'),
    path('notificaciones/', views.notificaciones_view, name='notificaciones'),
    path('calendario/', views.calendario_view, name='calendario'),
    path('crear-reserva/', views.crear_reserva_view, name='crear_reserva'),
    path('reserva-exitosa/', views.reserva_exitosa, name='reserva_exitosa'),
    path('detalle-reserva/', views.detalle_reserva_view, name='detalle_reserva'),
    path('cancelar-reserva/', views.cancelar_reserva_view, name='cancelar_reserva'),
    
    path('reservas/<int:reserva_id>/agregar-elementos/', views.agregar_elementos_reserva, name='agregar_elementos_reserva'),
    path('reservas/<int:reserva_id>/quitar-elemento/<int:elemento_id>/', views.quitar_elemento_reserva, name='quitar_elemento_reserva'),
    path('elementos/disponibilidad/', views.ver_disponibilidad_elementos, name='ver_disponibilidad_elementos'),
    
    # === VISTAS DE ADMINISTRACIÓN ===
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('solicitudes-pendientes/', views.solicitudes_pendientes_view, name='solicitudes_pendientes'),
    path('gestion-espacios/', views.gestion_espacios_view, name='gestion_espacios'),
    path('gestion-usuarios/', views.gestion_usuarios_view, name='gestion_usuarios'),
    path('crear-usuario/', views.crear_usuario_view, name='crear_usuario'),
    path('reportes/', views.reportes_view, name='reportes'),
    path('revisar-solicitud/', views.revisar_solicitud_view, name='revisar_solicitud'),
    path('force-logout/', views.force_logout, name='force_logout'),
    
    # URLs para gestión de elementos (admin)
    path('admin/elementos/', views.lista_elementos, name='lista_elementos'),
    path('admin/elementos/crear/', views.crear_elemento, name='crear_elemento'),
    path('admin/elementos/editar/<int:elemento_id>/', views.editar_elemento, name='editar_elemento'),
    path('admin/elementos/estado/<int:elemento_id>/', views.cambiar_estado_elemento, name='cambiar_estado_elemento'),
    path('admin/elementos/detalle/<int:elemento_id>/', views.detalle_elemento, name='detalle_elemento'),
    
    # === GESTIÓN DE ESPACIOS ===
    path('crear-espacio/', views.crear_espacio_view, name='crear_espacio'),
    path('editar-espacio/', views.editar_espacio_view, name='editar_espacio'),
    
    # === GESTIÓN DE USUARIOS ===
    path('editar-usuario/', views.editar_usuario_view, name='editar_usuario'),
    
    # === NOTIFICACIONES ADMIN ===
    path('notificaciones-admin/', views.notificaciones_admin_view, name='notificaciones_admin'),
    
    # === REPORTES ===
    path('reportes/generar-pdf/<str:tipo_reporte>/', views.generar_reporte_pdf, name='generar_reporte_pdf'),
    
    # URLs para préstamo/devolución (admin)
    path('admin/prestamos/', views.gestionar_prestamos, name='gestionar_prestamos'),
    path('admin/prestamos/registrar/<int:elemento_reserva_id>/', views.registrar_prestamo, name='registrar_prestamo'),
    path('admin/prestamos/devolucion/<int:elemento_reserva_id>/', views.registrar_devolucion, name='registrar_devolucion'),
    
    # === API ENDPOINTS ===
    path('api/', include(router.urls)),
    
    # API - Reservas
    path('api/reservas/', views.get_user_reservas, name='get_reservas'),
    path('api/crear-reserva/', views.crear_reserva_api, name='crear_reserva_api'),
    path('api/reservas/<int:reserva_id>/cancelar/', views.cancelar_reserva_api, name='cancelar_reserva_api'),
    path('api/reservas/<int:reserva_id>/aprobar/', views.aprobar_reserva_api, name='aprobar_reserva_api'),
    path('api/reservas/<int:reserva_id>/rechazar/', views.rechazar_reserva_api, name='rechazar_reserva_api'),
    
    # API - Espacios
    path('api/espacios/', views.get_espacios_disponibles, name='get_espacios'),
    path('api/espacios/crear/', views.crear_espacio_api, name='crear_espacio_api'),
    path('api/espacios/<int:espacio_id>/', views.obtener_espacio_api, name='obtener_espacio_api'),
    path('api/espacios/<int:espacio_id>/actualizar/', views.actualizar_espacio_api, name='actualizar_espacio_api'),
    path('api/espacios/<int:espacio_id>/eliminar/', views.eliminar_espacio_api, name='eliminar_espacio_api'),
    
    # API - Usuarios
    path('api/registro/', views.registro_usuario, name='registro_usuario'),
    path('api/crear-usuario/', views.crear_usuario_api, name='crear_usuario_api'),
    path('api/usuarios/filtrar/', views.filtrar_usuarios_api, name='filtrar_usuarios_api'),
    path('api/usuarios/<int:user_id>/', views.obtener_usuario_api, name='obtener_usuario_api'),
    path('api/usuarios/<int:user_id>/actualizar/', views.actualizar_usuario_api, name='actualizar_usuario_api'),
    path('api/usuarios/<int:user_id>/cambiar-estado/', views.cambiar_estado_usuario_api, name='cambiar_estado_usuario_api'),
    path('api/usuarios/<int:user_id>/cambiar-rol/', views.cambiar_rango_admin_api, name='cambiar_rango_admin_api'),
    path('api/perfiles/', views.obtener_perfiles_usuario_api, name='obtener_perfiles_usuario_api'),
    
    # API - Notificaciones
    path('api/notificaciones/', views.get_notificaciones_usuario, name='get_notificaciones'),
    path('api/notificaciones/contar/', views.contar_notificaciones_no_leidas, name='contar_notificaciones'),
    path('api/notificaciones/marcar-todas-leidas/', views.marcar_todas_leidas, name='marcar_todas_leidas'),
    path('api/notificaciones/<int:notificacion_id>/marcar-leida/', views.marcar_notificacion_leida, name='marcar_notificacion_leida'),
    
    # API - Notificaciones Admin
    path('api/notificaciones-admin/', views.get_notificaciones_admin_api, name='get_notificaciones_admin_api'),
    path('api/notificaciones-admin/contar/', views.contar_notificaciones_admin_no_leidas, name='contar_notificaciones_admin_no_leidas'),
    path('api/notificaciones-admin/marcar-todas-leidas/', views.marcar_todas_notificaciones_admin_leidas, name='marcar_todas_notificaciones_admin_leidas'),
    path('api/notificaciones-admin/<int:notificacion_id>/marcar-leida/', views.marcar_notificacion_admin_leida, name='marcar_notificacion_admin_leida'),
    
    # API - Dashboard y otros
    path('api/dashboard/stats/', views.get_dashboard_stats, name='dashboard_stats'),
    path('api/incidencias/reportar/', views.reportar_incidencia, name='reportar_incidencia'),
    
    # API
    path('api/elemento/<int:elemento_id>/disponibilidad/', views.api_disponibilidad_elemento, name='api_disponibilidad_elemento'),
    
    # API - Testing
    path('api/test-notificaciones-reales/', views.test_notificaciones_reales, name='test_notificaciones_reales'),
    # === Recuperación de contraseña ===
    path('forgot-password/', views.forgot_password_request_view, name='forgot_password_request'),
    path('forgot-password/sent/', views.forgot_password_sent_view, name='forgot_password_sent'),
    path('reset/<str:uidb64>/<str:token>/', views.reset_password_view, name='reset_password'),
    path('reset-otp/', views.reset_via_otp_view, name='reset_via_otp'),
]