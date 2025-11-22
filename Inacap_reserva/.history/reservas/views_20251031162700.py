# reservas/views.py
from rest_framework import viewsets, permissions
from django.contrib.auth.models import User
from .models import Espacio, Reserva, PerfilUsuario, Equipamiento, Area, Notificacion, HistorialAprobacion
from .serializers import (
    UserSerializer, PerfilUsuarioSerializer, EquipamientoSerializer, 
    AreaSerializer, EspacioSerializer, ReservaSerializer, 
    NotificacionSerializer, HistorialAprobacionSerializer
)
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
from .models import PerfilUsuario, Reserva, Espacio, Notificacion, Incidencia, Area
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models import Q
import traceback
from .services import NotificacionService
from datetime import datetime, date, time
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from .models import NotificacionAdmin
from .services import NotificacionAdminService

def is_admin_user(user):
    """Verifica si el usuario tiene permisos de administrador"""
    try:
        perfil = PerfilUsuario.objects.get(user=user)
        return perfil.rol in ['Administrativo', 'Investigacion', 'Aprobador']
    except PerfilUsuario.DoesNotExist:
        return False

# === FUNCIONES PARA NOTIFICACIONES DE ADMINISTRADOR ===

def notificar_accion_admin(tipo, titulo, mensaje, usuario_admin=None, usuario_relacionado=None, reserva=None, espacio=None, request=None):
    """
    Función mejorada para notificaciones administrativas
    """
    try:
        print(f"🚀 CREANDO NOTIFICACIÓN ADMIN")
        print(f"   📝 Tipo: {tipo}")
        print(f"   🏷️ Titulo: {titulo}")
        print(f"   📄 Mensaje: {mensaje}")
        print(f"   👨‍💼 Admin: {usuario_admin.username if usuario_admin else 'None'}")
        print(f"   👤 Usuario relacionado: {usuario_relacionado.username if usuario_relacionado else 'None'}")
        print(f"   📅 Reserva: {reserva.id if reserva else 'None'}")
        print(f"   🏢 Espacio: {espacio.nombre if espacio else 'None'}")
        
        # Determinar prioridad según el tipo de notificación
        prioridad_map = {
            'reserva_creada': 'alta',
            'reserva_aprobada': 'media', 
            'reserva_rechazada': 'media',
            'reserva_cancelada': 'media',
            'usuario_registrado': 'media',
            'usuario_actualizado': 'baja',
            'usuario_eliminado': 'alta',
            'espacio_creado': 'media',
            'espacio_actualizado': 'baja',
            'espacio_eliminado': 'alta',
            'incidencia_reportada': 'alta',
            'mantenimiento_programado': 'media',
            'sesion_iniciada': 'baja',
            'sesion_cerrada': 'baja',
            'sistema': 'baja'
        }
        
        prioridad = prioridad_map.get(tipo, 'media')
        print(f"   ⚠️ Prioridad: {prioridad}")
        
        notificacion = NotificacionAdminService.crear_notificacion_admin(
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            prioridad=prioridad,
            usuario_relacionado=usuario_relacionado,
            reserva=reserva,
            espacio=espacio,
            request=request
        )
        
        print(f"   ✅ NOTIFICACIÓN CREADA: ID {notificacion.id if notificacion else 'FALLÓ'}")
        return notificacion
        
    except Exception as e:
        print(f"❌ ERROR CREANDO NOTIFICACIÓN ADMIN: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

# Agrega este decorador a las vistas de gestión de espacios
@login_required
@user_passes_test(is_admin_user, login_url='/dashboard/')
def crear_espacio_view(request):
    """Vista para crear espacio (template)"""
    return render(request, 'reservas/crear_espacio.html')

# --- Vista de Login Modificada ---
@csrf_exempt
def login_view(request):
    if request.method == 'GET':
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, 'reservas/login.html')

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip()
            password = data.get('password')
            user_type = data.get('user_type', 'usuario')  # 'usuario' o 'administrador'

            print(f"🔐 Intento de login: {email} - Tipo: {user_type}")

            if not email or not password:
                return JsonResponse({
                    'success': False,
                    'message': 'Correo electrónico y contraseña son requeridos.'
                }, status=400)

            # Autenticación
            user = authenticate(request, username=email, password=password)
            
            if user is not None and user.is_active:
                try:
                    perfil = PerfilUsuario.objects.get(user=user)
                    print(f"👤 Perfil encontrado: {perfil.rol}")
                    
                    # 🔑 VERIFICACIÓN CORREGIDA DE ACCESO - ACTUALIZADA
                    is_admin_login = user_type == 'administrador'
                    
                    # Roles que pueden acceder como administradores
                    admin_roles = ['Administrativo', 'Investigacion', 'Aprobador']
                    # Roles que pueden acceder como usuarios normales (todos)
                    user_roles = ['Usuario', 'Docente', 'Investigacion', 'Administrativo', 'Aprobador']
                    
                    print(f"🔄 Login tipo: {user_type}, Rol usuario: {perfil.rol}")
                    print(f"🎯 Roles admin: {admin_roles}")
                    print(f"🎯 Roles usuario: {user_roles}")
                    
                    if is_admin_login:
                        # Para login de administrador: solo roles específicos de admin
                        if perfil.rol not in admin_roles:
                            return JsonResponse({
                                'success': False,
                                'message': f'No tienes permisos de administrador. Tu rol es: {perfil.rol}. Solo Personal Administrativo e Investigación pueden acceder aquí.'
                            }, status=403)
                    else:
                        # Para login de usuario: todos los roles pueden acceder
                        if perfil.rol not in user_roles:
                            return JsonResponse({
                                'success': False,
                                'message': f'Rol no autorizado. Tu rol es: {perfil.rol}'
                            }, status=403)

                    # ✅ Login exitoso
                    login(request, user)
                    perfil.ultimo_acceso = timezone.now()
                    perfil.save()

                    print(f"✅ Login exitoso - Redirigiendo a dashboard")

                    # 🔔 NOTIFICAR LOGIN DE ADMINISTRADOR - SI ES ADMIN
                    if perfil.rol in ['Administrativo', 'Investigacion', 'Aprobador']:
                        try:
                            notificar_accion_admin(
                                tipo='sesion_iniciada',
                                titulo='🔐 Sesión de Admin Iniciada',
                                mensaje=f"El administrador {user.username} ha iniciado sesión en el sistema",
                                usuario_admin=user,
                                request=request
                            )
                            print(f"📢 Notificación admin creada para login de {user.username}")
                        except Exception as admin_notif_error:
                            print(f"⚠️ Error en notificación admin login: {admin_notif_error}")
                        except PerfilUsuario.DoesNotExist:
                            pass
                        
                        logout(request)
                        return redirect('login')

                    return JsonResponse({
                        'success': True,
                        'message': 'Login exitoso',
                        'redirect_url': '/dashboard/'
                    })

                except PerfilUsuario.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': 'Error: Perfil de usuario no configurado.'
                    }, status=500)
            else:
                return JsonResponse({
                    'success': False, 
                    'message': 'Credenciales incorrectas o cuenta desactivada'
                }, status=401)

        except Exception as e:
            print(f"💥 Error en login: {str(e)}")
            return JsonResponse({
                'success': False, 
                'message': 'Error interno del servidor'
            }, status=500)

# --- Función de Registro Automático Modificada ---
def registrar_usuario_automatico(email, password, rol='Usuario'):
    """Registra un usuario automáticamente si no existe (insensible a mayúsculas/minúsculas)."""
    try:
        username_base = email.split('@')[0]
        first_name = username_base.capitalize()

        if User.objects.filter(Q(email__iexact=email) | Q(username__iexact=email)).exists():
            print(f"⚠️ Intento de registro automático para usuario existente: {email}")
            return None

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name='Usuario'
        )
        print(f"✅ Usuario base creado: {email}")

        area_default, _ = Area.objects.get_or_create(
            nombre_area="General",
            defaults={'descripcion': 'Área general por defecto'}
        )

        PerfilUsuario.objects.create(
            user=user,
            rol=rol,
            area=area_default,
            departamento='Indefinido',
            estado='activo'
        )
        print(f"✅ PerfilUsuario creado para: {email}")
        return user

    except IntegrityError as e:
         print(f"❌ Error de integridad al registrar usuario {email}: {e}")
         return None
    except Exception as e:
        print(f"❌ Error inesperado registrando usuario {email}: {e}")
        traceback.print_exc()
        return None

# --- Vista del Dashboard Modificada ---
@login_required
def dashboard_view(request):
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        print(f"🎯 Usuario {request.user.username} accediendo a dashboard. Rol: {perfil.rol}")
        
        # Obtener datos REALES de la base de datos
        reservas_usuario = Reserva.objects.filter(solicitante=request.user)
        reservas_activas = reservas_usuario.filter(
            estado='Aprobada', 
            fecha_reserva__gte=timezone.now().date()
        ).count()
        reservas_pendientes = reservas_usuario.filter(estado='Pendiente').count()
        
        # Obtener las 5 reservas más recientes
        reservas_recientes = reservas_usuario.select_related('espacio').order_by('-fecha_solicitud')[:5]
        
        print(f"📊 Estadísticas - Activas: {reservas_activas}, Pendientes: {reservas_pendientes}, Total: {reservas_usuario.count()}")
        
        context = {
            'user': request.user,
            'perfil': perfil,
            'reservas_activas': reservas_activas,
            'reservas_pendientes': reservas_pendientes,
            'total_reservas': reservas_usuario.count(),
            'reservas_recientes': reservas_recientes,
        }
        
        # Redirigir según el rol - ACTUALIZADO
        if perfil.rol in ['Administrativo', 'Investigacion', 'Aprobador']:
            print("➡️ Redirigiendo a dashboard admin")
            return render(request, 'reservas/dashboard_admin.html', context)
        else:
            print("➡️ Redirigiendo a dashboard usuario")
            return render(request, 'reservas/dashboard_usuario.html', context)
            
    except PerfilUsuario.DoesNotExist:
        print(f"❌ Usuario {request.user.username} no tiene perfil")
        logout(request)
        return redirect('login')
    except Exception as e:
        print(f"💥 Error en dashboard: {str(e)}")
        import traceback
        traceback.print_exc()
        logout(request)
        return redirect('login')

