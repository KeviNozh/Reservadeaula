# services.py - Versión corregida
from django.utils import timezone
from .models import Notificacion, Reserva
from django.contrib.auth.models import User

class NotificacionService:
    
    @staticmethod
    def crear_notificacion(destinatario, tipo, titulo, mensaje, reserva=None):
        """
        Crea una notificación genérica - VERSIÓN CORREGIDA
        """
        try:
            notificacion = Notificacion.objects.create(
                destinatario=destinatario,
                tipo=tipo,
                titulo=titulo,
                mensaje=mensaje,
                reserva=reserva  # Ahora se guarda correctamente
            )
            print(f"📧 Notificación creada: {titulo} para {destinatario.username} - Reserva: {reserva.id if reserva else 'N/A'}")
            return notificacion
        except Exception as e:
            print(f"❌ Error creando notificación: {e}")
            return None
    
    @staticmethod
    def crear_notificacion_reserva(reserva, tipo, titulo, mensaje):
        """
        Crea una notificación relacionada con una reserva - VERSIÓN CORREGIDA
        """
        try:
            return NotificacionService.crear_notificacion(
                destinatario=reserva.solicitante,
                tipo=tipo,
                titulo=titulo,
                mensaje=mensaje,
                reserva=reserva  # Pasar la instancia completa de reserva
            )
        except Exception as e:
            print(f"❌ Error en crear_notificacion_reserva: {e}")
            return None
    
    @staticmethod
    def notificar_creacion_reserva(reserva):
        """
        Notifica al usuario que su reserva fue creada exitosamente - VERSIÓN CORREGIDA
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

    # Los demás métodos permanecen igual...