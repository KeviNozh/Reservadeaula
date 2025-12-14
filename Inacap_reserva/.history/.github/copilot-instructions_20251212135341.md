<!-- Instrucciones para agentes AI que contribuyen código en este repositorio -->
# Copilot / AI agent instructions

Breve: este repositorio es una aplicación Django (app `reservas`) que gestiona reservas de espacios, notificaciones y roles de usuario. Las siguientes notas ayudan a entender la arquitectura, flujos críticos y convenciones específicas del proyecto para ser productivo rápidamente.

- **Arquitectura (big picture):** aplicación Django monolítica con una app principal `reservas` y configuración en `project_core`.
  - La app expone páginas servidor-rendered (templates en reservas/templates) y una API REST bajo `/api/` (router + vistas función en [reservas/urls.py](reservas/urls.py)).
  - Lógica de negocio centralizada en `reservas/services.py` (servicios de notificaciones) y modelos en [reservas/models.py](reservas/models.py).

- **Puntos de integración clave:**
  - Autenticación: backend personalizado en [reservas/backends.py](reservas/backends.py) (EmailBackend) — las autenticaciones pueden usar email o username.
  - Notificaciones: usar `NotificacionService` y `NotificacionAdminService` en [reservas/services.py](reservas/services.py) en vez de duplicar lógica.
  - Vistas que sirven templates y endpoints API coexisten en [reservas/views.py](reservas/views.py); muchas APIs usan `@csrf_exempt` y `print()` para debug.

- **Patrones y convenciones del proyecto:**
  - Roles y permisos: el modelo `PerfilUsuario` (ver [reservas/models.py](reservas/models.py)) determina redirecciones y permisos (ej.: roles `Administrativo`, `Investigacion`, `Aprobador` son tratados como admin). Evitar cambiar el enum de roles sin migraciones.
  - Serializadores: los `Serializer` del API están en [reservas/serializers.py](reservas/serializers.py). Cuando añadas campos a modelos, actualiza los serializers correspondientemente.
  - Evitar duplicados: hay comprobaciones explícitas para evitar notificaciones duplicadas (ver `notificar_*` en services/views).

- **Flujos y comandos de desarrollo (Windows):**
  - Activar entorno virtual PowerShell: `venv_reservas\Scripts\Activate.ps1` (o `venv_reservas\Scripts\activate.bat` para cmd).
  - Instalar dependencias: `python -m pip install -r requirements.txt`.
  - Migraciones / DB: este proyecto usa PostgreSQL por defecto (conf. en [project_core/settings.py](project_core/settings.py)). Comandos típicos:
    - `python manage.py migrate`
    - `python manage.py createsuperuser`
    - `python manage.py runserver`
  - Nota: las credenciales de ejemplo (DB) están en `project_core/settings.py`; no las comites en producción — prefiera variables de entorno.

- **Rutas y API importantes (ejemplos):**
  - Páginas: `/login/`, `/dashboard/`, `/reservas/`, `/crear-reserva/` están en [reservas/urls.py](reservas/urls.py).
  - API REST principales: `/api/reservas/`, `/api/espacios/`, `/api/notificaciones/`. Muchas funciones auxiliares aparecen con rutas `api/...` en el mismo archivo.

- **Prácticas observables (seguirlas):**
  - Logging simple: el proyecto usa `print()` extensamente para debug en producción-local; si añades logs use el mismo estilo o migrar progresivamente a `logging` centralizado.
  - Manejo de errores: vistas usan try/except y retornan JSON con clave `success` y mensajes; mantén esa forma en nuevas APIs.

- **Qué priorizar al editar código:**
  - Reutilizar `NotificacionService` / `NotificacionAdminService` para notificaciones.
  - Respetar el flujo de `PerfilUsuario` para autorización (ej.: `is_admin_user` y comprobaciones en `dashboard_view`).
  - Mantener compatibilidad con los templates bajo `reservas/templates` (no renombrar variables usadas por templates sin actualizar las vistas).

- **Dónde buscar ejemplos concretos:**
  - Autenticación: [reservas/backends.py](reservas/backends.py)
  - Registro y login: [reservas/views.py](reservas/views.py) (funciones `registro_usuario` y `login_view`).
  - Notificaciones: [reservas/services.py](reservas/services.py) y funciones `notificar_accion_admin` en [reservas/views.py](reservas/views.py).

- **Limitaciones y riesgos detectados:**
  - `DEBUG = True` y credenciales Postgres en [project_core/settings.py](project_core/settings.py) — no seguro para producción.
  - `@csrf_exempt` en endpoints críticos; revisar CSRF si se exponen públicamente.

Si quieres, aplico cambios automáticos (p. ej. mover secrets a variables de entorno, convertir prints a `logging`, o añadir tests básicos). ¿Qué parte quieres que afine primero?
