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
            return JsonResponse({'success': True, 'incidencia_id': incidencia.id})
        except Exception as e:
            print(f"❌ Error en reportar_incidencia: {e}")
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

@csrf_exempt
def registro_usuario(request):
    """
    Vista para registrar nuevos usuarios desde el formulario de registro - ACTUALIZADA
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip().lower()
            password = data.get('password')
            first_name = data.get('first_name', '').strip()
            last_name = data.get('last_name', '').strip()
            department = data.get('department', 'Indefinido')
            rol = data.get('rol', 'Usuario')  # Nuevo campo para el rol

            # Validaciones básicas
            if not all([email, password, first_name, last_name]):
                return JsonResponse({
                    'success': False,
                    'message': 'Todos los campos son requeridos'
                }, status=400)

            if len(password) < 6:
                return JsonResponse({
                    'success': False,
                    'message': 'La contraseña debe tener al menos 6 caracteres'
                }, status=400)

            # Verificar si el usuario ya existe
            if User.objects.filter(Q(email__iexact=email) | Q(username__iexact=email)).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Ya existe un usuario con este correo electrónico'
                }, status=400)

            # Validar que el rol sea permitido para registro público
            roles_permitidos = ['Usuario', 'Docente', 'Investigacion', 'Administrativo']
            if rol not in roles_permitidos:
                return JsonResponse({
                    'success': False,
                    'message': 'Rol no válido para registro público'
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

            # Crear perfil de usuario CON EL ROL SELECCIONADO
            PerfilUsuario.objects.create(
                user=user,
                rol=rol,  # Usar el rol seleccionado en el formulario
                area=area,
                departamento=department,
                estado='activo'
            )

            print(f"✅ Nuevo usuario registrado: {email} - {first_name} {last_name} - Rol: {rol}")

            return JsonResponse({
                'success': True,
                'message': 'Usuario registrado exitosamente. Ahora puedes iniciar sesión.'
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Error en los datos enviados'
            }, status=400)
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
    logout(request)
    return redirect('login')

# --- VISTAS PARA SERVIR TEMPLATES HTML ---
@login_required
def notificaciones_view(request):
    return render(request, 'reservas/notificaciones.html')

@login_required
def calendario_view(request):
    """Vista del calendario con eventos REALES"""
    try:
        # Obtener reservas REALES para el calendario
        reservas_calendario = Reserva.objects.filter(
            solicitante=request.user
        ).select_related('espacio')
        
        eventos_calendario = []
        for reserva in reservas_calendario:
            eventos_calendario.append({
                'id': reserva.id,
                'title': f"{reserva.espacio.nombre} - {reserva.proposito}",
                'start': f"{reserva.fecha_reserva}T{reserva.hora_inicio}",
                'end': f"{reserva.fecha_reserva}T{reserva.hora_fin}",
                'color': '#10b981' if reserva.estado == 'Aprobada' else 
                        '#f59e0b' if reserva.estado == 'Pendiente' else 
                        '#ef4444',
                'estado': reserva.estado,
                'espacio': reserva.espacio.nombre,
                'espacio_id': reserva.espacio.id,
                'extendedProps': {
                    'estado': reserva.estado,
                    'espacio_id': reserva.espacio.id,
                    'espacio_nombre': reserva.espacio.nombre,
                    'proposito': reserva.proposito
                }
            })
        
        # Obtener espacios para el filtro
        espacios = Espacio.objects.filter(estado='Disponible')
        
        # Convertir a JSON para el template
        eventos_json = json.dumps(eventos_calendario, default=str)
        
        context = {
            'user': request.user,
            'eventos': eventos_json,
            'espacios': espacios,
            'reservas': reservas_calendario,
            'current_month': timezone.now().strftime('%Y-%m')
        }
        return render(request, 'reservas/calendario.html', context)
        
    except Exception as e:
        print(f"Error en calendario_view: {e}")
        import traceback
        traceback.print_exc()
        return render(request, 'reservas/calendario.html', {
            'eventos': '[]', 
            'espacios': [],
            'reservas': [],
            'current_month': timezone.now().strftime('%Y-%m')
        })

@login_required
def crear_reserva_view(request):
    return render(request, 'reservas/crear_reserva.html')

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
def solicitudes_pendientes_view(request):
    """Vista de solicitudes pendientes para administradores"""
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        # ACTUALIZADO: Roles que pueden acceder
        if perfil.rol not in ['Administrativo', 'Investigacion', 'Aprobador']:
            return redirect('dashboard')
        
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
        
        context = {
            'user': request.user,
            'total_reservas': total_reservas,
            'usuarios_activos': usuarios_activos,
            'total_espacios': total_espacios,
            'tasa_aprobacion': tasa_aprobacion
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
                reserva.estado = 'Cancelada'
                reserva.save()
                
                # Crear notificación
                Notificacion.objects.create(
                    destinatario=request.user,
                    tipo='reserva',
                    titulo='Reserva Cancelada',
                    mensaje=f'Tu reserva para {reserva.espacio.nombre} ha sido cancelada.',
                    leida=False
                )
                
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
            
            # NOTIFICAR AL USUARIO - VERSIÓN MEJORADA
            try:
                notificacion = NotificacionService.notificar_creacion_reserva(reserva)
                if notificacion:
                    print(f"📧 Notificación de creación enviada exitosamente: {notificacion.id}")
                else:
                    print("⚠️ No se pudo crear la notificación de creación")
            except Exception as notif_error:
                print(f"⚠️ Error en notificación: {notif_error}")
                # No fallar la reserva por error en notificación
            
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
def crear_reserva_view(request):
    """Vista para crear nueva reserva"""
    try:
        espacios = Espacio.objects.filter(estado='Disponible')
        context = {
            'user': request.user,
            'espacios': espacios
        }
        return render(request, 'reservas/crear_reserva.html', context)
    except Exception as e:
        print(f"Error en crear_reserva_view: {e}")
        return render(request, 'reservas/crear_reserva.html', {'espacios': []})

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
            
            # NOTIFICAR AL USUARIO - VERSIÓN CORREGIDA
            notificacion = NotificacionService.notificar_aprobacion_reserva(
                reserva, 
                comentario_admin
            )
            
            if notificacion:
                print(f"📧 Notificación de aprobación creada: {notificacion.id}")
            else:
                print("⚠️ No se pudo crear la notificación de aprobación")
            
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
            
            # NOTIFICAR AL USUARIO - VERSIÓN CORREGIDA
            notificacion = NotificacionService.notificar_rechazo_reserva(
                reserva, 
                motivo
            )
            
            if notificacion:
                print(f"📧 Notificación de rechazo creada: {notificacion.id}")
            else:
                print("⚠️ No se pudo crear la notificación de rechazo")
            
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
    
    # Agregar estas vistas al final del views.py

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
        usuario.first_name = data.get('first_name', usuario.first_name)
        usuario.last_name = data.get('last_name', usuario.last_name)
        usuario.email = data.get('email', usuario.email)
        usuario.save()
        
        # Actualizar perfil
        try:
            perfil_usuario = PerfilUsuario.objects.get(user=usuario)
            perfil_usuario.rol = data.get('rol', perfil_usuario.rol)
            perfil_usuario.save()
        except PerfilUsuario.DoesNotExist:
            # Crear perfil si no existe
            area_default = Area.objects.get_or_create(nombre_area="General")[0]
            PerfilUsuario.objects.create(
                user=usuario,
                rol=data.get('rol', 'Usuario'),
                area=area_default,
                departamento='Indefinido',
                estado='activo'
            )
        
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
        usuario.is_active = activo
        usuario.save()
        
        # Actualizar estado en el perfil también
        try:
            perfil_usuario = PerfilUsuario.objects.get(user=usuario)
            perfil_usuario.estado = 'activo' if activo else 'inactivo'
            perfil_usuario.save()
        except PerfilUsuario.DoesNotExist:
            pass
        
        accion = "activado" if activo else "desactivado"
        return JsonResponse({'success': True, 'message': f'Usuario {accion} exitosamente'})
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def obtener_usuario_api(request, user_id):
    """API para obtener datos de un usuario específico"""
    try:
        usuario = User.objects.get(id=user_id)
        return JsonResponse({
            'success': True,
            'id': usuario.id,
            'username': usuario.username,
            'first_name': usuario.first_name,
            'last_name': usuario.last_name,
            'email': usuario.email,
            'is_active': usuario.is_active
        })
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no encontrado'}, status=404)

@login_required
@require_http_methods(["GET"])
def obtener_perfiles_usuario_api(request):
    """API para obtener perfiles de usuario"""
    try:
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
                'rol': perfil.rol,
                'estado': perfil.estado,
                'departamento': perfil.departamento
            })
        
        return JsonResponse({'success': True, 'perfiles': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
@login_required
@require_http_methods(["GET"])
def obtener_espacio_api(request, espacio_id):
    """API para obtener datos de un espacio específico"""
    try:
        espacio = Espacio.objects.get(id=espacio_id)
        return JsonResponse({
            'success': True,
            'espacio': {
                'id': espacio.id,
                'nombre': espacio.nombre,
                'tipo': espacio.tipo,
                'edificio': espacio.edificio,
                'piso': espacio.piso,
                'capacidad': espacio.capacidad,
                'descripcion': espacio.descripcion,
                'estado': espacio.estado
            }
        })
    except Espacio.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Espacio no encontrado'}, status=404)

@login_required
@csrf_exempt
def crear_espacio_api(request):
    """API PARA CREAR ESPACIO - VERSIÓN CORREGIDA"""
    print("=" * 50)
    print("🔍 INICIANDO crear_espacio_api")
    
    try:
        # 1. Verificar método
        if request.method != 'POST':
            print("❌ Método incorrecto:", request.method)
            return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
        
        # 2. Verificar que el usuario está autenticado
        print(f"👤 Usuario: {request.user} (autenticado: {request.user.is_authenticated})")
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)
        
        # 3. Verificar permisos
        try:
            perfil = PerfilUsuario.objects.get(user=request.user)
            print(f"🎯 Rol del usuario: {perfil.rol}")
            if perfil.rol not in ['Administrativo', 'Investigacion', 'Aprobador']:
                return JsonResponse({'success': False, 'error': 'No tienes permisos de administrador'}, status=403)
        except PerfilUsuario.DoesNotExist:
            print("❌ Usuario no tiene perfil")
            return JsonResponse({'success': False, 'error': 'Perfil de usuario no encontrado'}, status=403)
        
        # 4. Leer y parsear datos
        print("📦 Body recibido:", request.body)
        try:
            data = json.loads(request.body)
            print("📝 Datos parseados:", data)
        except json.JSONDecodeError as e:
            print("❌ Error parseando JSON:", e)
            return JsonResponse({'success': False, 'error': 'Error en formato JSON'}, status=400)
        
        # 5. Validaciones básicas
        errors = []
        if not data.get('nombre'):
            errors.append('El nombre es requerido')
        if not data.get('tipo'):
            errors.append('El tipo es requerido')
        if not data.get('capacidad'):
            errors.append('La capacidad es requerida')
        
        if errors:
            print("❌ Errores de validación:", errors)
            return JsonResponse({'success': False, 'error': ', '.join(errors)})
        
        # 6. Validar capacidad
        try:
            capacidad = int(data['capacidad'])
            if capacidad <= 0:
                errors.append('La capacidad debe ser mayor a 0')
        except (ValueError, TypeError):
            errors.append('La capacidad debe ser un número válido')
        
        # 7. Validar piso (campo opcional)
        piso = None
        if data.get('piso'):
            try:
                piso = int(data['piso'])
                if piso < 0:
                    errors.append('El piso no puede ser negativo')
            except (ValueError, TypeError):
                errors.append('El piso debe ser un número válido')
        
        if errors:
            return JsonResponse({'success': False, 'error': ', '.join(errors)})
        
        # 8. Validar y preparar datos
        nombre = data['nombre'].strip()
        tipo = data['tipo']
        edificio = data.get('edificio', '').strip() or None
        descripcion = data.get('descripcion', '').strip()
        estado = data.get('estado', 'Disponible')
        
        # Validar que el estado sea válido
        estados_validos = ['Disponible', 'Mantenimiento', 'Fuera de Servicio']
        if estado not in estados_validos:
            estado = 'Disponible'  # Valor por defecto
        
        # 9. Crear el espacio
        print("🏗️ Creando espacio en la base de datos...")
        espacio = Espacio(
            nombre=nombre,
            tipo=tipo,
            edificio=edificio,
            piso=piso,  # Ahora puede ser None
            capacidad=capacidad,
            descripcion=descripcion,
            estado=estado
        )
        
        espacio.save()
        print(f"✅ ESPACIO CREADO EXITOSAMENTE: {espacio.id} - {espacio.nombre}")
        
        return JsonResponse({
            'success': True, 
            'message': 'Espacio creado exitosamente',
            'espacio_id': espacio.id
        })
        
    except Exception as e:
        print("💥 ERROR NO CONTROLADO:", str(e))
        import traceback
        print("📋 Traceback completo:")
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': f'Error interno: {str(e)}'})

print("=" * 50)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def actualizar_espacio_api(request, espacio_id):
    """API para actualizar un espacio existente"""
    try:
        # Verificar permisos de administrador
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol not in ['Administrativo', 'Investigacion', 'Aprobador']:
            return JsonResponse({'success': False, 'error': 'No tienes permisos'}, status=403)
        
        data = json.loads(request.body)
        espacio = Espacio.objects.get(id=espacio_id)
        
        # Actualizar campos
        if 'nombre' in data:
            espacio.nombre = data['nombre']
        if 'tipo' in data:
            espacio.tipo = data['tipo']
        if 'edificio' in data:
            espacio.edificio = data['edificio']
        if 'piso' in data:
            espacio.piso = data['piso']
        if 'capacidad' in data:
            espacio.capacidad = data['capacidad']
        if 'descripcion' in data:
            espacio.descripcion = data['descripcion']
        if 'estado' in data:
            espacio.estado = data['estado']
        
        espacio.save()
        
        return JsonResponse({'success': True, 'message': 'Espacio actualizado exitosamente'})
        
    except Espacio.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Espacio no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

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
        
        return JsonResponse({
            'success': True, 
            'message': f'Espacio "{espacio_nombre}" eliminado exitosamente'
        })
        
    except Espacio.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Espacio no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)