from django.utils import timezone
from .models import Notificacion, Reserva
from django.contrib.auth.models import User

class NotificacionService:
    
    @staticmethod
    def crear_notificacion(destinatario, tipo, titulo, mensaje, reserva=None):
        """
        Crea una notificación genérica
        """
        notificacion = Notificacion.objects.create(
            destinatario=destinatario,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            reserva=reserva
        )
        print(f"📧 Notificación creada: {titulo} para {destinatario.username}")
        return notificacion
    
    @staticmethod
    def crear_notificacion_reserva(reserva, tipo, titulo, mensaje):
        """
        Crea una notificación relacionada con una reserva
        """
        return NotificacionService.crear_notificacion(
            destinatario=reserva.solicitante,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            reserva=reserva
        )
    
    @staticmethod
    def notificar_creacion_reserva(reserva):
        """
        Notifica al usuario que su reserva fue creada exitosamente
        """
        mensaje = f"Tu solicitud de reserva para {reserva.espacio.nombre} el {reserva.fecha_reserva.strftime('%d/%m/%Y')} de {reserva.hora_inicio.strftime('%H:%M')} a {reserva.hora_fin.strftime('%H:%M')} ha sido recibida y está pendiente de aprobación."
        
        return NotificacionService.crear_notificacion_reserva(
            reserva=reserva,
            tipo='reserva_creada',
            titulo='📋 Reserva Creada Exitosamente',
            mensaje=mensaje
        )
    
    @staticmethod
    def notificar_aprobacion_reserva(reserva, comentario_admin=None):
        """
        Notifica al usuario que su reserva fue aprobada
        """
        mensaje = f"✅ Tu reserva para {reserva.espacio.nombre} el {reserva.fecha_reserva.strftime('%d/%m/%Y')} ha sido APROBADA."
        if comentario_admin:
            mensaje += f"\n\nComentario del administrador: {comentario_admin}"
        
        return NotificacionService.crear_notificacion_reserva(
            reserva=reserva,
            tipo='reserva_aprobada',
            titulo='✅ Reserva Aprobada',
            mensaje=mensaje
        )
    
    @staticmethod
    def notificar_rechazo_reserva(reserva, motivo):
        """
        Notifica al usuario que su reserva fue rechazada
        """
        mensaje = f"❌ Tu reserva para {reserva.espacio.nombre} el {reserva.fecha_reserva.strftime('%d/%m/%Y')} ha sido RECHAZADA.\n\nMotivo: {motivo}"
        
        return NotificacionService.crear_notificacion_reserva(
            reserva=reserva,
            tipo='reserva_rechazada',
            titulo='❌ Reserva Rechazada',
            mensaje=mensaje
        )
    
    @staticmethod
    def notificar_cancelacion_reserva(reserva, motivo=None):
        """
        Notifica al usuario que su reserva fue cancelada
        """
        mensaje = f"📝 Tu reserva para {reserva.espacio.nombre} el {reserva.fecha_reserva.strftime('%d/%m/%Y')} ha sido CANCELADA."
        if motivo:
            mensaje += f"\n\nMotivo: {motivo}"
        
        return NotificacionService.crear_notificacion_reserva(
            reserva=reserva,
            tipo='reserva_cancelada',
            titulo='📝 Reserva Cancelada',
            mensaje=mensaje
        )
    
    @staticmethod
    def notificar_cambio_estado_reserva(reserva, estado_anterior, estado_nuevo, motivo=None):
        """
        Notifica al usuario sobre cambios en el estado de su reserva
        """
        mensaje = f"🔄 El estado de tu reserva para {reserva.espacio.nombre} ha cambiado de '{estado_anterior}' a '{estado_nuevo}'."
        if motivo:
            mensaje += f"\n\nMotivo: {motivo}"
        
        return NotificacionService.crear_notificacion_reserva(
            reserva=reserva,
            tipo='reserva_pendiente',
            titulo='🔄 Estado de Reserva Actualizado',
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