from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Area(models.Model):
    nombre_area = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.nombre_area

class PerfilUsuario(models.Model):
    ROL_CHOICES = (
        ('Usuario', 'Usuario'),
        ('Docente', 'Docente'),
        ('Investigacion', 'Investigación'),  # Cambiado
        ('Administrativo', 'Administrativo'),  # Nuevo rol
        ('Aprobador', 'Aprobador')
    )
    
    ESTADO_CHOICES = (
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('suspendido', 'Suspendido')
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rol = models.CharField(max_length=50, choices=ROL_CHOICES, default='Usuario')
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True)
    departamento = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=50, choices=ESTADO_CHOICES, default='activo')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    ultimo_acceso = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} ({self.rol})"

class Espacio(models.Model):
    ESTADO_CHOICES = (
        ('Disponible', 'Disponible'),
        ('Mantenimiento', 'Mantenimiento'),
        ('Fuera de Servicio', 'Fuera de Servicio'),
    )
    
    TIPO_CHOICES = (
        ('Sala de Reuniones', 'Sala de Reuniones'),
        ('Auditorio', 'Auditorio'),
        ('Laboratorio', 'Laboratorio'),
        ('Oficina', 'Oficina'),
        ('Aula', 'Aula'),
    )
    
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=100, choices=TIPO_CHOICES)
    edificio = models.CharField(max_length=100, blank=True, null=True)
    piso = models.IntegerField(blank=True, null=True)
    capacidad = models.IntegerField()
    descripcion = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=50, choices=ESTADO_CHOICES, default='Disponible')
    
    def __str__(self):
        return self.nombre
    
class Equipamiento(models.Model):
    TIPO_EQUIPO_CHOICES = (
        ('Proyector', 'Proyector'),
        ('Computador', 'Computador'),
        ('Audio', 'Sistema de Audio'),
        ('Video', 'Sistema de Video'),
        ('Mobiliario', 'Mobiliario'),
    )
    
    id_espacio = models.ForeignKey(Espacio, on_delete=models.CASCADE, related_name='equipamientos')
    nombre_equipo = models.CharField(max_length=100)
    tipo_equipo = models.CharField(max_length=100, choices=TIPO_EQUIPO_CHOICES)
    marca_modelo = models.CharField(max_length=255, blank=True, null=True)
    numero_serie = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return self.nombre_equipo

class Reserva(models.Model):
    ESTADO_CHOICES = (
        ('Pendiente', 'Pendiente'),
        ('Aprobada', 'Aprobada'),
        ('Rechazada', 'Rechazada'),
        ('Cancelada', 'Cancelada'),
    )
    
    espacio = models.ForeignKey(Espacio, on_delete=models.CASCADE)
    solicitante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservas_solicitadas')
    fecha_reserva = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    proposito = models.TextField()
    num_asistentes = models.IntegerField()
    estado = models.CharField(max_length=50, choices=ESTADO_CHOICES, default='Pendiente')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    id_aprobador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservas_aprobadas')
    comentario_admin = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Reserva de {self.espacio.nombre} por {self.solicitante.username}"

class HistorialAprobacion(models.Model):
    TIPO_ACCION_CHOICES = (
        ('Aprobada', 'Aprobada'),
        ('Rechazada', 'Rechazada'),
        ('Cancelada', 'Cancelada'),
    )
    
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE)
    usuario_admin = models.ForeignKey(User, on_delete=models.CASCADE)
    tipo_accion = models.CharField(max_length=50, choices=TIPO_ACCION_CHOICES)
    fecha_accion = models.DateField(auto_now_add=True)
    hora_accion = models.TimeField(auto_now_add=True)
    motivo = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Aprobación {self.tipo_accion} - Reserva {self.reserva.id}"

