from django.utils import timezone
from .models import Notificacion, Reserva
from django.contrib.auth.models import User

class NotificacionService:
    
    @staticmethod
    def crear_notificacion(destinatario, tipo, titulo, mensaje, reserva=None):
        """
        Crea una notificación genérica
        """
        try:
            notificacion = Notificacion.objects.create(
                destinatario=destinatario,
                tipo=tipo,
                titulo=titulo,
                mensaje=mensaje,
                reserva=reserva
            )
            print(f"📧 Notificación creada: {titulo} para {destinatario.username}")
            return notificacion
        except Exception as e:
            print(f"❌ Error creando notificación: {e}")
            return None
    
    @staticmethod
    def crear_notificacion_reserva(reserva, tipo, titulo, mensaje):
        """
        Crea una notificación relacionada con una reserva
        """
        try:
            return NotificacionService.crear_notificacion(
                destinatario=reserva.solicitante,
                tipo=tipo,
                titulo=titulo,
                mensaje=mensaje,
                reserva=reserva
            )
        except Exception as e:
            print(f"❌ Error en crear_notificacion_reserva: {e}")
            return None
    
    @staticmethod
    def notificar_creacion_reserva(reserva):
        """
        Notifica al usuario que su reserva fue creada exitosamente
        """
        try:
            mensaje = f"Tu solicitud de reserva para {reserva.espacio.nombre} el {reserva.fecha_reserva.strftime('%d/%m/%Y')} de {reserva.hora_inicio.strftime('%H:%M')} a {reserva.hora_fin.strftime('%H:%M')} ha sido recibida y está pendiente de aprobación."
            
            notificacion = NotificacionService.crear_notificacion_reserva(
                reserva=reserva,
                tipo='reserva_creada',
                titulo='📋 Reserva Creada Exitosamente',
                mensaje=mensaje
            )
            
            if notificacion:
                print(f"✅ Notificación de creación enviada para reserva {reserva.id}")
            else:
                print(f"❌ Falló notificación de creación para reserva {reserva.id}")
                
            return notificacion
        except Exception as e:
            print(f"❌ Error en notificar_creacion_reserva: {e}")
            return None
    
    @staticmethod
    def notificar_aprobacion_reserva(reserva, comentario_admin=None):
        """
        Notifica al usuario que su reserva fue aprobada - VERSIÓN CORREGIDA
        """
        try:
            mensaje = f"✅ Tu reserva para {reserva.espacio.nombre} el {reserva.fecha_reserva.strftime('%d/%m/%Y')} ha sido APROBADA."
            if comentario_admin:
                mensaje += f"\n\nComentario del administrador: {comentario_admin}"
            
            notificacion = NotificacionService.crear_notificacion_reserva(
                reserva=reserva,
                tipo='reserva_aprobada',
                titulo='✅ Reserva Aprobada',
                mensaje=mensaje
            )
            
            if notificacion:
                print(f"✅ Notificación de aprobación enviada para reserva {reserva.id}")
            else:
                print(f"❌ Falló notificación de aprobación para reserva {reserva.id}")
                
            return notificacion
        except Exception as e:
            print(f"❌ Error en notificar_aprobacion_reserva: {e}")
            return None
    
    @staticmethod
    def notificar_rechazo_reserva(reserva, motivo):
        """
        Notifica al usuario que su reserva fue rechazada - VERSIÓN CORREGIDA
        """
        try:
            mensaje = f"❌ Tu reserva para {reserva.espacio.nombre} el {reserva.fecha_reserva.strftime('%d/%m/%Y')} ha sido RECHAZADA.\n\nMotivo: {motivo}"
            
            notificacion = NotificacionService.crear_notificacion_reserva(
                reserva=reserva,
                tipo='reserva_rechazada',
                titulo='❌ Reserva Rechazada',
                mensaje=mensaje
            )
            
            if notificacion:
                print(f"✅ Notificación de rechazo enviada para reserva {reserva.id}")
            else:
                print(f"❌ Falló notificación de rechazo para reserva {reserva.id}")
                
            return notificacion
        except Exception as e:
            print(f"❌ Error en notificar_rechazo_reserva: {e}")
            return None
    
    # Los demás métodos permanecen igual...
    @staticmethod
    def notificar_cancelacion_reserva(reserva, motivo=None):
        """Notifica al usuario que su reserva fue cancelada"""
        try:
            mensaje = f"📝 Tu reserva para {reserva.espacio.nombre} el {reserva.fecha_reserva.strftime('%d/%m/%Y')} ha sido CANCELADA."
            if motivo:
                mensaje += f"\n\nMotivo: {motivo}"
            
            return NotificacionService.crear_notificacion_reserva(
                reserva=reserva,
                tipo='reserva_cancelada',
                titulo='📝 Reserva Cancelada',
                mensaje=mensaje
            )
        except Exception as e:
            print(f"❌ Error en notificar_cancelacion_reserva: {e}")
            return None

    @staticmethod
    def obtener_notificaciones_usuario(usuario, no_leidas=False, limite=10):
        """Obtiene las notificaciones de un usuario"""
        try:
            notificaciones = Notificacion.objects.filter(destinatario=usuario)
            
            if no_leidas:
                notificaciones = notificaciones.filter(leida=False)
            
            return notificaciones.select_related('reserva', 'reserva__espacio').order_by('-fecha_creacion')[:limite]
        except Exception as e:
            print(f"❌ Error en obtener_notificaciones_usuario: {e}")
            return []
    
    @staticmethod
    def marcar_como_leida(notificacion_id):
        """
        Marca una notificación específica como leída
        """
        try:
            notificacion = Notificacion.objects.get(id=notificacion_id)
            notificacion.marcar_como_leida()
            return True
        except Notificacion.DoesNotExist:
            return False
    
    @staticmethod
    def marcar_todas_como_leidas(usuario):
        """
        Marca todas las notificaciones de un usuario como leídas
        """
        notificaciones = Notificacion.objects.filter(
            destinatario=usuario, 
            leida=False
        )
        
        count = notificaciones.count()
        notificaciones.update(leida=True, fecha_lectura=timezone.now())
        
        print(f"📭 Marcadas {count} notificaciones como leídas para {usuario.username}")
        return count
    
    @staticmethod
    def contar_notificaciones_no_leidas(usuario):
        """
        Cuenta las notificaciones no leídas de un usuario
        """
        return Notificacion.objects.filter(
            destinatario=usuario,
            leida=False
        ).count()

