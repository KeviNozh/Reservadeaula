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
        
        # Validar que la hora de fin sea después de la hora de inicio
        if hora_inicio >= hora_fin:
            return False, "La hora de fin debe ser posterior a la hora de inicio"
        
        # Validar reservas existentes
        reservas_query = Reserva.objects.filter(
            espacio_id=espacio_id,
            fecha_reserva=fecha,
            estado__in=['Aprobada', 'Pendiente']  # Solo considerar reservas activas
        )
        
        # Excluir la reserva actual si se está editando
        if reserva_excluida_id:
            reservas_query = reservas_query.exclude(id=reserva_excluida_id)
        
        # Buscar solapamientos
        reservas_solapadas = reservas_query.exclude(
            Q(hora_fin__lte=hora_inicio) | Q(hora_inicio__gte=hora_fin)
        )
        
        if reservas_solapadas.exists():
            return False, "El espacio no está disponible en el horario seleccionado"
        
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
            if hora_inicio < horario_disponibilidad.hora_apertura or hora_fin > horario_disponibilidad.hora_cierre:
                return False, f"El espacio solo está disponible de {horario_disponibilidad.hora_apertura} a {horario_disponibilidad.hora_cierre}"
        
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