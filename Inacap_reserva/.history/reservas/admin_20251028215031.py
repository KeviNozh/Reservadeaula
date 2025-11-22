from django.contrib import admin
from .models import Area, PerfilUsuario, Equipamiento, Espacio, Reserva, HistorialAprobacion, Notificacion

admin.site.register(Area)
admin.site.register(PerfilUsuario)
admin.site.register(Equipamiento)
admin.site.register(Espacio)
admin.site.register(Reserva)
admin.site.register(HistorialAprobacion)
admin.site.register(Notificacion)