@login_required
def reservas_view(request):
    """Vista del historial de reservas con datos REALES"""
    try:
        # Obtener reservas REALES del usuario
        reservas = Reserva.objects.filter(solicitante=request.user).order_by('-fecha_solicitud')
        
        context = {
            'user': request.user,
            'reservas': reservas,
            'reservas_count': reservas.count()
        }
        return render(request, 'reservas/reservas.html', context)
        
    except Exception as e:
        print(f"Error en reservas_view: {e}")
        return render(request, 'reservas/reservas.html', {'reservas': [], 'reservas_count': 0})

@login_required
def calendario_view(request):
    """Vista del calendario con eventos REALES"""
    try:
        # Obtener reservas REALES para el calendario
        reservas_calendario = Reserva.objects.filter(
            solicitante=request.user,
            fecha_reserva__month=timezone.now().month
        ).select_related('espacio')
        
        eventos_calendario = []
        for reserva in reservas_calendario:
            eventos_calendario.append({
                'title': reserva.espacio.nombre,
                'start': f"{reserva.fecha_reserva}T{reserva.hora_inicio}",
                'end': f"{reserva.fecha_reserva}T{reserva.hora_fin}",
                'color': '#10b981' if reserva.estado == 'Aprobada' else '#f59e0b',
                'estado': reserva.estado
            })
        
        context = {
            'user': request.user,
            'eventos': eventos_calendario
        }
        return render(request, 'reservas/calendario.html', context)
        
    except Exception as e:
        print(f"Error en calendario_view: {e}")
        return render(request, 'reservas/calendario.html', {'eventos': []})

