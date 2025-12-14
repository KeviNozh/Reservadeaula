from django.db.models import Q
from django.utils import timezone
from .models import Reserva, Mantenimiento, HorariosDisponibilidad
from datetime import datetime, time, date

def validar_disponibilidad_espacio(espacio_id, fecha, hora_inicio, hora_fin, reserva_excluida_id=None):
    """
    Valida que no existan reservas solapadas para el mismo espacio
    
    Args:
        espacio_id: ID del espacio a validar
        fecha: fecha de la reserva
        hora_inicio: hora de inicio
        hora_fin: hora de fin
        reserva_excluida_id: ID de reserva a excluir (para ediciones)
    
    Returns:
        tuple: (disponible, mensaje_error)
    """
    try:
        # Convertir a objetos time si son strings
        if isinstance(hora_inicio, str):
            hora_inicio = datetime.strptime(hora_inicio, '%H:%M:%S').time()
        if isinstance(hora_fin, str):
            hora_fin = datetime.strptime(hora_fin, '%H:%M:%S').time()
        
        # ======== VALIDACIONES NUEVAS ========
        
        # 1. Validar que la hora de fin sea después de la hora de inicio
        if hora_inicio >= hora_fin:
            return False, "La hora de fin debe ser posterior a la hora de inicio"
        
        # 2. Validar duración mínima (30 minutos)
        duracion_minutos = (hora_fin.hour * 60 + hora_fin.minute) - (hora_inicio.hour * 60 + hora_inicio.minute)
        if duracion_minutos < 30:
            return False, "La duración mínima de reserva es de 30 minutos"
        
        # 3. Validar duración máxima (8 horas)
        if duracion_minutos > 480:
            return False, "La duración máxima de reserva es de 8 horas"
        
        # ======== VALIDACIONES EXISTENTES ========
        
        # Validar reservas existentes
        reservas_query = Reserva.objects.filter(
            espacio_id=espacio_id,
            fecha_reserva=fecha,
            estado__in=['Aprobada', 'Pendiente']  # Solo considerar reservas activas
        )
        
        # Excluir la reserva actual si se está editando
        if reserva_excluida_id:
            reservas_query = reservas_query.exclude(id=reserva_excluida_id)
        
        # ======== CORRECCIÓN CRÍTICA AQUÍ ========
        # Validación CORREGIDA de solapamiento
        # Buscar reservas que SE SOLAPEN (no las que NO se solapen)
        reservas_solapadas = reservas_query.filter(
            hora_inicio__lt=hora_fin,    # La reserva existente comienza ANTES de que termine la nueva
            hora_fin__gt=hora_inicio     # La reserva existente termina DESPUÉS de que comience la nueva
        )
        
        if reservas_solapadas.exists():
            # Obtener información de la reserva que causa conflicto
            conflicto = reservas_solapadas.first()
            return False, f"Conflicto con reserva existente de {conflicto.hora_inicio.strftime('%H:%M')} a {conflicto.hora_fin.strftime('%H:%M')}"
        
        # Validar mantenimiento programado
        mantenimiento_activo = Mantenimiento.objects.filter(
            id_espacio_id=espacio_id,
            fecha_inicio__lte=fecha,
            fecha_fin__gte=fecha,
            estado__in=['Programado', 'En Proceso']
        ).exists()
        
        if mantenimiento_activo:
            return False, "El espacio está en mantenimiento en la fecha seleccionada"
        
        # Validar horarios de disponibilidad del espacio
        dia_semana = fecha.strftime('%A')
        dias_semana_es = {
            'Monday': 'Lunes',
            'Tuesday': 'Martes',
            'Wednesday': 'Miércoles',
            'Thursday': 'Jueves',
            'Friday': 'Viernes',
            'Saturday': 'Sábado',
            'Sunday': 'Domingo'
        }
        
        dia_semana_es = dias_semana_es.get(dia_semana, dia_semana)
        
        horario_disponibilidad = HorariosDisponibilidad.objects.filter(
            id_espacio_id=espacio_id,
            dia_semana=dia_semana_es,
            fecha_inicio_vigencia__lte=fecha
        ).order_by('-fecha_inicio_vigencia').first()
        
        if horario_disponibilidad:
            if hora_inicio < horario_disponibilidad.hora_apertura:
                return False, f"El espacio abre a las {horario_disponibilidad.hora_apertura.strftime('%H:%M')}"
            
            if hora_fin > horario_disponibilidad.hora_cierre:
                return False, f"El espacio cierra a las {horario_disponibilidad.hora_cierre.strftime('%H:%M')}"
        
        return True, "El espacio está disponible"
        
    except Exception as e:
        return False, f"Error al validar disponibilidad: {str(e)}"

