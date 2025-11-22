from django.db import models
from django.contrib.auth.models import User

class Area(models.Model):
    nombre_area = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    def __str__(self):
        return self.nombre_area

class PerfilUsuario(models.Model):
    ROL_CHOICES = (('Usuario', 'Usuario'), ('Admin', 'Administrador'))
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rol = models.CharField(max_length=50, choices=ROL_CHOICES, default='Usuario')
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True)
    def __str__(self):
        return f"{self.user.username} ({self.rol})"

class Equipamiento(models.Model):
    nombre_equipo = models.CharField(max_length=100)
    tipo_equipo = models.CharField(max_length=100)
    def __str__(self):
        return self.nombre_equipo

class Espacio(models.Model):
    ESTADO_CHOICES = (
        ('Disponible', 'Disponible'),
        ('Mantenimiento', 'Mantenimiento'),
        ('Fuera de Servicio', 'Fuera de Servicio'),
    )
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=100)
    capacidad = models.IntegerField()
    descripcion = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=50, choices=ESTADO_CHOICES, default='Disponible')
    equipamiento = models.ManyToManyField(Equipamiento, blank=True)
    def __str__(self):
        return self.nombre

class Reserva(models.Model):
    ESTADO_CHOICES = (
        ('Pendiente', 'Pendiente'),
        ('Aprobada', 'Aprobada'),
        ('Rechazada', 'Rechazada'),
        ('Cancelada', 'Cancelada'),
    )
    espacio = models.ForeignKey(Espacio, on_delete=models.CASCADE)
    solicitante = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_reserva = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    proposito = models.TextField()
    num_asistentes = models.IntegerField()
    estado = models.CharField(max_length=50, choices=ESTADO_CHOICES, default='Pendiente')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Reserva de {self.espacio.nombre} por {self.solicitante.username}"

class HistorialAprobacion(models.Model):
    ACCION_CHOICES = (('Aprobada', 'Aprobada'), ('Rechazada', 'Rechazada'), ('Cancelada', 'Cancelada'))
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE)
    usuario_admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    tipo_accion = models.CharField(max_length=50, choices=ACCION_CHOICES)
    fecha_accion = models.DateTimeField(auto_now_add=True)
    motivo = models.TextField(blank=True, null=True)
    def __str__(self):
        return f"Acción {self.tipo_accion} en Reserva {self.reserva.id}"

class Notificacion(models.Model):
    destinatario = models.ForeignKey(User, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=255)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.titulo