# --- Vistas de API ---
@login_required
def get_user_reservas(request):
    try:
        reservas = Reserva.objects.filter(solicitante=request.user).order_by('-fecha_solicitud')
        data = []
        for reserva in reservas:
            data.append({
                'id': reserva.id,
                'espacio': reserva.espacio.nombre,
                'fecha': reserva.fecha_reserva.strftime('%d/%m/%Y'),
                'hora_inicio': reserva.hora_inicio.strftime('%H:%M'),
                'hora_fin': reserva.hora_fin.strftime('%H:%M'),
                'estado': reserva.estado,
                'proposito': reserva.proposito,
                'num_asistentes': reserva.num_asistentes,
                'fecha_solicitud': reserva.fecha_solicitud.strftime('%d/%m/%Y %H:%M')
            })
        return JsonResponse({'success': True, 'reservas': data})
    except Exception as e:
        print(f"❌ Error en get_user_reservas: {e}")
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def get_espacios_disponibles(request):
    try:
        espacios = Espacio.objects.filter(estado='Disponible')
        data = []
        for espacio in espacios:
            data.append({
                'id': espacio.id,
                'nombre': espacio.nombre,
                'tipo': espacio.tipo,
                'edificio': espacio.edificio,
                'piso': espacio.piso,
                'capacidad': espacio.capacidad,
                'descripcion': espacio.descripcion,
                'estado': espacio.estado
            })
        return JsonResponse({'success': True, 'espacios': data})
    except Exception as e:
        print(f"❌ Error en get_espacios_disponibles: {e}")
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def get_notificaciones(request):
    try:
        notificaciones = Notificacion.objects.filter(
            destinatario=request.user,
            leida=False
        ).order_by('-fecha_creacion')[:10]

        data = []
        for notif in notificaciones:
            data.append({
                'id': notif.id,
                'tipo': notif.tipo,
                'titulo': notif.titulo,
                'mensaje': notif.mensaje,
                'fecha': notif.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
                'leida': notif.leida
            })
        return JsonResponse({'success': True, 'notificaciones': data})
    except Exception as e:
        print(f"❌ Error en get_notificaciones: {e}")
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@csrf_exempt
def reportar_incidencia(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            incidencia = Incidencia.objects.create(
                id_usuario=request.user,
                descripcion=data.get('descripcion'),
                prioridad=data.get('prioridad', 'Media'),
                id_espacio_id=data.get('id_espacio'),
                id_equipo_id=data.get('id_equipo')
            )
            
            # 🔔 NOTIFICAR INCIDENCIA REPORTADA
            try:
                notificar_accion_admin(
                    tipo='incidencia_reportada',
                    titulo='🚨 Incidencia Reportada',
                    mensaje=f"El usuario {request.user.username} ha reportado una incidencia: {data.get('descripcion', '')[:100]}...",
                    usuario_relacionado=request.user,
                    request=request
                )
                print(f"📢 Notificación admin creada para incidencia {incidencia.id}")
            except Exception as admin_notif_error:
                print(f"⚠️ Error en notificación admin incidencia: {admin_notif_error}")
                
            return JsonResponse({'success': True, 'incidencia_id': incidencia.id})
        except Exception as e:
            print(f"❌ Error en reportar_incidencia: {e}")
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

@csrf_exempt
def registro_usuario(request):
    """
    Vista para registrar nuevos usuarios desde el formulario de registro - CORREGIDA
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip().lower()
            password = data.get('password')
            first_name = data.get('first_name', '').strip()
            last_name = data.get('last_name', '').strip()
            department = data.get('department', 'Indefinido')
            rol = data.get('rol', 'Usuario')

            # Validaciones básicas
            if not all([email, password, first_name, last_name]):
                return JsonResponse({
                    'success': False,
                    'message': 'Todos los campos son requeridos'
                }, status=400)

            # Verificar si el usuario ya existe
            if User.objects.filter(Q(email__iexact=email) | Q(username__iexact=email)).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Ya existe un usuario con este correo electrónico'
                }, status=400)

            # Crear el usuario
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Obtener o crear área por defecto
            area, _ = Area.objects.get_or_create(
                nombre_area="General",
                defaults={'descripcion': 'Área general por defecto'}
            )

            # Crear perfil de usuario
            PerfilUsuario.objects.create(
                user=user,
                rol=rol,
                area=area,
                departamento=department,
                estado='activo'
            )

            print(f"✅ Nuevo usuario registrado: {email} - {first_name} {last_name} - Rol: {rol}")

            # 🔔 NOTIFICAR NUEVO USUARIO REGISTRADO - CORREGIDO
            try:
                notificar_accion_admin(
                    tipo='usuario_registrado',
                    titulo='👤 Nuevo Usuario Registrado',
                    mensaje=f"El usuario {user.username} ({first_name} {last_name}) se ha registrado en el sistema con rol: {rol}",
                    usuario_relacionado=user,
                    request=request
                )
                print(f"📢 Notificación admin creada para nuevo usuario: {user.username}")
            except Exception as admin_notif_error:
                print(f"⚠️ Error en notificación admin usuario: {admin_notif_error}")

            return JsonResponse({
                'success': True,
                'message': 'Usuario registrado exitosamente. Ahora puedes iniciar sesión.'
            })

        except Exception as e:
            print(f"❌ Error en registro_usuario: {e}")
            return JsonResponse({
                'success': False,
                'message': 'Error interno del servidor al crear la cuenta'
            }, status=500)

    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    }, status=405)
    
@login_required
def get_dashboard_stats(request):
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        stats = {}

        # ACTUALIZADO: Roles de administración
        if perfil.rol in ['Administrativo', 'Investigacion', 'Aprobador']:
            stats['reservas_pendientes_aprobacion'] = Reserva.objects.filter(
                estado='Pendiente'
            ).count()
            stats['total_espacios'] = Espacio.objects.count()
            stats['espacios_disponibles'] = Espacio.objects.filter(estado='Disponible').count()
        else:
            # Usuario normal
            stats['reservas_activas'] = Reserva.objects.filter(
                solicitante=request.user,
                estado='Aprobada',
                fecha_reserva__gte=timezone.now().date()
            ).count()
            stats['reservas_pendientes'] = Reserva.objects.filter(
                solicitante=request.user,
                estado='Pendiente'
            ).count()
            stats['total_reservas'] = Reserva.objects.filter(
                solicitante=request.user
            ).count()

        stats['notificaciones_sin_leer'] = Notificacion.objects.filter(
            destinatario=request.user,
            leida=False
        ).count()

        return JsonResponse({'success': True, 'stats': stats})

    except PerfilUsuario.DoesNotExist:
         print(f"⚠️ Error en get_dashboard_stats: Usuario {request.user.username} sin PerfilUsuario.")
         return JsonResponse({'success': False, 'error': 'Perfil no encontrado'}, status=404)
    except Exception as e:
        print(f"❌ Error en get_dashboard_stats: {e}")
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# --- Vista de Logout ---
def logout_view(request):
    # 🔔 NOTIFICAR LOGOUT DE ADMINISTRADOR
    if request.user.is_authenticated:
        try:
            perfil = PerfilUsuario.objects.get(user=request.user)
            if perfil.rol in ['Administrativo', 'Investigacion', 'Aprobador']:
                notificar_accion_admin(
                    tipo='sesion_cerrada',
                    titulo='🚪 Sesión de Admin Cerrada',
                    mensaje=f"El administrador {request.user.username} ha cerrado sesión",
                    usuario_admin=request.user,
                    request=request
                )
                print(f"📢 Notificación admin creada para logout de {request.user.username}")
        except Exception as admin_notif_error:
            print(f"⚠️ Error en notificación admin logout: {admin_notif_error}")
        except PerfilUsuario.DoesNotExist:
            pass
    
    logout(request)
    return redirect('login')

# --- VISTAS PARA SERVIR TEMPLATES HTML ---
@login_required
def notificaciones_view(request):
    return render(request, 'reservas/notificaciones.html')

@login_required
def crear_reserva_view(request):
    """Vista para crear reserva con espacios disponibles"""
    try:
        # Obtener espacios disponibles
        espacios = Espacio.objects.filter(estado='Disponible').prefetch_related('equipamientos')
        
        # Obtener fecha actual para el formulario
        today = timezone.now().date()
        
        print(f"🏢 Espacios disponibles encontrados: {espacios.count()}")
        
        context = {
            'user': request.user,
            'espacios': espacios,
            'today': today.isoformat()  # Para el campo date min
        }
        return render(request, 'reservas/crear_reserva.html', context)
        
    except Exception as e:
        print(f"❌ Error en crear_reserva_view: {e}")
        import traceback
        traceback.print_exc()
        # Si hay error, pasar lista vacía
        context = {
            'user': request.user,
            'espacios': [],
            'today': timezone.now().date().isoformat()
        }
        return render(request, 'reservas/crear_reserva.html', context)

@login_required
def reserva_exitosa(request):
    """Vista de confirmación de reserva exitosa con datos REALES"""
    reserva_id = request.GET.get('reserva_id')
    print(f"🔍 ID de reserva recibido: {reserva_id}")
    
    try:
        if reserva_id:
            # Obtener la reserva específica
            reserva = Reserva.objects.select_related('espacio').get(id=reserva_id, solicitante=request.user)
            print(f"✅ Reserva encontrada: {reserva.id} - {reserva.espacio.nombre}")
        else:
            # Obtener la última reserva del usuario
            reserva = Reserva.objects.select_related('espacio').filter(
                solicitante=request.user
            ).order_by('-fecha_solicitud').first()
            print(f"📋 Última reserva encontrada: {reserva.id if reserva else 'None'}")
        
        context = {
            'user': request.user,
            'reserva': reserva
        }
        return render(request, 'reservas/reserva_exitosa.html', context)
        
    except Reserva.DoesNotExist:
        print(f"❌ Reserva no encontrada: ID {reserva_id}")
        # Si no hay reserva, mostrar página genérica
        context = {
            'user': request.user,
            'reserva': None
        }
        return render(request, 'reservas/reserva_exitosa.html', context)
    except Exception as e:
        print(f"💥 Error en reserva_exitosa: {e}")
        import traceback
        traceback.print_exc()
        context = {
            'user': request.user,
            'reserva': None
        }
        return render(request, 'reservas/reserva_exitosa.html', context)

@login_required
def detalle_reserva_view(request):
    """Vista de detalle de reserva con datos REALES de la BD"""
    reserva_id = request.GET.get('id')
    
    try:
        # Obtener la reserva específica del usuario
        reserva = Reserva.objects.select_related('espacio', 'solicitante').get(
            id=reserva_id, 
            solicitante=request.user
        )
        
        # Formatear datos para el template
        context = {
            'user': request.user,
            'reserva': reserva,
            'reserva_data': {
                'id': reserva.id,
                'estado': reserva.estado.lower(),
                'espacio': {
                    'id': reserva.espacio.id,
                    'nombre': reserva.espacio.nombre,
                    'ubicacion': f"{reserva.espacio.edificio or 'Edificio Principal'}, Piso {reserva.espacio.piso or 'N/A'}",
                    'capacidad': f"{reserva.espacio.capacidad} personas",
                    'equipamiento': ', '.join([eq.nombre_equipo for eq in reserva.espacio.equipamientos.all()]) or "Equipamiento básico",
                    'descripcion': reserva.espacio.descripcion or "Espacio disponible para reuniones y eventos."
                },
                'fecha': reserva.fecha_reserva.strftime('%A, %d de %B %Y'),
                'horario': f"{reserva.hora_inicio.strftime('%H:%M')} - {reserva.hora_fin.strftime('%H:%M')}",
                'duracion': calcular_duracion(reserva.hora_inicio, reserva.hora_fin),
                'proposito': reserva.proposito,
                'asistentes': f"{reserva.num_asistentes} personas",
                'usuario': {
                    'nombre': f"{reserva.solicitante.first_name} {reserva.solicitante.last_name}",
                    'email': reserva.solicitante.email,
                    'telefono': 'N/A'
                },
                'fechaSolicitud': reserva.fecha_solicitud.strftime('%d de %B, %H:%M'),
                'comentariosAdmin': reserva.comentario_admin or "Sin comentarios adicionales."
            }
        }
        return render(request, 'reservas/detalle_reserva.html', context)
        
    except Reserva.DoesNotExist:
        messages.error(request, 'Reserva no encontrada.')
        return redirect('reservas')
    except Exception as e:
        print(f"Error en detalle_reserva_view: {e}")
        messages.error(request, 'Error al cargar los detalles de la reserva.')
        return redirect('reservas')

def calcular_duracion(hora_inicio, hora_fin):
    """Calcular la duración en formato legible"""
    if isinstance(hora_inicio, str):
        hora_inicio = datetime.strptime(hora_inicio, '%H:%M:%S').time()
    if isinstance(hora_fin, str):
        hora_fin = datetime.strptime(hora_fin, '%H:%M:%S').time()
    
    diferencia = datetime.combine(date.today(), hora_fin) - datetime.combine(date.today(), hora_inicio)
    horas = diferencia.seconds // 3600
    minutos = (diferencia.seconds % 3600) // 60
    
    if horas > 0:
        return f"{horas} hora{'s' if horas > 1 else ''} {minutos} minuto{'s' if minutos > 1 else ''}"
    else:
        return f"{minutos} minutos"

@login_required
def cancelar_reserva_view(request):
    return render(request, 'reservas/cancelar_reserva.html')

# --- Vistas de Administración - ACTUALIZADAS ---
@login_required
def admin_dashboard_view(request):
    """Dashboard para administradores - CON DATOS REALES"""
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol not in ['Administrativo', 'Investigacion', 'Aprobador']:
            return redirect('dashboard')
        
        # Datos REALES de la base de datos
        total_reservas = Reserva.objects.count()
        reservas_pendientes = Reserva.objects.filter(estado='Pendiente').count()
        total_espacios = Espacio.objects.count()
        usuarios_activos = User.objects.filter(is_active=True).count()
        
        # Reservas recientes (últimas 5)
        reservas_recientes = Reserva.objects.select_related('solicitante', 'espacio').order_by('-fecha_solicitud')[:5]
        
        # Notificaciones sin leer
        notificaciones_sin_leer = Notificacion.objects.filter(
            destinatario=request.user,
            leida=False
        ).count()
        
        context = {
            'user': request.user,
            'perfil': perfil,
            'total_reservas': total_reservas,
            'reservas_pendientes': reservas_pendientes,
            'total_espacios': total_espacios,
            'usuarios_activos': usuarios_activos,
            'reservas_recientes': reservas_recientes,
            'notificaciones_sin_leer': notificaciones_sin_leer,
        }
        return render(request, 'reservas/dashboard_admin.html', context)
    except PerfilUsuario.DoesNotExist:
        return redirect('login')

@login_required
def solicitudes_pendientes_view(request):
    """Vista de solicitudes pendientes para administradores - CON DATOS REALES"""
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol not in ['Administrativo', 'Investigacion', 'Aprobador']:
            return redirect('dashboard')
        
        # Obtener solicitudes REALES pendientes
        solicitudes = Reserva.objects.filter(estado='Pendiente').select_related('solicitante', 'espacio')
        
        context = {
            'user': request.user,
            'solicitudes': solicitudes
        }
        return render(request, 'reservas/solicitudes_pendientes.html', context)
    except PerfilUsuario.DoesNotExist:
        return redirect('login')

@login_required
def gestion_espacios_view(request):
    """Vista de gestión de espacios para administradores - CON DATOS REALES"""
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol not in ['Administrativo', 'Investigacion', 'Aprobador']:
            return redirect('dashboard')
        
        # Obtener todos los espacios
        espacios = Espacio.objects.all().order_by('nombre')
        
        context = {
            'user': request.user,
            'espacios': espacios
        }
        return render(request, 'reservas/gestion_espacios.html', context)
    except PerfilUsuario.DoesNotExist:
        return redirect('login')

@login_required
def gestion_usuarios_view(request):
    """Vista de gestión de usuarios para administradores - CON DATOS REALES"""
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol not in ['Administrativo', 'Investigacion', 'Aprobador']:
            return redirect('dashboard')
        
        # Obtener TODOS los usuarios (activos e inactivos) con sus perfiles
        usuarios = User.objects.all().select_related('perfilusuario').order_by('-date_joined')
        
        context = {
            'user': request.user,
            'usuarios': usuarios
        }
        return render(request, 'reservas/gestion_usuarios.html', context)
    except PerfilUsuario.DoesNotExist:
        return redirect('login')

@login_required
def reportes_view(request):
    """Vista de reportes para administradores - CON DATOS REALES"""
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol not in ['Administrativo', 'Investigacion', 'Aprobador']:
            return redirect('dashboard')
        
        # Datos REALES para reportes
        total_reservas = Reserva.objects.count()
        usuarios_activos = User.objects.filter(is_active=True).count()
        total_espacios = Espacio.objects.count()
        
        # Calcular tasa de aprobación
        reservas_aprobadas = Reserva.objects.filter(estado='Aprobada').count()
        tasa_aprobacion = round((reservas_aprobadas / total_reservas * 100) if total_reservas > 0 else 0)
        
        # Estadísticas de uso de espacios (TOP 5)
        espacios_mas_usados = Espacio.objects.annotate(
            num_reservas=models.Count('reserva')
        ).order_by('-num_reservas')[:5]
        
        # Reservas por estado
        reservas_pendientes = Reserva.objects.filter(estado='Pendiente').count()
        reservas_rechazadas = Reserva.objects.filter(estado='Rechazada').count()
        reservas_canceladas = Reserva.objects.filter(estado='Cancelada').count()
        
        # Usuarios más activos (TOP 5)
        usuarios_activos_top = User.objects.annotate(
            num_reservas=models.Count('reservas_solicitadas')
        ).order_by('-num_reservas')[:5]
        
        # Reservas del mes actual
        mes_actual = timezone.now().month
        año_actual = timezone.now().year
        reservas_mes_actual = Reserva.objects.filter(
            fecha_solicitud__month=mes_actual,
            fecha_solicitud__year=año_actual
        ).count()
        
        context = {
            'user': request.user,
            'total_reservas': total_reservas,
            'usuarios_activos': usuarios_activos,
            'total_espacios': total_espacios,
            'tasa_aprobacion': tasa_aprobacion,
            'reservas_aprobadas': reservas_aprobadas,
            'reservas_pendientes': reservas_pendientes,
            'reservas_rechazadas': reservas_rechazadas,
            'reservas_canceladas': reservas_canceladas,
            'reservas_mes_actual': reservas_mes_actual,
            'espacios_mas_usados': espacios_mas_usados,
            'usuarios_activos_top': usuarios_activos_top,
        }
        return render(request, 'reservas/reportes.html', context)
    except PerfilUsuario.DoesNotExist:
        return redirect('login')

@login_required
def revisar_solicitud_view(request):
    """Vista para revisar una solicitud específica"""
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        # ACTUALIZADO: Roles que pueden acceder
        if perfil.rol not in ['Administrativo', 'Investigacion', 'Aprobador']:
            return redirect('dashboard')
        
        solicitud_id = request.GET.get('id')
        if solicitud_id:
            solicitud = Reserva.objects.get(id=solicitud_id)
            context = {
                'user': request.user,
                'solicitud': solicitud
            }
            return render(request, 'reservas/revisar_solicitud.html', context)
        else:
            return redirect('solicitudes_pendientes')
    except Reserva.DoesNotExist:
        return redirect('solicitudes_pendientes')
    except PerfilUsuario.DoesNotExist:
        return redirect('login')

@login_required
@csrf_exempt
def cancelar_reserva_api(request, reserva_id):
    if request.method == 'POST':
        try:
            reserva = Reserva.objects.get(id=reserva_id, solicitante=request.user)
            
            if reserva.estado in ['Pendiente', 'Aprobada']:
                estado_anterior = reserva.estado
                reserva.estado = 'Cancelada'
                reserva.save()
                
                # Crear notificación al usuario
                Notificacion.objects.create(
                    destinatario=request.user,
                    tipo='reserva_cancelada',
                    titulo='Reserva Cancelada',
                    mensaje=f'Tu reserva para {reserva.espacio.nombre} ha sido cancelada.',
                    leida=False
                )
                
                # 🔔 NOTIFICAR A ADMINISTRADORES SOBRE CANCELACIÓN
                try:
                    notificar_accion_admin(
                        tipo='reserva_cancelada',
                        titulo='📝 Reserva Cancelada por Usuario',
                        mensaje=f"El usuario {request.user.username} ha cancelado la reserva #{reserva.id} para {reserva.espacio.nombre} (estado anterior: {estado_anterior})",
                        usuario_relacionado=request.user,
                        reserva=reserva,
                        request=request
                    )
                    print(f"📢 Notificación admin creada para cancelación de reserva {reserva.id}")
                except Exception as admin_notif_error:
                    print(f"⚠️ Error en notificación admin cancelación: {admin_notif_error}")
                
                return JsonResponse({'success': True, 'message': 'Reserva cancelada exitosamente'})
            else:
                return JsonResponse({'success': False, 'error': 'No se puede cancelar esta reserva'})
                
        except Reserva.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Reserva no encontrada'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@login_required
@csrf_exempt
def crear_reserva_api(request):
    """API para crear reservas REALES en la base de datos - VERSIÓN MEJORADA"""
    if request.method == 'POST':
        try:
            print("🔍 Llegó la solicitud POST a crear_reserva_api")
            data = json.loads(request.body)
            print(f"📝 Datos recibidos para crear reserva: {data}")
            
            # Validar datos requeridos
            required_fields = ['espacio_id', 'fecha_reserva', 'hora_inicio', 'hora_fin', 'proposito', 'num_asistentes']
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({
                        'success': False, 
                        'message': f'El campo {field} es requerido'
                    }, status=400)

            # Verificar que el espacio existe
            try:
                espacio = Espacio.objects.get(id=data['espacio_id'])
                print(f"🏢 Espacio encontrado: {espacio.nombre}")
            except Espacio.DoesNotExist:
                print(f"❌ Espacio no encontrado: ID {data['espacio_id']}")
                return JsonResponse({
                    'success': False,
                    'message': 'El espacio seleccionado no existe'
                }, status=400)

            # Crear la reserva REAL
            reserva = Reserva.objects.create(
                espacio=espacio,
                solicitante=request.user,
                fecha_reserva=data['fecha_reserva'],
                hora_inicio=data['hora_inicio'],
                hora_fin=data['hora_fin'],
                proposito=data['proposito'],
                num_asistentes=data['num_asistentes'],
                estado='Pendiente'
            )
            
            print(f"✅ Reserva REAL creada: ID {reserva.id} para {request.user.username}")
            print(f"📅 Detalles: {reserva.espacio.nombre} - {reserva.fecha_reserva} - {reserva.hora_inicio} a {reserva.hora_fin}")
            
            # NOTIFICAR AL USUARIO
            try:
                notificacion = NotificacionService.notificar_creacion_reserva(reserva)
                if notificacion:
                    print(f"📧 Notificación de creación enviada exitosamente: {notificacion.id}")
                else:
                    print("⚠️ No se pudo crear la notificación de creación")
            except Exception as notif_error:
                print(f"⚠️ Error en notificación: {notif_error}")
                # No fallar la reserva por error en notificación
                
            # 🔔 NOTIFICAR A ADMINISTRADORES SOBRE NUEVA RESERVA
            try:
                notificar_accion_admin(
                    tipo='reserva_creada',
                    titulo='📋 Nueva Reserva Creada',
                    mensaje=f"El usuario {request.user.username} ha creado una nueva reserva para {reserva.espacio.nombre} el {reserva.fecha_reserva.strftime('%d/%m/%Y')} de {reserva.hora_inicio.strftime('%H:%M')} a {reserva.hora_fin.strftime('%H:%M')}",
                    usuario_relacionado=request.user,
                    reserva=reserva,
                    request=request
                )
                print(f"📢 Notificación admin creada para nueva reserva {reserva.id}")
            except Exception as admin_notif_error:
                print(f"⚠️ Error en notificación admin: {admin_notif_error}")
            
            return JsonResponse({
                'success': True,
                'message': 'Reserva creada exitosamente',
                'reserva_id': reserva.id,
                'notificacion_creada': notificacion is not None,
                'redirect_url': f'/reserva-exitosa/?reserva_id={reserva.id}'
            })

        except json.JSONDecodeError as e:
            print(f"❌ Error JSON: {e}")
            return JsonResponse({
                'success': False,
                'message': 'Error en los datos enviados'
            }, status=400)
        except Exception as e:
            print(f"❌ Error creando reserva: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'message': f'Error interno del servidor: {str(e)}'
            }, status=500)

    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    }, status=405)

@login_required
def espacios_view(request):
    """Vista para mostrar los espacios disponibles"""
    try:
        espacios = Espacio.objects.filter(estado='Disponible').prefetch_related('equipamientos')
        print(f"🏢 Espacios encontrados: {espacios.count()}")
        
        context = {
            'user': request.user,
            'espacios': espacios
        }
        return render(request, 'reservas/espacios.html', context)
    except Exception as e:
        print(f"❌ Error en espacios_view: {e}")
        return render(request, 'reservas/espacios.html', {'espacios': []})

@login_required
def notificaciones_view(request):
    """Vista para mostrar notificaciones"""
    try:
        notificaciones = Notificacion.objects.filter(
            destinatario=request.user
        ).order_by('-fecha_creacion')[:10]
        
        context = {
            'user': request.user,
            'notificaciones': notificaciones
        }
        return render(request, 'reservas/notificaciones.html', context)
    except Exception as e:
        print(f"Error en notificaciones_view: {e}")
        return render(request, 'reservas/notificaciones.html', {'notificaciones': []})

@login_required
@csrf_exempt
def aprobar_reserva_api(request, reserva_id):
    """API para que administradores aprueben reservas - VERSIÓN CORREGIDA"""
    if request.method == 'POST':
        try:
            # Verificar que el usuario es administrador - ACTUALIZADO
            perfil = PerfilUsuario.objects.get(user=request.user)
            if perfil.rol not in ['Administrativo', 'Investigacion', 'Aprobador']:
                return JsonResponse({
                    'success': False, 
                    'error': 'No tienes permisos para aprobar reservas'
                }, status=403)
            
            # Obtener datos del cuerpo de la solicitud
            data = json.loads(request.body) if request.body else {}
            comentario_admin = data.get('comentario', '')
            
            reserva = Reserva.objects.get(id=reserva_id)
            estado_anterior = reserva.estado
            reserva.estado = 'Aprobada'
            reserva.id_aprobador = request.user
            reserva.comentario_admin = comentario_admin
            reserva.save()
            
            print(f"✅ Reserva {reserva_id} aprobada por {request.user.username}")
            
            # NOTIFICAR AL USUARIO
            notificacion = NotificacionService.notificar_aprobacion_reserva(
                reserva, 
                comentario_admin
            )
            
            # 🔔 NOTIFICAR A ADMINISTRADORES SOBRE APROBACIÓN
            try:
                notificar_accion_admin(
                    tipo='reserva_aprobada',
                    titulo='✅ Reserva Aprobada',
                    mensaje=f"El administrador {request.user.username} ha aprobado la reserva #{reserva.id} de {reserva.solicitante.username} para {reserva.espacio.nombre}",
                    usuario_admin=request.user,
                    usuario_relacionado=reserva.solicitante,
                    reserva=reserva,
                    request=request
                )
                print(f"📢 Notificación admin creada para aprobación de reserva {reserva.id}")
            except Exception as admin_notif_error:
                print(f"⚠️ Error en notificación admin aprobación: {admin_notif_error}")
            
            # Crear historial
            HistorialAprobacion.objects.create(
                reserva=reserva,
                usuario_admin=request.user,
                tipo_accion='Aprobada',
                motivo=comentario_admin
            )
            
            return JsonResponse({
                'success': True, 
                'message': 'Reserva aprobada exitosamente',
                'notificacion_creada': notificacion is not None
            })
            
        except Reserva.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Reserva no encontrada'})
        except Exception as e:
            print(f"❌ Error en aprobar_reserva_api: {e}")
            return JsonResponse({'success': False, 'error': str(e)})

@login_required
@csrf_exempt
def rechazar_reserva_api(request, reserva_id):
    """API para que administradores rechacen reservas - VERSIÓN CORREGIDA"""
    if request.method == 'POST':
        try:
            # Verificar que el usuario es administrador - ACTUALIZADO
            perfil = PerfilUsuario.objects.get(user=request.user)
            if perfil.rol not in ['Administrativo', 'Investigacion', 'Aprobador']:
                return JsonResponse({
                    'success': False, 
                    'error': 'No tienes permisos para rechazar reservas'
                }, status=403)
            
            # Obtener datos del cuerpo de la solicitud
            data = json.loads(request.body) if request.body else {}
            motivo = data.get('motivo', 'Sin motivo especificado')
            
            reserva = Reserva.objects.get(id=reserva_id)
            estado_anterior = reserva.estado
            reserva.estado = 'Rechazada'
            reserva.id_aprobador = request.user
            reserva.comentario_admin = motivo
            reserva.save()
            
            print(f"❌ Reserva {reserva_id} rechazada por {request.user.username}")
            
            # NOTIFICAR AL USUARIO
            notificacion = NotificacionService.notificar_rechazo_reserva(
                reserva, 
                motivo
            )
            
            # 🔔 NOTIFICAR A ADMINISTRADORES SOBRE RECHAZO
            try:
                notificar_accion_admin(
                    tipo='reserva_rechazada',
                    titulo='❌ Reserva Rechazada',
                    mensaje=f"El administrador {request.user.username} ha rechazado la reserva #{reserva.id} de {reserva.solicitante.username} para {reserva.espacio.nombre}. Motivo: {motivo}",
                    usuario_admin=request.user,
                    usuario_relacionado=reserva.solicitante,
                    reserva=reserva,
                    request=request
                )
                print(f"📢 Notificación admin creada para rechazo de reserva {reserva.id}")
            except Exception as admin_notif_error:
                print(f"⚠️ Error en notificación admin rechazo: {admin_notif_error}")
            
            # Crear historial
            HistorialAprobacion.objects.create(
                reserva=reserva,
                usuario_admin=request.user,
                tipo_accion='Rechazada',
                motivo=motivo
            )
            
            return JsonResponse({
                'success': True, 
                'message': 'Reserva rechazada exitosamente',
                'notificacion_creada': notificacion is not None
            })
            
        except Reserva.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Reserva no encontrada'})
        except Exception as e:
            print(f"❌ Error en rechazar_reserva_api: {e}")
            return JsonResponse({'success': False, 'error': str(e)})

def force_logout(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('login')

# Agregar estas vistas al final del views.py existente

@login_required
@require_http_methods(["GET"])
def get_notificaciones_usuario(request):
    """
    API para obtener las notificaciones del usuario - VERSIÓN MEJORADA
    """
    try:
        # Obtener parámetros de la solicitud
        no_leidas = request.GET.get('no_leidas', 'false').lower() == 'true'
        limite = int(request.GET.get('limite', 20))
        
        # Obtener notificaciones usando el servicio
        notificaciones = NotificacionService.obtener_notificaciones_usuario(
            usuario=request.user,
            no_leidas=no_leidas,
            limite=limite
        )
        
        # Formatear respuesta con más información
        data = []
        for notif in notificaciones:
            notif_data = {
                'id': notif.id,
                'tipo': notif.tipo,
                'titulo': notif.titulo,
                'mensaje': notif.mensaje,
                'leida': notif.leida,
                'fecha_creacion': notif.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
                'fecha_creacion_formateada': notif.get_fecha_creacion_formateada(),
            }
            
            # Incluir información de la reserva si existe
            if notif.reserva:
                notif_data.update({
                    'reserva_id': notif.reserva.id,
                    'espacio_nombre': notif.reserva.espacio.nombre,
                    'fecha_reserva': notif.reserva.fecha_reserva.strftime('%d/%m/%Y') if notif.reserva.fecha_reserva else None,
                    'estado_reserva': notif.reserva.estado
                })
            
            data.append(notif_data)
        
        # Contar notificaciones no leídas
        total_no_leidas = NotificacionService.contar_notificaciones_no_leidas(request.user)
        
        return JsonResponse({
            'success': True,
            'notificaciones': data,
            'total_no_leidas': total_no_leidas,
            'total': len(data)
        })
        
    except Exception as e:
        print(f"❌ Error en get_notificaciones_usuario: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error al obtener notificaciones',
            'notificaciones': [],
            'total_no_leidas': 0,
            'total': 0
        })

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def marcar_notificacion_leida(request, notificacion_id):
    """
    API para marcar una notificación como leída
    """
    try:
        # Verificar que la notificación pertenece al usuario
        notificacion = Notificacion.objects.get(
            id=notificacion_id,
            destinatario=request.user
        )
        
        # Marcar como leída usando el servicio
        NotificacionService.marcar_como_leida(notificacion_id)
        
        return JsonResponse({
            'success': True,
            'message': 'Notificación marcada como leída'
        })
        
    except Notificacion.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Notificación no encontrada'
        }, status=404)
    except Exception as e:
        print(f"❌ Error en marcar_notificacion_leida: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error al marcar notificación como leída'
        }, status=500)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def marcar_todas_leidas(request):
    """
    API para marcar todas las notificaciones como leídas
    """
    try:
        count = NotificacionService.marcar_todas_como_leidas(request.user)
        
        return JsonResponse({
            'success': True,
            'message': f'{count} notificaciones marcadas como leídas',
            'count': count
        })
        
    except Exception as e:
        print(f"❌ Error en marcar_todas_leidas: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error al marcar notificaciones como leídas'
        }, status=500)

@login_required
@require_http_methods(["GET"])
def contar_notificaciones_no_leidas(request):
    """
    API para contar notificaciones no leídas
    """
    try:
        count = NotificacionService.contar_notificaciones_no_leidas(request.user)
        
        return JsonResponse({
            'success': True,
            'count': count
        })
        
    except Exception as e:
        print(f"❌ Error en contar_notificaciones_no_leidas: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error al contar notificaciones'
        }, status=500)

# === VISTAS PARA GESTIÓN DE ESPACIOS ===

@login_required
def crear_espacio_view(request):
    """Vista para crear espacio (template)"""
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol not in ['Administrativo', 'Investigacion', 'Aprobador']:
            return redirect('dashboard')
        
        return render(request, 'reservas/crear_espacio.html')
    except PerfilUsuario.DoesNotExist:
        return redirect('login')

@login_required
def editar_espacio_view(request):
    """Vista para editar espacio (template)"""
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol not in ['Administrativo', 'Investigacion', 'Aprobador']:
            return redirect('dashboard')
        
        espacio_id = request.GET.get('id')
        if not espacio_id:
            return redirect('gestion_espacios')
            
        # Verificar que el espacio existe
        espacio = Espacio.objects.get(id=espacio_id)
        
        context = {
            'user': request.user,
            'espacio_id': espacio_id,
            'espacio': espacio
        }
        return render(request, 'reservas/editar_espacio.html', context)
        
    except Espacio.DoesNotExist:
        messages.error(request, 'Espacio no encontrado')
        return redirect('gestion_espacios')
    except PerfilUsuario.DoesNotExist:
        return redirect('login')

# APIs para gestión de espacios
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def crear_espacio_api(request):
    """API para crear espacios - VERSIÓN CORREGIDA"""
    print("🔍 Llegó solicitud a crear_espacio_api")
    
    try:
        # Verificar permisos de administrador
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol not in ['Administrativo', 'Investigacion', 'Aprobador']:
            print("❌ Usuario sin permisos de administrador")
            return JsonResponse({
                'success': False, 
                'error': 'No tienes permisos para crear espacios'
            }, status=403)
        
        # Parsear datos
        data = json.loads(request.body)
        print(f"📝 Datos recibidos: {data}")
        
        # Validaciones
        required_fields = ['nombre', 'tipo', 'capacidad']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False, 
                    'error': f'El campo {field} es requerido'
                }, status=400)
        
        # Validar capacidad
        try:
            capacidad = int(data['capacidad'])
            if capacidad <= 0:
                return JsonResponse({
                    'success': False, 
                    'error': 'La capacidad debe ser mayor a 0'
                }, status=400)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False, 
                'error': 'La capacidad debe ser un número válido'
            }, status=400)
        
        # Crear espacio
        espacio = Espacio.objects.create(
            nombre=data['nombre'].strip(),
            tipo=data['tipo'],
            capacidad=capacidad,
            edificio=data.get('edificio', '').strip() or None,
            piso=data.get('piso'),
            descripcion=data.get('descripcion', '').strip() or None,
            estado=data.get('estado', 'Disponible')
        )
        
        print(f"✅ Espacio creado exitosamente: {espacio.id} - {espacio.nombre}")
        
        # Crear espacio
        espacio = Espacio.objects.create(
            nombre=data['nombre'].strip(),
            tipo=data['tipo'],
            capacidad=capacidad,
            edificio=data.get('edificio', '').strip() or None,
            piso=data.get('piso'),
            descripcion=data.get('descripcion', '').strip() or None,
            estado=data.get('estado', 'Disponible')
        )

        print(f"✅ Espacio creado exitosamente: {espacio.id} - {espacio.nombre}")

        # 🔔 NOTIFICAR A ADMINISTRADORES SOBRE NUEVO ESPACIO
        try:
            notificar_accion_admin(
                tipo='espacio_creado',
                titulo='🏢 Nuevo Espacio Creado',
                mensaje=f"El administrador {request.user.username} ha creado el espacio '{espacio.nombre}' ({espacio.tipo}) con capacidad para {espacio.capacidad} personas",
                usuario_admin=request.user,
                espacio=espacio,
                request=request
            )
            print(f"📢 Notificación admin creada para nuevo espacio {espacio.id}")
        except Exception as admin_notif_error:
            print(f"⚠️ Error en notificación admin espacio: {admin_notif_error}")
        
        return JsonResponse({
            'success': True, 
            'message': 'Espacio creado exitosamente',
            'espacio_id': espacio.id
        })
        
    except json.JSONDecodeError as e:
        print(f"❌ Error JSON: {e}")
        return JsonResponse({
            'success': False, 
            'error': 'Error en el formato de datos JSON'
        }, status=400)
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False, 
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)

@login_required
@require_http_methods(["GET"])
def obtener_espacio_api(request, espacio_id):
    """API para obtener datos de un espacio específico - VERSIÓN CORREGIDA"""
    try:
        print(f"🔍 Buscando espacio ID: {espacio_id}")
        
        # Verificar permisos
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol not in ['Administrativo', 'Investigacion', 'Aprobador']:
            return JsonResponse({
                'success': False, 
                'error': 'No tienes permisos para editar espacios'
            }, status=403)
        
        espacio = Espacio.objects.get(id=espacio_id)
        print(f"✅ Espacio encontrado: {espacio.nombre}")
        
        return JsonResponse({
            'success': True,
            'espacio': {
                'id': espacio.id,
                'nombre': espacio.nombre,
                'tipo': espacio.tipo,
                'edificio': espacio.edificio or '',
                'piso': espacio.piso,
                'capacidad': espacio.capacidad,
                'descripcion': espacio.descripcion or '',
                'estado': espacio.estado
            }
        })
    except Espacio.DoesNotExist:
        print(f"❌ Espacio {espacio_id} no encontrado")
        return JsonResponse({
            'success': False, 
            'error': 'Espacio no encontrado'
        }, status=404)
    except Exception as e:
        print(f"💥 Error al obtener espacio: {str(e)}")
        return JsonResponse({
            'success': False, 
            'error': f'Error al cargar espacio: {str(e)}'
        }, status=500)
        
@login_required
@csrf_exempt
@require_http_methods(["POST"])  
def actualizar_espacio_api(request, espacio_id):
    """API para actualizar espacios"""
    print(f"🔍 Actualizando espacio ID: {espacio_id}")
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        # Verificar permisos
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol not in ['Administrativo', 'Investigacion', 'Aprobador']:
            return JsonResponse({'success': False, 'error': 'No tienes permisos de administrador'})
        
        # Obtener espacio
        espacio = Espacio.objects.get(id=espacio_id)
        
        # Parsear datos
        data = json.loads(request.body)
        print(f"📝 Datos para actualizar: {data}")
        
        # Actualizar campos
        if 'nombre' in data:
            espacio.nombre = data['nombre'].strip()
        if 'tipo' in data:
            espacio.tipo = data['tipo']
        if 'capacidad' in data:
            espacio.capacidad = int(data['capacidad'])
        if 'edificio' in data:
            espacio.edificio = data['edificio'].strip() or None
        if 'piso' in data:
            piso = data['piso']
            espacio.piso = int(piso) if piso and str(piso).strip() else None
        if 'descripcion' in data:
            espacio.descripcion = data['descripcion'].strip() or None
        if 'estado' in data:
            espacio.estado = data['estado']
        
        # Guardar cambios
        espacio.save()
        
        print(f"✅ Espacio actualizado: {espacio.id} - {espacio.nombre}")
        
        # 🔔 NOTIFICAR GENERACIÓN DE REPORTE
        try:
            notificar_accion_admin(
                tipo='reporte_generado',
                titulo='📊 Reporte PDF Generado',
                mensaje=f"El administrador {request.user.username} ha generado un reporte PDF: {tipo_reporte}",
                usuario_admin=request.user,
                request=request
            )
        except Exception as admin_notif_error:
            print(f"⚠️ Error en notificación admin reporte: {admin_notif_error}")
        
        return JsonResponse({
            'success': True, 
            'message': 'Espacio actualizado exitosamente'
        })
        
    except Espacio.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Espacio no encontrado'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Error en el formato de datos JSON'})
    except Exception as e:
        print(f"❌ Error al actualizar: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': f'Error interno del servidor: {str(e)}'})

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def eliminar_espacio_api(request, espacio_id):
    """API para eliminar un espacio"""
    try:
        # Verificar permisos de administrador
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol not in ['Administrativo', 'Investigacion', 'Aprobador']:
            return JsonResponse({'success': False, 'error': 'No tienes permisos'}, status=403)
        
        espacio = Espacio.objects.get(id=espacio_id)
        espacio_nombre = espacio.nombre
        espacio.delete()
        
        # 🔔 NOTIFICAR A ADMINISTRADORES SOBRE ELIMINACIÓN DE ESPACIO
        try:
            notificar_accion_admin(
                tipo='espacio_eliminado',
                titulo='🗑️ Espacio Eliminado',
                mensaje=f"El administrador {request.user.username} ha eliminado el espacio '{espacio_nombre}'",
                usuario_admin=request.user,
                request=request
            )
            print(f"📢 Notificación admin creada para eliminación de espacio {espacio_id}")
        except Exception as admin_notif_error:
            print(f"⚠️ Error en notificación admin eliminación espacio: {admin_notif_error}")
        
        return JsonResponse({
            'success': True, 
            'message': f'Espacio "{espacio_nombre}" eliminado exitosamente'
        })
        
    except Espacio.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Espacio no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# === VISTAS FALTANTES PARA GESTIÓN DE USUARIOS ===

@login_required
@require_http_methods(["GET"])
def obtener_usuario_api(request, user_id):
    """API para obtener datos de un usuario específico"""
    try:
        # Verificar permisos de administrador
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol not in ['Administrativo', 'Investigacion', 'Aprobador']:
            return JsonResponse({'success': False, 'error': 'No tienes permisos'}, status=403)
        
        usuario = User.objects.get(id=user_id)
        perfil_usuario = PerfilUsuario.objects.get(user=usuario)
        
        return JsonResponse({
            'success': True,
            'usuario': {
                'id': usuario.id,
                'username': usuario.username,
                'first_name': usuario.first_name,
                'last_name': usuario.last_name,
                'email': usuario.email,
                'is_active': usuario.is_active,
                'rol': perfil_usuario.rol,
                'departamento': perfil_usuario.departamento,
                'estado': perfil_usuario.estado
            }
        })
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def actualizar_usuario_api(request, user_id):
    """API para actualizar datos de usuario"""
    try:
        # Verificar permisos de administrador
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol not in ['Administrativo', 'Investigacion', 'Aprobador']:
            return JsonResponse({'success': False, 'error': 'No tienes permisos'}, status=403)
        
        data = json.loads(request.body)
        usuario = User.objects.get(id=user_id)
        
        # Actualizar datos básicos
        if 'first_name' in data:
            usuario.first_name = data['first_name']
        if 'last_name' in data:
            usuario.last_name = data['last_name']
        if 'email' in data:
            usuario.email = data['email']
        usuario.save()
        
        # Actualizar perfil
        try:
            perfil_usuario = PerfilUsuario.objects.get(user=usuario)
            if 'rol' in data:
                perfil_usuario.rol = data['rol']
            if 'departamento' in data:
                perfil_usuario.departamento = data['departamento']
            perfil_usuario.save()
        except PerfilUsuario.DoesNotExist:
            # Crear perfil si no existe
            area_default = Area.objects.get_or_create(nombre_area="General")[0]
            PerfilUsuario.objects.create(
                user=usuario,
                rol=data.get('rol', 'Usuario'),
                area=area_default,
                departamento=data.get('departamento', 'Indefinido'),
                estado='activo'
            )
        
        # 🔔 NOTIFICAR ACTUALIZACIÓN DE USUARIO
        try:
            notificar_accion_admin(
                tipo='usuario_actualizado',
                titulo='✏️ Usuario Actualizado',
                mensaje=f"El administrador {request.user.username} ha actualizado los datos del usuario {usuario.username}",
                usuario_admin=request.user,
                usuario_relacionado=usuario,
                request=request
            )
            print(f"📢 Notificación admin creada para actualización de usuario {usuario.id}")
        except Exception as admin_notif_error:
            print(f"⚠️ Error en notificación admin actualización usuario: {admin_notif_error}")
        
        return JsonResponse({'success': True, 'message': 'Usuario actualizado exitosamente'})
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def cambiar_estado_usuario_api(request, user_id):
    """API para activar/desactivar usuario"""
    try:
        # Verificar permisos de administrador
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol not in ['Administrativo', 'Investigacion', 'Aprobador']:
            return JsonResponse({'success': False, 'error': 'No tienes permisos'}, status=403)
        
        data = json.loads(request.body)
        activo = data.get('activo', True)
        
        usuario = User.objects.get(id=user_id)
        estado_anterior = usuario.is_active
        usuario.is_active = activo
        usuario.save()
        
        # Actualizar estado en el perfil también
        try:
            perfil_usuario = PerfilUsuario.objects.get(user=usuario)
            perfil_usuario.estado = 'activo' if activo else 'inactivo'
            perfil_usuario.save()
        except PerfilUsuario.DoesNotExist:
            pass
        
        # 🔔 NOTIFICAR CAMBIO DE ESTADO DE USUARIO
        try:
            accion = "activado" if activo else "desactivado"
            notificar_accion_admin(
                tipo='usuario_actualizado',
                titulo=f'👤 Usuario {accion.capitalize()}',
                mensaje=f"El administrador {request.user.username} ha {accion} al usuario {usuario.username}",
                usuario_admin=request.user,
                usuario_relacionado=usuario,
                request=request
            )
            print(f"📢 Notificación admin creada para {accion} de usuario {usuario.id}")
        except Exception as admin_notif_error:
            print(f"⚠️ Error en notificación admin estado usuario: {admin_notif_error}")
        
        accion = "activado" if activo else "desactivado"
        return JsonResponse({'success': True, 'message': f'Usuario {accion} exitosamente'})
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def obtener_perfiles_usuario_api(request):
    """API para obtener perfiles de usuario"""
    try:
        # Verificar permisos de administrador
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol not in ['Administrativo', 'Investigacion', 'Aprobador']:
            return JsonResponse({'success': False, 'error': 'No tienes permisos'}, status=403)
        
        user_id = request.GET.get('user_id')
        if user_id:
            perfiles = PerfilUsuario.objects.filter(user_id=user_id)
        else:
            perfiles = PerfilUsuario.objects.all()
        
        data = []
        for perfil in perfiles:
            data.append({
                'id': perfil.id,
                'user_id': perfil.user.id,
                'username': perfil.user.username,
                'email': perfil.user.email,
                'first_name': perfil.user.first_name,
                'last_name': perfil.user.last_name,
                'rol': perfil.rol,
                'estado': perfil.estado,
                'departamento': perfil.departamento,
                'fecha_registro': perfil.fecha_registro.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({'success': True, 'perfiles': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
@login_required
def notificaciones_admin_view(request):
    """Vista de notificaciones para administradores"""
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol not in ['Administrativo', 'Investigacion', 'Aprobador']:
            return redirect('dashboard')
        
        return render(request, 'reservas/notificaciones_admin.html')
    except PerfilUsuario.DoesNotExist:
        return redirect('login')

@login_required
def get_notificaciones_admin_api(request):
    """API para obtener notificaciones de administradores"""
    try:
        # Verificar que el usuario es administrador
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol not in ['Administrativo', 'Investigacion', 'Aprobador']:
            return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
        
        # Obtener parámetros
        no_leidas = request.GET.get('no_leidas', 'false').lower() == 'true'
        limite = int(request.GET.get('limite', 50))
        tipo_filtro = request.GET.get('tipo', '')
        
        # Consulta base
        notificaciones = NotificacionAdmin.objects.all()
        
        # Aplicar filtros
        if no_leidas:
            notificaciones = notificaciones.filter(leida=False)
        
        if tipo_filtro:
            notificaciones = notificaciones.filter(tipo=tipo_filtro)
        
        # Ordenar y limitar
        notificaciones = notificaciones.select_related(
            'usuario_relacionado', 'reserva', 'reserva__espacio', 'espacio'
        ).order_by('-fecha_creacion')[:limite]
        
        # Formatear respuesta
        data = []
        for notif in notificaciones:
            notif_data = {
                'id': notif.id,
                'tipo': notif.tipo,
                'titulo': notif.titulo,
                'mensaje': notif.mensaje,
                'prioridad': notif.prioridad,
                'leida': notif.leida,
                'fecha_creacion': notif.fecha_creacion.strftime('%d/%m/%Y %H:%M:%S'),
                'fecha_creacion_timestamp': notif.fecha_creacion.timestamp(),
                'usuario_relacionado': None,
                'reserva_info': None,
                'espacio_info': None
            }
            
            # Información del usuario relacionado
            if notif.usuario_relacionado:
                notif_data['usuario_relacionado'] = {
                    'username': notif.usuario_relacionado.username,
                    'nombre_completo': f"{notif.usuario_relacionado.first_name} {notif.usuario_relacionado.last_name}"
                }
            
            # Información de la reserva
            if notif.reserva:
                notif_data['reserva_info'] = {
                    'id': notif.reserva.id,
                    'espacio_nombre': notif.reserva.espacio.nombre,
                    'fecha': notif.reserva.fecha_reserva.strftime('%d/%m/%Y'),
                    'estado': notif.reserva.estado
                }
            
            # Información del espacio
            if notif.espacio:
                notif_data['espacio_info'] = {
                    'id': notif.espacio.id,
                    'nombre': notif.espacio.nombre,
                    'tipo': notif.espacio.tipo
                }
            
            data.append(notif_data)
        
        # Contar no leídas
        total_no_leidas = NotificacionAdmin.objects.filter(leida=False).count()
        
        return JsonResponse({
            'success': True,
            'notificaciones': data,
            'total_no_leidas': total_no_leidas,
            'total': len(data)
        })
        
    except Exception as e:
        print(f"❌ Error en get_notificaciones_admin_api: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error al obtener notificaciones'
        })

# === VISTAS PARA NOTIFICACIONES DE ADMINISTRADOR ===

@login_required
@require_http_methods(["GET"])
def contar_notificaciones_admin_no_leidas(request):
    """API para contar notificaciones de admin no leídas"""
    try:
        # Verificar que el usuario es administrador
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol not in ['Administrativo', 'Investigacion', 'Aprobador']:
            return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
        
        count = NotificacionAdmin.objects.filter(leida=False).count()
        
        return JsonResponse({
            'success': True,
            'count': count
        })
        
    except Exception as e:
        print(f"❌ Error en contar_notificaciones_admin_no_leidas: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error al contar notificaciones'
        }, status=500)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def marcar_todas_notificaciones_admin_leidas(request):
    """API para marcar todas las notificaciones de admin como leídas"""
    try:
        # Verificar que el usuario es administrador
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol not in ['Administrativo', 'Investigacion', 'Aprobador']:
            return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
        
        notificaciones = NotificacionAdmin.objects.filter(leida=False)
        count = notificaciones.count()
        notificaciones.update(leida=True, fecha_lectura=timezone.now())
        
        print(f"📭 Marcadas {count} notificaciones admin como leídas")
        
        return JsonResponse({
            'success': True,
            'message': f'{count} notificaciones marcadas como leídas',
            'count': count
        })
        
    except Exception as e:
        print(f"❌ Error en marcar_todas_notificaciones_admin_leidas: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error al marcar notificaciones como leídas'
        }, status=500)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def marcar_notificacion_admin_leida(request, notificacion_id):
    """API para marcar una notificación de admin como leída"""
    try:
        # Verificar que el usuario es administrador
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol not in ['Administrativo', 'Investigacion', 'Aprobador']:
            return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
        
        notificacion = NotificacionAdmin.objects.get(id=notificacion_id)
        notificacion.marcar_como_leida()
        
        return JsonResponse({
            'success': True,
            'message': 'Notificación marcada como leída'
        })
        
    except NotificacionAdmin.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Notificación no encontrada'
        }, status=404)
    except Exception as e:
        print(f"❌ Error en marcar_notificacion_admin_leida: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error al marcar notificación como leída'
        }, status=500)

@login_required
def notificaciones_admin_view(request):
    """Vista de notificaciones para administradores"""
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol not in ['Administrativo', 'Investigacion', 'Aprobador']:
            return redirect('dashboard')
        
        return render(request, 'reservas/notificaciones_admin.html')
    except PerfilUsuario.DoesNotExist:
        return redirect('login')

@login_required
def get_notificaciones_admin_api(request):
    """API para obtener notificaciones de administradores"""
    try:
        # Verificar que el usuario es administrador
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol not in ['Administrativo', 'Investigacion', 'Aprobador']:
            return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
        
        # Obtener parámetros
        no_leidas = request.GET.get('no_leidas', 'false').lower() == 'true'
        limite = int(request.GET.get('limite', 50))
        tipo_filtro = request.GET.get('tipo', '')
        
        # Consulta base
        notificaciones = NotificacionAdmin.objects.all()
        
        # Aplicar filtros
        if no_leidas:
            notificaciones = notificaciones.filter(leida=False)
        
        if tipo_filtro:
            notificaciones = notificaciones.filter(tipo=tipo_filtro)
        
        # Ordenar y limitar
        notificaciones = notificaciones.select_related(
            'usuario_relacionado', 'reserva', 'reserva__espacio', 'espacio'
        ).order_by('-fecha_creacion')[:limite]
        
        # Formatear respuesta
        data = []
        for notif in notificaciones:
            notif_data = {
                'id': notif.id,
                'tipo': notif.tipo,
                'titulo': notif.titulo,
                'mensaje': notif.mensaje,
                'prioridad': notif.prioridad,
                'leida': notif.leida,
                'fecha_creacion': notif.fecha_creacion.strftime('%d/%m/%Y %H:%M:%S'),
                'fecha_creacion_timestamp': notif.fecha_creacion.timestamp(),
                'usuario_relacionado': None,
                'reserva_info': None,
                'espacio_info': None
            }
            
            # Información del usuario relacionado
            if notif.usuario_relacionado:
                notif_data['usuario_relacionado'] = {
                    'username': notif.usuario_relacionado.username,
                    'nombre_completo': f"{notif.usuario_relacionado.first_name} {notif.usuario_relacionado.last_name}"
                }
            
            # Información de la reserva
            if notif.reserva:
                notif_data['reserva_info'] = {
                    'id': notif.reserva.id,
                    'espacio_nombre': notif.reserva.espacio.nombre,
                    'fecha': notif.reserva.fecha_reserva.strftime('%d/%m/%Y'),
                    'estado': notif.reserva.estado
                }
            
            # Información del espacio
            if notif.espacio:
                notif_data['espacio_info'] = {
                    'id': notif.espacio.id,
                    'nombre': notif.espacio.nombre,
                    'tipo': notif.espacio.tipo
                }
            
            data.append(notif_data)
        
        # Contar no leídas
        total_no_leidas = NotificacionAdmin.objects.filter(leida=False).count()
        
        return JsonResponse({
            'success': True,
            'notificaciones': data,
            'total_no_leidas': total_no_leidas,
            'total': len(data)
        })
        
    except Exception as e:
        print(f"❌ Error en get_notificaciones_admin_api: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error al obtener notificaciones'
        })

# ViewSets para tu API
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

class PerfilUsuarioViewSet(viewsets.ModelViewSet):
    queryset = PerfilUsuario.objects.all()
    serializer_class = PerfilUsuarioSerializer
    permission_classes = [permissions.IsAuthenticated]

class EspacioViewSet(viewsets.ModelViewSet):
    queryset = Espacio.objects.all()
    serializer_class = EspacioSerializer
    permission_classes = [permissions.IsAuthenticated]

class ReservaViewSet(viewsets.ModelViewSet):
    queryset = Reserva.objects.all()
    serializer_class = ReservaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filtrar reservas por usuario (solo sus propias reservas)
        user = self.request.user
        if user.is_authenticated:
            return Reserva.objects.filter(solicitante=user)
        return Reserva.objects.none()

class NotificacionViewSet(viewsets.ModelViewSet):
    queryset = Notificacion.objects.all()
    serializer_class = NotificacionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filtrar notificaciones por usuario
        user = self.request.user
        if user.is_authenticated:
            return Notificacion.objects.filter(destinatario=user)
        return Notificacion.objects.none()

class HistorialAprobacionViewSet(viewsets.ModelViewSet):
    queryset = HistorialAprobacion.objects.all()
    serializer_class = HistorialAprobacionSerializer
    permission_classes = [permissions.IsAuthenticated]

class EquipamientoViewSet(viewsets.ModelViewSet):
    queryset = Equipamiento.objects.all()
    serializer_class = EquipamientoSerializer
    permission_classes = [permissions.IsAuthenticated]

class AreaViewSet(viewsets.ModelViewSet):
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    permission_classes = [permissions.IsAuthenticated]
    
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
from datetime import datetime
from django.db import models

@login_required
def generar_reporte_pdf(request, tipo_reporte):
    """Genera reportes en PDF basados en datos reales de la BD"""
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol not in ['Administrativo', 'Investigacion', 'Aprobador']:
            return JsonResponse({'success': False, 'error': 'No autorizado'})
        
        # Crear el objeto PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=30)
        elements = []
        styles = getSampleStyleSheet()
        
        # Estilo para el título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1,  # Centrado
            textColor=colors.HexColor('#2c5530')
        )
        
        # Estilo para subtítulos
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=12,
            textColor=colors.HexColor('#4a5568')
        )
        
        # Obtener fecha actual
        fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        if tipo_reporte == 'uso_espacios':
            # Reporte de Uso de Espacios
            title = Paragraph("REPORTE DE USO DE ESPACIOS", title_style)
            elements.append(title)
            
            # Información del reporte
            info_text = f"Generado el: {fecha_actual}<br/>Generado por: {request.user.get_full_name() or request.user.username}"
            elements.append(Paragraph(info_text, styles['Normal']))
            elements.append(Spacer(1, 20))
            
            # Estadísticas generales
            elements.append(Paragraph("ESTADÍSTICAS GENERALES", subtitle_style))
            
            total_espacios = Espacio.objects.count()
            total_reservas = Reserva.objects.count()
            espacios_disponibles = Espacio.objects.filter(estado='Disponible').count()
            
            stats_data = [
                ['Total de Espacios', str(total_espacios)],
                ['Espacios Disponibles', str(espacios_disponibles)],
                ['Total de Reservas', str(total_reservas)],
            ]
            
            stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0'))
            ]))
            elements.append(stats_table)
            elements.append(Spacer(1, 20))
            
            # Espacios más utilizados
            elements.append(Paragraph("ESPACIOS MÁS UTILIZADOS", subtitle_style))
            
            espacios_mas_usados = Espacio.objects.annotate(
                num_reservas=models.Count('reserva')
            ).order_by('-num_reservas')[:10]
            
            if espacios_mas_usados:
                espacios_data = [['Espacio', 'Tipo', 'Capacidad', 'N° Reservas']]
                for espacio in espacios_mas_usados:
                    espacios_data.append([
                        espacio.nombre,
                        espacio.tipo,
                        str(espacio.capacidad),
                        str(espacio.num_reservas)
                    ])
                
                espacios_table = Table(espacios_data, colWidths=[2*inch, 1.5*inch, 1*inch, 1*inch])
                espacios_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5530')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0fff4')),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#9ae6b4'))
                ]))
                elements.append(espacios_table)
            else:
                elements.append(Paragraph("No hay datos de uso de espacios disponibles.", styles['Normal']))
                
        elif tipo_reporte == 'usuarios':
            # Reporte de Usuarios
            title = Paragraph("REPORTE DE USUARIOS", title_style)
            elements.append(title)
            
            info_text = f"Generado el: {fecha_actual}<br/>Generado por: {request.user.get_full_name() or request.user.username}"
            elements.append(Paragraph(info_text, styles['Normal']))
            elements.append(Spacer(1, 20))
            
            # Estadísticas de usuarios
            elements.append(Paragraph("ESTADÍSTICAS DE USUARIOS", subtitle_style))
            
            total_usuarios = User.objects.count()
            usuarios_activos = User.objects.filter(is_active=True).count()
            usuarios_inactivos = User.objects.filter(is_active=False).count()
            
            stats_data = [
                ['Total de Usuarios', str(total_usuarios)],
                ['Usuarios Activos', str(usuarios_activos)],
                ['Usuarios Inactivos', str(usuarios_inactivos)],
            ]
            
            stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0'))
            ]))
            elements.append(stats_table)
            elements.append(Spacer(1, 20))
            
            # Usuarios más activos
            elements.append(Paragraph("USUARIOS MÁS ACTIVOS", subtitle_style))
            
            usuarios_activos_top = User.objects.annotate(
                num_reservas=models.Count('reservas_solicitadas')
            ).filter(num_reservas__gt=0).order_by('-num_reservas')[:10]
            
            if usuarios_activos_top:
                usuarios_data = [['Usuario', 'Nombre', 'Email', 'N° Reservas']]
                for usuario in usuarios_activos_top:
                    usuarios_data.append([
                        usuario.username,
                        f"{usuario.first_name} {usuario.last_name}".strip() or 'No especificado',
                        usuario.email,
                        str(usuario.num_reservas)
                    ])
                
                usuarios_table = Table(usuarios_data, colWidths=[1.5*inch, 2*inch, 2*inch, 1*inch])
                usuarios_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2b6cb0')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ebf8ff')),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#90cdf4'))
                ]))
                elements.append(usuarios_table)
            else:
                elements.append(Paragraph("No hay datos de usuarios disponibles.", styles['Normal']))
                
        elif tipo_reporte == 'mensual':
            # Reporte Mensual
            title = Paragraph("REPORTE MENSUAL", title_style)
            elements.append(title)
            
            info_text = f"Generado el: {fecha_actual}<br/>Generado por: {request.user.get_full_name() or request.user.username}"
            elements.append(Paragraph(info_text, styles['Normal']))
            elements.append(Spacer(1, 20))
            
            # Estadísticas del mes actual
            elements.append(Paragraph("ESTADÍSTICAS DEL MES ACTUAL", subtitle_style))
            
            mes_actual = timezone.now().month
            año_actual = timezone.now().year
            
            reservas_mes = Reserva.objects.filter(
                fecha_solicitud__month=mes_actual,
                fecha_solicitud__year=año_actual
            )
            
            reservas_mes_count = reservas_mes.count()
            reservas_aprobadas_mes = reservas_mes.filter(estado='Aprobada').count()
            reservas_pendientes_mes = reservas_mes.filter(estado='Pendiente').count()
            
            stats_data = [
                ['Total de Reservas', str(reservas_mes_count)],
                ['Reservas Aprobadas', str(reservas_aprobadas_mes)],
                ['Reservas Pendientes', str(reservas_pendientes_mes)],
                ['Tasa de Aprobación', f"{round((reservas_aprobadas_mes / reservas_mes_count * 100) if reservas_mes_count > 0 else 0)}%"],
            ]
            
            stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0'))
            ]))
            elements.append(stats_table)
            elements.append(Spacer(1, 20))
            
            # Distribución por estado
            elements.append(Paragraph("DISTRIBUCIÓN DE RESERVAS POR ESTADO", subtitle_style))
            
            estados_data = [['Estado', 'Cantidad', 'Porcentaje']]
            total_reservas = reservas_mes_count
            
            for estado in ['Aprobada', 'Pendiente', 'Rechazada', 'Cancelada']:
                count = reservas_mes.filter(estado=estado).count()
                porcentaje = round((count / total_reservas * 100) if total_reservas > 0 else 0)
                estados_data.append([estado, str(count), f"{porcentaje}%"])
            
            estados_table = Table(estados_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
            estados_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#744210')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fefcbf')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d69e2e'))
            ]))
            elements.append(estados_table)
            
        else:
            return JsonResponse({'success': False, 'error': 'Tipo de reporte no válido'})
        
        # Construir el PDF
        doc.build(elements)
        
        # Preparar la respuesta
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        
        # Nombre del archivo según el tipo de reporte
        nombres_archivos = {
            'uso_espacios': 'reporte_uso_espacios',
            'usuarios': 'reporte_usuarios', 
            'mensual': 'reporte_mensual'
        }
        
        filename = f"{nombres_archivos.get(tipo_reporte, 'reporte')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        print(f"❌ Error generando PDF: {e}")
        return JsonResponse({'success': False, 'error': 'Error al generar el reporte PDF'})
    
@login_required
@user_passes_test(is_admin_user)
def test_notificaciones_admin(request):
    """Endpoint de prueba para notificaciones admin"""
    try:
        print("🧪 INICIANDO PRUEBA DE NOTIFICACIONES ADMIN")
        
        # Probar diferentes tipos de notificaciones
        test_cases = [
            {
                'tipo': 'usuario_registrado',
                'titulo': '👤 Usuario de Prueba Registrado',
                'mensaje': 'Este es un usuario de prueba creado para verificar el sistema de notificaciones',
                'usuario_relacionado': request.user
            },
            {
                'tipo': 'espacio_creado',
                'titulo': '🏢 Espacio de Prueba Creado',
                'mensaje': 'Se ha creado un espacio de prueba en el sistema',
                'usuario_admin': request.user
            },
            {
                'tipo': 'reserva_creada', 
                'titulo': '📋 Reserva de Prueba Creada',
                'mensaje': 'Un usuario ha creado una reserva de prueba',
                'usuario_relacionado': request.user
            },
            {
                'tipo': 'sesion_iniciada',
                'titulo': '🔐 Sesión Admin de Prueba',
                'mensaje': 'Se ha detectado una sesión administrativa de prueba',
                'usuario_admin': request.user
            }
        ]
        
        resultados = []
        for test_case in test_cases:
            notif = notificar_accion_admin(
                tipo=test_case['tipo'],
                titulo=test_case['titulo'],
                mensaje=test_case['mensaje'],
                usuario_admin=test_case.get('usuario_admin'),
                usuario_relacionado=test_case.get('usuario_relacionado'),
                request=request
            )
            resultados.append({
                'tipo': test_case['tipo'],
                'creada': notif is not None,
                'id': notif.id if notif else None
            })
        
        # Contar notificaciones totales
        total_notificaciones = NotificacionAdmin.objects.count()
        no_leidas = NotificacionAdmin.objects.filter(leida=False).count()
        
        return JsonResponse({
            'success': True,
            'message': f'Prueba completada. Total notificaciones: {total_notificaciones}, No leídas: {no_leidas}',
            'resultados': resultados,
            'estadisticas': {
                'total': total_notificaciones,
                'no_leidas': no_leidas
            }
        })
        
    except Exception as e:
        print(f"❌ ERROR EN PRUEBA: {e}")
        return JsonResponse({'success': False, 'error': str(e)})
    
    