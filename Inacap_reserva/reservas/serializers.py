from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Espacio, Reserva, PerfilUsuario, Equipamiento, Area, Notificacion, HistorialAprobacion

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']

class PerfilUsuarioSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    area_nombre = serializers.CharField(source='area.nombre_area', read_only=True)
    class Meta:
        model = PerfilUsuario
        fields = ['id', 'user', 'rol', 'area', 'area_nombre']

class EquipamientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipamiento
        fields = '__all__'

class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = '__all__'

class EspacioSerializer(serializers.ModelSerializer):
    equipamiento = EquipamientoSerializer(many=True, read_only=True)
    class Meta:
        model = Espacio
        fields = ['id', 'nombre', 'tipo', 'capacidad', 'descripcion', 'estado', 'equipamiento']

class ReservaSerializer(serializers.ModelSerializer):
    espacio_nombre = serializers.CharField(source='espacio.nombre', read_only=True)
    solicitante_nombre = serializers.CharField(source='solicitante.username', read_only=True)
    class Meta:
        model = Reserva
        fields = [
            'id', 'espacio', 'espacio_nombre', 'solicitante', 'solicitante_nombre',
            'fecha_reserva', 'hora_inicio', 'hora_fin', 'proposito',
            'num_asistentes', 'estado', 'fecha_solicitud'
        ]

class NotificacionSerializer(serializers.ModelSerializer):
    espacio_nombre = serializers.CharField(source='reserva.espacio.nombre', read_only=True, allow_null=True)
    fecha_creacion_formateada = serializers.CharField(source='get_fecha_creacion_formateada', read_only=True)
    
    class Meta:
        model = Notificacion
        fields = [
            'id', 'tipo', 'titulo', 'mensaje', 'leida', 'fecha_creacion', 
            'fecha_creacion_formateada', 'reserva', 'espacio_nombre'
        ]
        read_only_fields = ['fecha_creacion']

class HistorialAprobacionSerializer(serializers.ModelSerializer):
    admin_nombre = serializers.CharField(source='usuario_admin.username', read_only=True)
    class Meta:
        model = HistorialAprobacion
        fields = '__all__'