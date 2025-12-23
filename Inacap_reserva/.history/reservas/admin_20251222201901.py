from django.contrib import admin
from .models import Elemento, ElementoReserva, Area, PerfilUsuario, Equipamiento, Espacio, Reserva, HistorialAprobacion, Notificacion, Mantenimiento, HorariosDisponibilidad, Incidencia

@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ['nombre_area', 'descripcion']
    search_fields = ['nombre_area']

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ['user', 'rol', 'departamento', 'estado', 'fecha_registro']
    list_filter = ['rol', 'estado']
    search_fields = ['user__username', 'user__email', 'departamento']

@admin.register(Equipamiento)
class EquipamientoAdmin(admin.ModelAdmin):
    list_display = ['nombre_equipo', 'tipo_equipo', 'id_espacio', 'marca_modelo']
    list_filter = ['tipo_equipo']
    search_fields = ['nombre_equipo', 'marca_modelo']

@admin.register(Espacio)
class EspacioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'edificio', 'piso', 'capacidad', 'estado']
    list_filter = ['tipo', 'estado', 'edificio']
    search_fields = ['nombre', 'edificio']

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ['espacio', 'solicitante', 'fecha_reserva', 'hora_inicio', 'hora_fin', 'estado']
    list_filter = ['estado', 'fecha_reserva']
    search_fields = ['espacio__nombre', 'solicitante__username']
    date_hierarchy = 'fecha_reserva'

@admin.register(HistorialAprobacion)
class HistorialAprobacionAdmin(admin.ModelAdmin):
    list_display = ['reserva', 'usuario_admin', 'tipo_accion', 'fecha_accion']
    list_filter = ['tipo_accion', 'fecha_accion']
    search_fields = ['reserva__espacio__nombre', 'usuario_admin__username']

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ['destinatario', 'tipo', 'titulo', 'leida', 'fecha_creacion']
    list_filter = ['tipo', 'leida']
    search_fields = ['titulo', 'destinatario__username']

@admin.register(Mantenimiento)
class MantenimientoAdmin(admin.ModelAdmin):
    list_display = ['id_espacio', 'tipo_mantenimiento', 'fecha_inicio', 'fecha_fin', 'estado']
    list_filter = ['tipo_mantenimiento', 'estado']
    search_fields = ['id_espacio__nombre']

@admin.register(HorariosDisponibilidad)
class HorariosDisponibilidadAdmin(admin.ModelAdmin):
    list_display = ['id_espacio', 'dia_semana', 'hora_apertura', 'hora_cierre']
    list_filter = ['dia_semana']
    search_fields = ['id_espacio__nombre']

@admin.register(Incidencia)
class IncidenciaAdmin(admin.ModelAdmin):
    list_display = ['id_usuario', 'prioridad', 'estado', 'fecha_reporte']
    list_filter = ['prioridad', 'estado']
    search_fields = ['descripcion', 'id_usuario__username']
    
@admin.register(Elemento)
class ElementoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria', 'cantidad_disponible', 'cantidad_total', 'estado', 'ubicacion']
    list_filter = ['categoria', 'estado', 'creado_en']
    search_fields = ['nombre', 'descripcion', 'codigo_patrimonial', 'marca', 'modelo']
    readonly_fields = ['creado_en', 'actualizado_en']
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'descripcion', 'categoria', 'codigo_patrimonial')
        }),
        ('Especificaciones', {
            'fields': ('marca', 'modelo', 'serie', 'imagen')
        }),
        ('Inventario', {
            'fields': ('cantidad_total', 'cantidad_disponible', 'estado', 'ubicacion')
        }),
        ('Información Adicional', {
            'fields': ('fecha_adquisicion', 'valor', 'observaciones')
        }),
        ('Auditoría', {
            'fields': ('creado_en', 'actualizado_en'),
            'classes': ('collapse',)
        }),
    )
    actions = ['marcar_como_disponible', 'marcar_como_mantenimiento']
    
    def marcar_como_disponible(self, request, queryset):
        updated = queryset.update(estado='disponible')
        self.message_user(request, f'{updated} elementos marcados como disponibles.')
    
    def marcar_como_mantenimiento(self, request, queryset):
        updated = queryset.update(estado='mantenimiento')
        self.message_user(request, f'{updated} elementos enviados a mantenimiento.')

@admin.register(ElementoReserva)
class ElementoReservaAdmin(admin.ModelAdmin):
    list_display = ['reserva', 'elemento', 'cantidad', 'prestado', 'devuelto', 'fecha_prestamo']
    list_filter = ['prestado', 'devuelto', 'fecha_prestamo']
    search_fields = ['reserva__id', 'elemento__nombre']
    readonly_fields = ['creado_en']