def calcular_duracion(hora_inicio, hora_fin):
    """
    Calcular la duración en formato legible
    """
    try:
        if isinstance(hora_inicio, str):
            hora_inicio = datetime.strptime(hora_inicio, '%H:%M:%S').time()
        if isinstance(hora_fin, str):
            hora_fin = datetime.strptime(hora_fin, '%H:%M:%S').time()
        
        diferencia = datetime.combine(date.today(), hora_fin) - datetime.combine(date.today(), hora_inicio)
        horas = diferencia.seconds // 3600
        minutos = (diferencia.seconds % 3600) // 60
        
        if horas > 0:
            return f"{horas} hora{'s' if horas > 1 else ''} {minutos} minuto{'s' if minutos > 1 else ''}"
        else:
            return f"{minutos} minutos"
    except Exception as e:
        return "Duración no disponible"

def obtener_estadisticas_uso_espacio(espacio_id, mes=None, año=None):
    """
    Obtiene estadísticas de uso de un espacio
    """
    if not mes:
        mes = timezone.now().month
    if not año:
        año = timezone.now().year
    
    reservas_mes = Reserva.objects.filter(
        espacio_id=espacio_id,
        fecha_reserva__month=mes,
        fecha_reserva__year=año,
        estado='Aprobada'
    )
    
    return {
        'total_reservas': reservas_mes.count(),
        'dias_ocupados': reservas_mes.dates('fecha_reserva', 'day').count(),
        'horas_totales': sum(
            (reserva.hora_fin.hour - reserva.hora_inicio.hour) + 
            (reserva.hora_fin.minute - reserva.hora_inicio.minute) / 60 
            for reserva in reservas_mes
        )
    }

# ======== FUNCIONES NUEVAS AÑADIDAS ========

def validar_anticipacion_reserva(fecha_reserva, hora_inicio):
    """
    Valida que la reserva tenga suficiente anticipación
    
    Returns:
        tuple: (valido, mensaje_error)
    """
    from datetime import timedelta
    
    try:
        ahora = timezone.now()
        fecha_hora_reserva = datetime.combine(fecha_reserva, hora_inicio)
        
        # Convertir a timezone aware si no lo es
        if timezone.is_naive(fecha_hora_reserva):
            fecha_hora_reserva = timezone.make_aware(fecha_hora_reserva)
        
        # Mínimo 2 horas de anticipación
        min_anticipacion = timedelta(hours=2)
        
        if fecha_hora_reserva < ahora + min_anticipacion:
            return False, "Se requiere al menos 2 horas de anticipación para las reservas"
        
        # Máximo 30 días de anticipación
        max_anticipacion = timedelta(days=30)
        if fecha_hora_reserva > ahora + max_anticipacion:
            return False, "No se pueden hacer reservas con más de 30 días de anticipación"
        
        return True, "Horario válido"
        
    except Exception as e:
        return False, f"Error validando anticipación: {str(e)}"

def validar_limite_reservas_usuario(usuario, fecha_reserva):
    """
    Valida que el usuario no exceda el límite de reservas por día
    
    Returns:
        tuple: (valido, mensaje_error)
    """
    try:
        # Máximo 3 reservas por día
        reservas_del_dia = Reserva.objects.filter(
            solicitante=usuario,
            fecha_reserva=fecha_reserva,
            estado__in=['Aprobada', 'Pendiente']
        ).count()
        
        if reservas_del_dia >= 3:
            return False, "Límite de 3 reservas por día alcanzado"
        
        return True, "Límite de reservas válido"
        
    except Exception as e:
        return False, f"Error validando límite de reservas: {str(e)}"