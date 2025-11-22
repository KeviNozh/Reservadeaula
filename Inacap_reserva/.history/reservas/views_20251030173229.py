# reservas/views.py

# --- Imports necesarios ---
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
from django.db.models import Q # Importa Q para búsquedas complejas
import traceback # Para imprimir errores detallados
from .services import NotificacionService

# --- Vista de Login Modificada ---
@csrf_exempt
def login_view(request):
    if request.method == 'GET':
        # Si ya está logueado, redirigir al dashboard
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, 'reservas/login.html')

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip()
            password = data.get('password')
            user_type = data.get('user_type', 'usuario')

            print(f"🔐 Intento de login: {email} - Tipo: {user_type}")

            if not email or not password:
                return JsonResponse({
                    'success': False,
                    'message': 'Correo electrónico y contraseña son requeridos.'
                }, status=400)

            # Autenticación simple
            user = authenticate(request, username=email, password=password)
            print(f"🔍 Resultado autenticación: {user}")

            if user is not None:
                if user.is_active:
                    try:
                        perfil = PerfilUsuario.objects.get(user=user)
                        print(f"👤 Perfil encontrado: {perfil.rol}")
                        
                        # Verificar rol para login de administrador
                        is_admin_login = user_type == 'administrador'
                        is_admin_role = perfil.rol in ['Admin', 'Aprobador']
                        
                        print(f"🔑 Login admin: {is_admin_login}, Rol admin: {is_admin_role}")

                        if is_admin_login and not is_admin_role:
                            return JsonResponse({
                                'success': False,
                                'message': f'No tienes permisos de administrador. Tu rol es: {perfil.rol}'
                            }, status=403)

                        # Login exitoso
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
                        print(f"❌ No tiene perfil: {email}")
                        return JsonResponse({
                            'success': False,
                            'message': 'Error: Perfil de usuario no configurado.'
                        }, status=500)
                else:
                    return JsonResponse({
                        'success': False,
                        'message': 'Cuenta desactivada.'
                    }, status=403)
            else:
                print(f"❌ Credenciales incorrectas para: {email}")
                return JsonResponse({
                    'success': False, 
                    'message': 'Credenciales incorrectas'
                }, status=401)

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False, 
                'message': 'Error en los datos enviados'
            }, status=400)
        except Exception as e:
            print(f"💥 Error en login: {str(e)}")
            return JsonResponse({
                'success': False, 
                'message': 'Error interno del servidor'
            }, status=500)

    return JsonResponse({
        'success': False, 
        'message': 'Método no permitido'
    }, status=405)
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
        
        # Redirigir según el rol
        if perfil.rol in ['Admin', 'Aprobador']:
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
    Vista para registrar nuevos usuarios desde el formulario de registro
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip().lower()
            password = data.get('password')
            first_name = data.get('first_name', '').strip()
            last_name = data.get('last_name', '').strip()
            department = data.get('department', 'Indefinido')

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
                rol='Usuario',  # Todos los registrados son usuarios normales
                area=area,
                departamento=department,
                estado='activo'
            )

            print(f"✅ Nuevo usuario registrado: {email} - {first_name} {last_name}")

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

        if perfil.rol == 'Usuario':
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
        elif perfil.rol in ['Admin', 'Aprobador']:
            stats['reservas_pendientes_aprobacion'] = Reserva.objects.filter(
                estado='Pendiente'
            ).count()
            stats['total_espacios'] = Espacio.objects.count()
            stats['espacios_disponibles'] = Espacio.objects.filter(estado='Disponible').count()

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
def reserva_exitosa_view(request):
    return render(request, 'reservas/reserva_exitosa.html')

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
                    'telefono': 'N/A'  # Podrías agregar este campo al modelo de usuario
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
    diferencia = datetime.combine(date.today(), hora_fin) - datetime.combine(date.today(), hora_inicio)
    horas = diferencia.seconds // 3600
    minutos = (diferencia.seconds % 3600) // 60
    
    if horas > 0:
        return f"{horas} hora{'s' if horas > 1 else ''} {minutos} minuto{'s' if minutos > 1 else ''}"
    else:
        return f"{minutos} minutos"

