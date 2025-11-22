# reservas/views.py

# --- Imports necesarios ---
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
from .models import PerfilUsuario, Reserva, Espacio, Notificacion, Incidencia, Area
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models import Q # Importa Q para búsquedas complejas
import traceback # Para imprimir errores detallados

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
            email = data.get('email', '').strip() # Obtener email y quitar espacios
            password = data.get('password')
            user_type = data.get('user_type', 'usuario') # 'usuario' o 'administrador'

            if not email or not password:
                return JsonResponse({
                    'success': False,
                    'message': 'Correo electrónico y contraseña son requeridos.'
                }, status=400)

            print(f"🔐 Intento de login: {email}, tipo: {user_type}")

            # --- Autenticación ---
            # Ahora authenticate usará EmailBackend (gracias a settings.py)
            user = authenticate(request, username=email, password=password)

            # --- Verificación Post-Autenticación ---
            if user is not None:
                # Usuario autenticado correctamente, ahora verificamos el perfil y rol
                try:
                    perfil = PerfilUsuario.objects.get(user=user)

                    is_admin_login = user_type == 'administrador'
                    is_admin_role = perfil.rol in ['Admin', 'Aprobador']

                    if is_admin_login and not is_admin_role:
                        print(f"❌ Rol incorrecto para login admin: Usuario {email} tiene rol {perfil.rol}")
                        return JsonResponse({
                            'success': False,
                            'message': f'No tienes permisos para acceder como Administrador. Tu rol es: {perfil.rol}'
                        }, status=403) # 403 Forbidden

                    if not is_admin_login and is_admin_role:
                        print(f"ℹ️ Admin {email} iniciando sesión como usuario normal.")
                        pass # Permitir login

                    if perfil.estado != 'activo':
                         print(f"❌ Perfil inactivo o suspendido para: {email}")
                         return JsonResponse({
                             'success': False,
                             'message': f'Tu cuenta está {perfil.estado}. Contacta al administrador.'
                         }, status=403)

                    login(request, user)
                    perfil.ultimo_acceso = timezone.now()
                    perfil.save()

                    print(f"✅ Login exitoso: {user.username} ({perfil.rol})")
                    return JsonResponse({
                        'success': True,
                        'message': 'Login exitoso',
                        'user': {
                            'id': user.id,
                            'nombre_completo': user.get_full_name() or f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username,
                            'username': user.username,
                            'email': user.email,
                            'rol': perfil.rol,
                            'departamento': perfil.departamento,
                            'area': perfil.area.nombre_area if perfil.area else None
                        }
                    })

                except PerfilUsuario.DoesNotExist:
                    print(f"❌ Error crítico: Usuario {email} autenticado pero sin perfil.")
                    logout(request)
                    return JsonResponse({
                        'success': False,
                        'message': 'Error: Perfil de usuario no encontrado. Contacta al soporte.'
                    }, status=500)

            else:
                # --- Falló la autenticación ---
                if user_type == 'usuario' and not email.lower().endswith('@inacapmail.com'):
                    user_exists = User.objects.filter(Q(email__iexact=email) | Q(username__iexact=email)).exists()
                    if not user_exists:
                        print(f"👤 Usuario no existe ({email}), intentando registro automático...")
                        nuevo_usuario = registrar_usuario_automatico(email, password)
                        if nuevo_usuario:
                            user_recien_creado = authenticate(request, username=email, password=password)
                            if user_recien_creado:
                                login(request, user_recien_creado)
                                try:
                                     perfil_nuevo = PerfilUsuario.objects.get(user=user_recien_creado)
                                     perfil_nuevo.ultimo_acceso = timezone.now()
                                     perfil_nuevo.save()
                                     print(f"✅ Registro y login automático exitoso para: {email}")
                                     return JsonResponse({
                                         'success': True,
                                         'message': 'Registro y login exitoso',
                                         'user': {
                                              'id': user_recien_creado.id,
                                              'nombre_completo': user_recien_creado.get_full_name() or user_recien_creado.username,
                                              'username': user_recien_creado.username,
                                              'email': user_recien_creado.email,
                                              'rol': perfil_nuevo.rol,
                                              'departamento': perfil_nuevo.departamento,
                                              'area': perfil_nuevo.area.nombre_area if perfil_nuevo.area else None
                                         }
                                     })
                                except PerfilUsuario.DoesNotExist:
                                     print(f"❌ Error crítico post-registro: No se encontró perfil para {email}")
                                     logout(request)
                                     return JsonResponse({'success': False, 'message': 'Error al crear el perfil.'}, status=500)
                            else:
                                print(f"❌ Error post-registro: Falló la autenticación para {email}")
                                return JsonResponse({'success': False, 'message': 'Error al iniciar sesión después del registro.'}, status=500)
                        else:
                             return JsonResponse({'success': False, 'message': 'No se pudo registrar el usuario automáticamente.'}, status=500)
                    else:
                         print(f"❌ Credenciales incorrectas para usuario existente: {email}")
                         return JsonResponse({'success': False, 'message': 'Credenciales incorrectas'}, status=401)
                else:
                    print(f"❌ Credenciales incorrectas para: {email}")
                    return JsonResponse({'success': False, 'message': 'Credenciales incorrectas'}, status=401)

        except json.JSONDecodeError:
            print("❌ Error: JSON mal formado recibido.")
            return JsonResponse({'success': False, 'message': 'Error en los datos enviados'}, status=400)
        except Exception as e:
            print(f"❌ Error inesperado en login_view: {e}")
            traceback.print_exc()
            return JsonResponse({'success': False, 'message': f'Error interno del servidor.'}, status=500)

    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)

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
    # Forzar logout si hay error
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol in ['Admin', 'Aprobador']:
            return render(request, 'reservas/dashboard_admin.html')
        else:
            return render(request, 'reservas/dashboard_usuario.html')
    except Exception as e:
        print(f"Error: {e}")
        logout(request)
        return redirect('login')

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
@login_required # Añade @login_required si estas vistas deben ser protegidas
def espacios_view(request):
    return render(request, 'reservas/espacios.html')

@login_required
def reservas_view(request):
    return render(request, 'reservas/reservas.html')

@login_required
def notificaciones_view(request):
    return render(request, 'reservas/notificaciones.html')

@login_required
def calendario_view(request):
    return render(request, 'reservas/calendario.html')

@login_required
def crear_reserva_view(request):
    return render(request, 'reservas/crear_reserva.html')

@login_required
def reserva_exitosa_view(request):
    return render(request, 'reservas/reserva_exitosa.html')

@login_required
def detalle_reserva_view(request):
    # Considera pasar un ID aquí
    return render(request, 'reservas/detalle_reserva.html')

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