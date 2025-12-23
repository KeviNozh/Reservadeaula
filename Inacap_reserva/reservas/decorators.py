from functools import wraps
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
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

def es_admin():
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            try:
                perfil = PerfilUsuario.objects.get(user=request.user)
                if perfil.rol in ['Administrativo', 'Investigacion', 'Aprobador', 'SuperAdmin']:
                    return view_func(request, *args, **kwargs)
            except PerfilUsuario.DoesNotExist:
                pass
            
            raise PermissionDenied("No tienes permisos de administrador")
        return _wrapped_view
    return decorator

def es_usuario_normal():
    """
    Decorador para usuarios normales (no administradores)
    """
    def decorator(view_func):
        @wraps(view_func)
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