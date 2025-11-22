from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
from .models import PerfilUsuario, Reserva, Espacio, Notificacion, Incidencia

@csrf_exempt
def login_view(request):
    if request.method == 'GET':
        return render(request, 'reservas/login.html')
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')
            user_type = data.get('user_type', 'usuario')
            
            print(f"🔐 Intento de login: {email}, tipo: {user_type}")  # DEBUG
            
            # Autenticar usuario
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                # Verificar el rol del usuario
                try:
                    perfil = PerfilUsuario.objects.get(user=user)
                    
                    # Mapear tipos de usuario (sin aprobador)
                    role_map = {
                        'usuario': 'Usuario',
                        'administrador': 'Admin', 
                    }
                    
                    expected_role = role_map.get(user_type, 'Usuario')
                    
                    if perfil.rol == expected_role or (user_type == 'administrador' and perfil.rol == 'Admin'):
                        login(request, user)
                        
                        # Actualizar último acceso
                        perfil.ultimo_acceso = timezone.now()
                        perfil.save()
                        
                        print(f"✅ Login exitoso: {user.username}")
                        return JsonResponse({
                            'success': True,
                            'message': 'Login exitoso',
                            'user': {
                                'id': user.id,
                                'nombre_completo': f"{user.first_name} {user.last_name}",
                                'username': user.username,
                                'email': user.email,
                                'rol': perfil.rol,
                                'departamento': perfil.departamento,
                                'area': perfil.area.nombre_area if perfil.area else None
                            }
                        })
                    else:
                        print(f"❌ Rol incorrecto: esperaba {expected_role}, tiene {perfil.rol}")
                        return JsonResponse({
                            'success': False,
                            'message': f'No tienes permisos para acceder como {user_type}. Tu rol es: {perfil.rol}'
                        })
                except PerfilUsuario.DoesNotExist:
                    print("❌ Perfil no encontrado")
                    return JsonResponse({
                        'success': False,
                        'message': 'Perfil de usuario no encontrado'
                    })
            else:
                print("❌ Credenciales incorrectas")
                return JsonResponse({
                    'success': False,
                    'message': 'Credenciales incorrectas'
                })
                
        except json.JSONDecodeError as e:
            print(f"❌ Error JSON: {e}")
            return JsonResponse({
                'success': False,
                'message': 'Error en los datos enviados'
            })
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return JsonResponse({
                'success': False,
                'message': f'Error del servidor: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})
@login_required
def dashboard_view(request):
    # CAMBIÉ ESTA LÍNEA - Ahora busca en 'reservas/dashboard.html'
    return render(request, 'reservas/dashboard.html')

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
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def get_espacios_disponibles(request):
    try:
        # Excluir espacios en mantenimiento
        espacios = Espacio.objects.exclude(estado='Mantenimiento')
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
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

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
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def logout_view(request):
    logout(request)
    return redirect('login')

# Vistas simples para el dashboard
def espacios_view(request):
    espacios = Espacio.objects.all()
    return render(request, 'reservas/espacios.html', {'espacios': espacios})

def reservas_view(request):
    reservas = Reserva.objects.filter(solicitante=request.user)
    return render(request, 'reservas/reservas.html', {'reservas': reservas})

def notificaciones_view(request):
    notificaciones = Notificacion.objects.filter(destinatario=request.user)
    return render(request, 'reservas/notificaciones.html', {'notificaciones': notificaciones})