@login_required
def cancelar_reserva_view(request):
    # Considera pasar un ID aquí
    return render(request, 'reservas/cancelar_reserva.html')

# --- Vistas de Administración ---
# Añade @login_required y verificación de rol/permisos aquí

@login_required
def admin_dashboard_view(request):
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol not in ['Admin', 'Aprobador']:
            return redirect('dashboard') # O página de error
    except PerfilUsuario.DoesNotExist:
        return redirect('login')
    return render(request, 'reservas/dashboard_admin.html')

@login_required
def solicitudes_pendientes_view(request):
    # Añadir verificación de rol
    return render(request, 'reservas/solicitudes_pendientes.html')

@login_required
def gestion_espacios_view(request):
    # Añadir verificación de rol
    return render(request, 'reservas/gestion_espacios.html')

@login_required
def gestion_usuarios_view(request):
    # Añadir verificación de rol
    return render(request, 'reservas/gestion_usuarios.html')

@login_required
def reportes_view(request):
    # Añadir verificación de rol
    return render(request, 'reservas/reportes.html')

@login_required
def revisar_solicitud_view(request):
    # Considera pasar un ID aquí
    # Añadir verificación de rol
    return render(request, 'reservas/revisar_solicitud.html')

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

# reservas/views.py - AGREGAR ESTA VISTA

