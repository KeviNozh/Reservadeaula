# reservas/services.py
from django.utils import timezone
from .models import Notificacion, Reserva
from django.contrib.auth.models import User

class NotificacionService:
    
    @staticmethod
    def crear_notificacion_reserva(reserva, tipo, titulo, mensaje):
        """
        Crea una notificación relacionada con una reserva
        """
        notificacion = Notificacion.objects.create(
            destinatario=reserva.solicitante,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            reserva=reserva
        )
        return notificacion
    
    @staticmethod
    def notificar_aprobacion_reserva(reserva, comentario_admin=None):
        mensaje = f"Tu reserva para {reserva.espacio.nombre} el {reserva.fecha_reserva} ha sido APROBADA."
        if comentario_admin:
            mensaje += f"\nComentario del administrador: {comentario_admin}"
        
        return NotificacionService.crear_notificacion_reserva(
            reserva=reserva,
            tipo='reserva_aprobada',
            titulo='✅ Reserva Aprobada',
            mensaje=mensaje
        )
    
    @staticmethod
    def notificar_rechazo_reserva(reserva, motivo):
        mensaje = f"Tu reserva para {reserva.espacio.nombre} el {reserva.fecha_reserva} ha sido RECHAZADA.\nMotivo: {motivo}"
        
        return NotificacionService.crear_notificacion_reserva(
            reserva=reserva,
            tipo='reserva_rechazada',
            titulo='❌ Reserva Rechazada',
            mensaje=mensaje
        )
    
    @staticmethod
    def notificar_cancelacion_reserva(reserva, motivo=None):
        mensaje = f"Tu reserva para {reserva.espacio.nombre} el {reserva.fecha_reserva} ha sido CANCELADA."
        if motivo:
            mensaje += f"\nMotivo: {motivo}"
        
        return NotificacionService.crear_notificacion_reserva(
            reserva=reserva,
            tipo='reserva_cancelada',
            titulo='📝 Reserva Cancelada',
            mensaje=mensaje
        )
    
    @staticmethod
    def notificar_creacion_reserva(reserva):
        mensaje = f"Tu solicitud de reserva para {reserva.espacio.nombre} el {reserva.fecha_reserva} ha sido recibida y está pendiente de aprobación."
        
        return NotificacionService.crear_notificacion_reserva(
            reserva=reserva,
            tipo='reserva_pendiente',
            titulo='⏰ Reserva Pendiente',
            mensaje=mensaje
        )
    
    @staticmethod
    def obtener_notificaciones_usuario(usuario, no_leidas=False, limite=10):
        """
        Obtiene las notificaciones de un usuario
        """
        notificaciones = Notificacion.objects.filter(destinatario=usuario)
        
        if no_leidas:
            notificaciones = notificaciones.filter(leida=False)
        
        return notificaciones.order_by('-fecha_creacion')[:limite]
    
    @staticmethod
    def marcar_todas_como_leidas(usuario):
        """
        Marca todas las notificaciones de un usuario como leídas
        """
        notificaciones = Notificacion.objects.filter(
            destinatario=usuario, 
            leida=False
        )
        
        for notificacion in notificaciones:
            notificacion.marcar_como_leida()
        
        return notificaciones.count()