class Notificacion(models.Model):
    TIPO_CHOICES = (
        ('reserva_aprobada', 'Reserva Aprobada'),
        ('reserva_rechazada', 'Reserva Rechazada'),
        ('reserva_cancelada', 'Reserva Cancelada'),
        ('reserva_pendiente', 'Reserva Pendiente'),
        ('reserva_creada', 'Reserva Creada'),
        ('mantenimiento', 'Mantenimiento'),
        ('incidencia', 'Incidencia'),
        ('sistema', 'Sistema'),
    )
    
    destinatario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificaciones')
    tipo = models.CharField(max_length=100, choices=TIPO_CHOICES)
    titulo = models.CharField(max_length=255)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_lectura = models.DateTimeField(null=True, blank=True)
    reserva = models.ForeignKey('Reserva', on_delete=models.CASCADE, null=True, blank=True, related_name='notificaciones')  # Añadido related_name
    
    def __str__(self):
        return self.titulo
    
    def get_fecha_creacion_formateada(self):
        """Retorna la fecha formateada de manera legible"""
        return self.fecha_creacion.strftime('%d/%m/%Y %H:%M')
    
    def marcar_como_leida(self):
        """Marca la notificación como leída"""
        self.leida = True
        self.fecha_lectura = timezone.now()
        self.save()
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
    
    def get_fecha_creacion_formateada(self):
        """Retorna la fecha formateada de manera legible"""
        return self.fecha_creacion.strftime('%d/%m/%Y %H:%M')
    
    def marcar_como_leida(self):
        """Marca la notificación como leída"""
        self.leida = True
        self.fecha_lectura = timezone.now()
        self.save()
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'



class Mantenimiento(models.Model):
    ESTADO_CHOICES = (
        ('Programado', 'Programado'),
        ('En Proceso', 'En Proceso'),
        ('Completado', 'Completado'),
        ('Cancelado', 'Cancelado'),
    )
    
    TIPO_MANTENIMIENTO_CHOICES = (
        ('Preventivo', 'Preventivo'),
        ('Correctivo', 'Correctivo'),
        ('Urgente', 'Urgente'),
    )
    
    id_espacio = models.ForeignKey(Espacio, on_delete=models.CASCADE)
    tipo_mantenimiento = models.CharField(max_length=100, choices=TIPO_MANTENIMIENTO_CHOICES)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(max_length=50, choices=ESTADO_CHOICES)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    
    def __str__(self):
        return f"Mantenimiento {self.tipo_mantenimiento} - {self.id_espacio.nombre}"

class HorariosDisponibilidad(models.Model):
    DIA_SEMANA_CHOICES = (
        ('Lunes', 'Lunes'),
        ('Martes', 'Martes'),
        ('Miércoles', 'Miércoles'),
        ('Jueves', 'Jueves'),
        ('Viernes', 'Viernes'),
        ('Sábado', 'Sábado'),
        ('Domingo', 'Domingo'),
    )
    
    id_espacio = models.ForeignKey(Espacio, on_delete=models.CASCADE)
    dia_semana = models.CharField(max_length=20, choices=DIA_SEMANA_CHOICES)
    hora_apertura = models.TimeField()
    hora_cierre = models.TimeField()
    fecha_inicio_vigencia = models.DateField()
    bloques_disponibles = models.IntegerField(default=1)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.id_espacio.nombre} - {self.dia_semana}"

class Incidencia(models.Model):
    PRIORIDAD_CHOICES = (
        ('Baja', 'Baja'),
        ('Media', 'Media'),
        ('Alta', 'Alta'),
        ('Crítica', 'Crítica'),
    )
    
    ESTADO_CHOICES = (
        ('Reportada', 'Reportada'),
        ('En Proceso', 'En Proceso'),
        ('Resuelta', 'Resuelta'),
        ('Cerrada', 'Cerrada'),
    )
    
    id_usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incidencias_reportadas')
    id_espacio = models.ForeignKey(Espacio, on_delete=models.SET_NULL, null=True, blank=True)
    id_equipo = models.ForeignKey(Equipamiento, on_delete=models.SET_NULL, null=True, blank=True)
    descripcion = models.TextField()
    prioridad = models.CharField(max_length=50, choices=PRIORIDAD_CHOICES, default='Media')
    estado = models.CharField(max_length=50, choices=ESTADO_CHOICES, default='Reportada')
    fecha_reporte = models.DateTimeField(auto_now_add=True)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    acciones_tomadas = models.TextField(blank=True, null=True)
    responsable = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='incidencias_asignadas')
    observaciones = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Incidencia {self.id} - {self.descripcion[:50]}"