@login_required
@csrf_exempt
def crear_reserva_api(request):
    """API para crear reservas REALES en la base de datos"""
    if request.method == 'POST':
        try:
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
            
            try:
                reserva_verificada = Reserva.objects.get(id=reserva.id)
                print(f"🔍 Reserva verificada en BD: {reserva_verificada}")
                print(f"📊 Datos de la reserva:")
                print(f"   - Espacio: {reserva_verificada.espacio.nombre}")
                print(f"   - Fecha: {reserva_verificada.fecha_reserva}")
                print(f"   - Hora inicio: {reserva_verificada.hora_inicio}")
                print(f"   - Hora fin: {reserva_verificada.hora_fin}")
                print(f"   - Asistentes: {reserva_verificada.num_asistentes}")
                print(f"   - Propósito: {reserva_verificada.proposito}")
            except Reserva.DoesNotExist:
                print(f"❌ ERROR: La reserva no se guardó en la base de datos")

            # Crear notificación - ESTA LÍNEA DEBE ESTAR BIEN INDENTADA
            Notificacion.objects.create(
                destinatario=request.user,
                tipo='reserva',
                titulo='Solicitud de Reserva Enviada',
                mensaje=f'Tu solicitud para {espacio.nombre} ha sido enviada y está pendiente de aprobación.',
                leida=False
            )

            return JsonResponse({
                'success': True,
                'message': 'Reserva creada exitosamente',
                'reserva_id': reserva.id,
                'redirect_url': f'/reserva-exitosa/?reserva_id={reserva.id}'  # ← Asegúrate de incluir el ID
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
    
    # --- VISTAS PARA SERVIR TEMPLATES HTML ---
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
def crear_reserva_view(request):
    
    """API para crear reservas REALES en la base de datos"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print(f"📝 Datos recibidos para crear reserva: {data}")
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
def reserva_exitosa_view(request):
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
        print(f"💥 Error en reserva_exitosa_view: {e}")
        import traceback
        traceback.print_exc()
        context = {
            'user': request.user,
            'reserva': None
        }
        return render(request, 'reservas/reserva_exitosa.html', context)

@login_required
def reserva_exitosa_view(request):
    """Vista de confirmación de reserva exitosa"""
    return render(request, 'reservas/reserva_exitosa.html')

@login_required
def detalle_reserva_view(request):
    """Vista de detalle de reserva"""
    reserva_id = request.GET.get('id')
    try:
        reserva = Reserva.objects.get(id=reserva_id, solicitante=request.user)
        context = {
            'user': request.user,
            'reserva': reserva
        }
        return render(request, 'reservas/detalle_reserva.html', context)
    except Reserva.DoesNotExist:
        return redirect('reservas')
    except Exception as e:
        print(f"Error en detalle_reserva_view: {e}")
        return redirect('reservas')

@login_required
def cancelar_reserva_view(request):
    """Vista para cancelar reserva"""
    reserva_id = request.GET.get('id')
    try:
        reserva = Reserva.objects.get(id=reserva_id, solicitante=request.user)
        context = {
            'user': request.user,
            'reserva': reserva
        }
        return render(request, 'reservas/cancelar_reserva.html', context)
    except Reserva.DoesNotExist:
        return redirect('reservas')
    except Exception as e:
        print(f"Error en cancelar_reserva_view: {e}")
        return redirect('reservas')

# --- Vistas de Administración ---
@login_required
def admin_dashboard_view(request):
    """Dashboard para administradores"""
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol not in ['Admin', 'Aprobador']:
            return redirect('dashboard')
        
        # Estadísticas para admin
        total_reservas = Reserva.objects.count()
        reservas_pendientes = Reserva.objects.filter(estado='Pendiente').count()
        total_espacios = Espacio.objects.count()
        usuarios_activos = User.objects.filter(is_active=True).count()
        
        context = {
            'user': request.user,
            'perfil': perfil,
            'total_reservas': total_reservas,
            'reservas_pendientes': reservas_pendientes,
            'total_espacios': total_espacios,
            'usuarios_activos': usuarios_activos
        }
        return render(request, 'reservas/dashboard_admin.html', context)
    except PerfilUsuario.DoesNotExist:
        return redirect('login')

@login_required
def solicitudes_pendientes_view(request):
    """Vista de solicitudes pendientes para administradores"""
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol not in ['Admin', 'Aprobador']:
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
    """Vista de gestión de espacios para administradores"""
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol not in ['Admin', 'Aprobador']:
            return redirect('dashboard')
        
        espacios = Espacio.objects.all()
        
        context = {
            'user': request.user,
            'espacios': espacios
        }
        return render(request, 'reservas/gestion_espacios.html', context)
    except PerfilUsuario.DoesNotExist:
        return redirect('login')

@login_required
def gestion_usuarios_view(request):
    """Vista de gestión de usuarios para administradores"""
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol not in ['Admin', 'Aprobador']:
            return redirect('dashboard')
        
        usuarios = User.objects.filter(is_active=True).prefetch_related('perfilusuario')
        
        context = {
            'user': request.user,
            'usuarios': usuarios
        }
        return render(request, 'reservas/gestion_usuarios.html', context)
    except PerfilUsuario.DoesNotExist:
        return redirect('login')

@login_required
def reportes_view(request):
    """Vista de reportes para administradores"""
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol not in ['Admin', 'Aprobador']:
            return redirect('dashboard')
        
        context = {
            'user': request.user
        }
        return render(request, 'reservas/reportes.html', context)
    except PerfilUsuario.DoesNotExist:
        return redirect('login')

@login_required
def revisar_solicitud_view(request):
    """Vista para revisar una solicitud específica"""
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol not in ['Admin', 'Aprobador']:
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
def force_logout(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('login')

@login_required
@require_http_methods(["GET"])
def get_notificaciones_usuario(request):
    """
    API para obtener las notificaciones del usuario
    """
    try:
        # Obtener parámetros de la solicitud
        no_leidas = request.GET.get('no_leidas', 'false').lower() == 'true'
        limite = int(request.GET.get('limite', 10))
        
        # Obtener notificaciones
        notificaciones = NotificacionService.obtener_notificaciones_usuario(
            usuario=request.user,
            no_leidas=no_leidas,
            limite=limite
        )
        
        # Formatear respuesta
        data = []
        for notif in notificaciones:
            data.append({
                'id': notif.id,
                'tipo': notif.tipo,
                'titulo': notif.titulo,
                'mensaje': notif.mensaje,
                'leida': notif.leida,
                'fecha_creacion': notif.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
                'reserva_id': notif.reserva.id if notif.reserva else None,
                'espacio_nombre': notif.reserva.espacio.nombre if notif.reserva else None
            })
        
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
            'error': 'Error al obtener notificaciones'
        }, status=500)

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
        
        # Marcar como leída
        notificacion.marcar_como_leida()
        
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