class NotificacionAdminService:
    
    @staticmethod
    def crear_notificacion_admin(tipo, titulo, mensaje, prioridad='media', usuario_relacionado=None, 
                               reserva=None, espacio=None, request=None):
        """
        Crea una notificación para administradores
        """
        try:
            notificacion = NotificacionAdmin.objects.create(
                tipo=tipo,
                titulo=titulo,
                mensaje=mensaje,
                prioridad=prioridad,
                usuario_relacionado=usuario_relacionado,
                reserva=reserva,
                espacio=espacio
            )
            
            # Agregar información de la solicitud si está disponible
            if request:
                notificacion.ip_address = get_client_ip(request)
                notificacion.user_agent = request.META.get('HTTP_USER_AGENT', '')
                notificacion.save()
            
            print(f"📢 Notificación Admin creada: {titulo}")
            return notificacion
            
        except Exception as e:
            print(f"❌ Error creando notificación admin: {e}")
            return None
    
    @staticmethod
    def notificar_nueva_reserva(reserva, request=None):
        """Notifica a los admin sobre nueva reserva"""
        mensaje = f"El usuario {reserva.solicitante.username} ha creado una nueva reserva para {reserva.espacio.nombre} el {reserva.fecha_reserva.strftime('%d/%m/%Y')} de {reserva.hora_inicio.strftime('%H:%M')} a {reserva.hora_fin.strftime('%H:%M')}."
        
        return NotificacionAdminService.crear_notificacion_admin(
            tipo='reserva_creada',
            titulo='📋 Nueva Reserva Creada',
            mensaje=mensaje,
            prioridad='alta',
            usuario_relacionado=reserva.solicitante,
            reserva=reserva,
            request=request
        )
    
    @staticmethod
    def notificar_usuario_registrado(usuario, request=None):
        """Notifica a los admin sobre nuevo usuario registrado"""
        mensaje = f"El usuario {usuario.username} ({usuario.first_name} {usuario.last_name}) se ha registrado en el sistema."
        
        return NotificacionAdminService.crear_notificacion_admin(
            tipo='usuario_registrado',
            titulo='👤 Nuevo Usuario Registrado',
            mensaje=mensaje,
            prioridad='media',
            usuario_relacionado=usuario,
            request=request
        )
    
    @staticmethod
    def notificar_espacio_creado(espacio, usuario_admin, request=None):
        """Notifica a los admin sobre nuevo espacio creado"""
        mensaje = f"El administrador {usuario_admin.username} ha creado el espacio '{espacio.nombre}' ({espacio.tipo})."
        
        return NotificacionAdminService.crear_notificacion_admin(
            tipo='espacio_creado',
            titulo='🏢 Nuevo Espacio Creado',
            mensaje=mensaje,
            prioridad='media',
            usuario_relacionado=usuario_admin,
            espacio=espacio,
            request=request
        )
    
    @staticmethod
    def notificar_sesion_admin(usuario_admin, accion, request=None):
        """Notifica sobre sesiones de administradores"""
        if accion == 'inicio':
            titulo = '🔐 Sesión de Admin Iniciada'
            mensaje = f"El administrador {usuario_admin.username} ha iniciado sesión."
            tipo = 'sesion_iniciada'
        else:  # cierre
            titulo = '🚪 Sesión de Admin Cerrada'
            mensaje = f"El administrador {usuario_admin.username} ha cerrado sesión."
            tipo = 'sesion_cerrada'
        
        return NotificacionAdminService.crear_notificacion_admin(
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            prioridad='baja',
            usuario_relacionado=usuario_admin,
            request=request
        )
    
    @staticmethod
    def notificar_accion_reserva(reserva, usuario_admin, accion, motivo=None, request=None):
        """Notifica acciones sobre reservas (aprobación/rechazo)"""
        if accion == 'aprobada':
            titulo = '✅ Reserva Aprobada'
            mensaje = f"El administrador {usuario_admin.username} ha APROBADO la reserva de {reserva.espacio.nombre} para {reserva.solicitante.username}."
            tipo = 'reserva_aprobada'
        else:  # rechazada
            titulo = '❌ Reserva Rechazada'
            mensaje = f"El administrador {usuario_admin.username} ha RECHAZADO la reserva de {reserva.espacio.nombre} para {reserva.solicitante.username}."
            if motivo:
                mensaje += f" Motivo: {motivo}"
            tipo = 'reserva_rechazada'
        
        return NotificacionAdminService.crear_notificacion_admin(
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            prioridad='alta',
            usuario_relacionado=usuario_admin,
            reserva=reserva,
            request=request
        )

def get_client_ip(request):
    """Obtiene la IP real del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip