from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Count
from rest_framework import viewsets
from .models import Reserva, Espacio, Notificacion, HistorialAprobacion, PerfilUsuario, Area, Equipamiento
from .serializers import ReservaSerializer, EspacioSerializer, NotificacionSerializer, HistorialAprobacionSerializer, PerfilUsuarioSerializer, AreaSerializer, EquipamientoSerializer
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages

def login_usuario(request):
    """Login para usuarios normales"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user_type = request.POST.get('user_type', 'usuario')
        
        # Verificar que sea un usuario normal (no admin)
        user = authenticate(username=username, password=password)
        if user is not None:
            # Solo permitir login si es usuario normal
            if hasattr(user, 'perfilusuario') and user.perfilusuario.rol == 'Usuario':
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Esta cuenta es de administrador. Use el login de administradores.')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    
    return render(request, 'reservas/login_usuario.html')

def login_admin(request):
    """Login exclusivo para administradores"""
    if request.user.is_authenticated and (request.user.is_superuser or 
                                         (hasattr(request.user, 'perfilusuario') and 
                                          request.user.perfilusuario.rol == 'Admin')):
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(username=username, password=password)
        if user is not None:
            # Solo permitir login si es admin
            if user.is_superuser or (hasattr(user, 'perfilusuario') and user.perfilusuario.rol == 'Admin'):
                login(request, user)
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'Acceso denegado. Solo para administradores.')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    
    return render(request, 'reservas/login_admin.html')

def logout_view(request):
    """Logout para ambos tipos de usuarios"""
    logout(request)
    return redirect('login_usuario')


# Decorador para administradores
def admin_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        if hasattr(request.user, 'perfilusuario') and request.user.perfilusuario.rol == 'Admin':
            return view_func(request, *args, **kwargs)
        return redirect('dashboard')
    return _wrapped_view

# VISTAS DE USUARIO
@login_required
def dashboard_usuario_view(request):
    reservas = Reserva.objects.filter(solicitante=request.user)
    activas = reservas.filter(estado='Aprobada', fecha_reserva__gte=timezone.now().date()).count()
    pendientes = reservas.filter(estado='Pendiente').count()
    del_mes = reservas.filter(fecha_solicitud__month=timezone.now().month).count()
    proximas_reservas = reservas.filter(fecha_reserva__gte=timezone.now().date()).order_by('fecha_reserva', 'hora_inicio')[:5]
    context = {
        'reservas_activas': activas,
        'reservas_pendientes': pendientes,
        'reservas_del_mes': del_mes,
        'proximas_reservas': proximas_reservas,
    }
    return render(request, 'reservas/dashboard_usuario.html', context)

@login_required
def calendario_view(request):
    espacios = Espacio.objects.all()
    context = {'espacios': espacios}
    return render(request, 'reservas/calendario.html', context)

@login_required
def notificaciones_view(request):
    notificaciones = Notificacion.objects.filter(destinatario=request.user).order_by('-fecha_creacion')
    context = {'notificaciones': notificaciones}
    return render(request, 'reservas/notificaciones.html', context)

@login_required
def crear_reserva_view(request):
    if request.method == 'POST':
        try:
            espacio_id = request.POST.get('espacio_id')
            reserva = Reserva.objects.create(
                espacio_id=espacio_id,
                solicitante=request.user,
                fecha_reserva=request.POST.get('reservationDate'),
                hora_inicio=request.POST.get('startTime'),
                hora_fin=request.POST.get('endTime'),
                proposito=request.POST.get('purpose'),
                num_asistentes=request.POST.get('attendees')
            )
            return redirect('reserva_exitosa', reserva_id=reserva.id)
        except Exception as e:
            print(f"Error al crear reserva: {e}")
    espacios = Espacio.objects.filter(estado='Disponible')
    context = {'espacios': espacios}
    return render(request, 'reservas/crear_reserva.html', context)

@login_required
def reserva_exitosa_view(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, solicitante=request.user)
    context = {'reserva': reserva}
    return render(request, 'reservas/reserva_exitosa.html', context)

@login_required
def detalle_reserva_view(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    historial = HistorialAprobacion.objects.filter(reserva=reserva).order_by('fecha_accion')
    context = {'reserva': reserva, 'historial': historial}
    return render(request, 'reservas/detalle_reserva.html', context)

@login_required
def cancelar_reserva_view(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    if request.method == 'POST':
        motivo = request.POST.get('cancelReason')
        reserva.estado = 'Cancelada'
        reserva.save()
        HistorialAprobacion.objects.create(
            reserva=reserva,
            usuario_admin=request.user,
            tipo_accion='Cancelada',
            motivo=motivo
        )
        return redirect('dashboard')
    context = {'reserva': reserva}
    return render(request, 'reservas/cancelar_reserva.html', context)

# VISTAS DE ADMINISTRADOR
@login_required
@admin_required
def dashboard_admin_view(request):
    pendientes = Reserva.objects.filter(estado='Pendiente').count()
    reservas_hoy = Reserva.objects.filter(fecha_reserva=timezone.now().date()).count()
    usuarios_activos = User.objects.filter(is_active=True).count()
    context = {
        'solicitudes_pendientes': pendientes,
        'reservas_hoy': reservas_hoy,
        'usuarios_activos': usuarios_activos,
    }
    return render(request, 'reservas/dashboard_admin.html', context)

@login_required
@admin_required
def gestion_usuarios_view(request):
    usuarios = PerfilUsuario.objects.all().select_related('user', 'area')
    context = {'usuarios': usuarios}
    return render(request, 'reservas/gestion_usuarios.html', context)

@login_required
@admin_required
def gestion_espacios_view(request):
    espacios = Espacio.objects.all()
    context = {'espacios': espacios}
    return render(request, 'reservas/gestion_espacios.html', context)

@login_required
@admin_required
def solicitudes_pendientes_view(request):
    solicitudes = Reserva.objects.filter(estado='Pendiente').select_related('espacio', 'solicitante')
    context = {'solicitudes': solicitudes}
    return render(request, 'reservas/solicitudes_pendientes.html', context)

@login_required
@admin_required
def revisar_solicitud_view(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    if request.method == 'POST':
        accion = request.POST.get('accion')
        motivo = request.POST.get('motivo', '')
        reserva.estado = accion
        reserva.save()
        HistorialAprobacion.objects.create(
            reserva=reserva,
            usuario_admin=request.user,
            tipo_accion=accion,
            motivo=motivo
        )
        return redirect('solicitudes_pendientes')
    context = {'reserva': reserva}
    return render(request, 'reservas/revisar_solicitud.html', context)

@login_required
@admin_required
def reportes_view(request):
    # Estadísticas para reportes
    total_reservas = Reserva.objects.count()
    reservas_aprobadas = Reserva.objects.filter(estado='Aprobada').count()
    ocupacion_promedio = (reservas_aprobadas / total_reservas * 100) if total_reservas > 0 else 0
    context = {
        'total_reservas': total_reservas,
        'reservas_aprobadas': reservas_aprobadas,
        'ocupacion_promedio': ocupacion_promedio,
    }
    return render(request, 'reservas/reportes.html', context)

@login_required
@admin_required
def notificaciones_admin_view(request):
    notificaciones = Notificacion.objects.all().order_by('-fecha_creacion')
    context = {'notificaciones': notificaciones}
    return render(request, 'reservas/notificaciones_admin.html', context)

# VISTAS DE API
class EspacioViewSet(viewsets.ModelViewSet):
    queryset = Espacio.objects.all()
    serializer_class = EspacioSerializer

class ReservaViewSet(viewsets.ModelViewSet):
    queryset = Reserva.objects.all()
    serializer_class = ReservaSerializer
    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(solicitante=self.request.user)
        return queryset

class PerfilUsuarioViewSet(viewsets.ModelViewSet):
    queryset = PerfilUsuario.objects.all()
    serializer_class = PerfilUsuarioSerializer

class EquipamientoViewSet(viewsets.ModelViewSet):
    queryset = Equipamiento.objects.all()
    serializer_class = EquipamientoSerializer

class AreaViewSet(viewsets.ModelViewSet):
    queryset = Area.objects.all()
    serializer_class = AreaSerializer

class NotificacionViewSet(viewsets.ModelViewSet):
    queryset = Notificacion.objects.all()
    serializer_class = NotificacionSerializer

class HistorialAprobacionViewSet(viewsets.ModelViewSet):
    queryset = HistorialAprobacion.objects.all()
    serializer_class = HistorialAprobacionSerializer