# reservas/decorators.py
from functools import wraps
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import messages  # <-- AGREGAR ESTA LÍNEA
from .models import PerfilUsuario

def rol_requerido(*roles_permisos):
    """
    Decorador para restringir acceso basado en el rol del usuario.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            try:
                perfil = PerfilUsuario.objects.get(user=request.user)
                
                # Verificar si el rol del usuario está en los roles permitidos
                if perfil.rol not in roles_permisos:
                    # Si es solicitud AJAX, retornar JSON
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'error': f'Acceso denegado. Rol requerido: {", ".join(roles_permisos)}'
                        }, status=403)
                    
                    # Redirigir según el rol del usuario
                    if perfil.rol in ['Administrativo', 'Investigacion', 'Aprobador', 'SuperAdmin']:
                        messages.error(request, 'Acceso denegado. Esta área es solo para usuarios normales.')
                        return redirect('admin_dashboard')
                    else:
                        messages.error(request, 'Acceso denegado. Esta área es solo para administradores.')
                        return redirect('dashboard')
                
            except PerfilUsuario.DoesNotExist:
                return redirect('login')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def es_usuario_normal():
    """
    Decorador para verificar que el usuario es normal (no admin)
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            try:
                perfil = PerfilUsuario.objects.get(user=request.user)
                
                # Roles de usuario normal
                roles_usuario = ['Usuario', 'Docente']
                
                if perfil.rol not in roles_usuario:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'error': 'Acceso denegado. Esta funcionalidad es solo para usuarios normales.'
                        }, status=403)
                    
                    messages.error(request, 'Acceso denegado. Esta área es solo para usuarios normales.')
                    return redirect('admin_dashboard')
                
            except PerfilUsuario.DoesNotExist:
                return redirect('login')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def es_administrador():
    """
    Decorador de fábrica que retorna un decorador real
    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            # Verificar si el usuario está autenticado
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Verificar si tiene perfil y rol de administrador
            try:
                perfil = PerfilUsuario.objects.get(user=request.user)
                # Roles que se consideran administradores
                if perfil.rol in ['Administrativo', 'Investigacion', 'Aprobador', 'SuperAdmin']:
                    return view_func(request, *args, **kwargs)
            except PerfilUsuario.DoesNotExist:
                pass
            
            # Si no es administrador, denegar acceso
            raise PermissionDenied("No tienes permisos de administrador")
        return _wrapped_view
    return decorator

def es_usuario_normal():
    """
    Decorador para usuarios normales (no administradores)
    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            try:
                perfil = PerfilUsuario.objects.get(user=request.user)
                # Usuarios normales: cualquier rol que NO sea administrador
                if perfil.rol not in ['Administrativo', 'Investigacion', 'Aprobador', 'SuperAdmin']:
                    return view_func(request, *args, **kwargs)
            except PerfilUsuario.DoesNotExist:
                # Si no tiene perfil, permitir acceso (podrías ajustar esto)
                return view_func(request, *args, **kwargs)
            
            # Si es administrador, redirigir al dashboard admin
            return redirect('admin_dashboard')
        return _wrapped_view
    return decorator

def rol_requerido(roles_permitidos):
    """
    Decorador genérico para verificar roles específicos
    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            try:
                perfil = PerfilUsuario.objects.get(user=request.user)
                if perfil.rol in roles_permitidos:
                    return view_func(request, *args, **kwargs)
            except PerfilUsuario.DoesNotExist:
                pass
            
            raise PermissionDenied(f"Se requiere uno de los siguientes roles: {', '.join(roles_permitidos)}")
        return _wrapped_view
    return decorator