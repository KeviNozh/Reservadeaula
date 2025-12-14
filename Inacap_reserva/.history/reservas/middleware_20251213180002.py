from django.conf import settings

class InjectThemeMiddleware:
    """Middleware que inyecta el link al CSS oscuro y el script `theme.js`
    en todas las respuestas HTML si no están presentes. Útil para asegurar
    cobertura global sin editar cada plantilla.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print("🔧 [Middleware de Tema] Se está ejecutando para:", request.path)
        response = self.get_response(request)

        try:
            content_type = response.get('Content-Type', '')
            if response.status_code == 200 and 'text/html' in content_type:
                # decodificar con el charset de la respuesta o utf-8
                charset = getattr(response, 'charset', 'utf-8') or 'utf-8'
                body = response.content.decode(charset)

                modified = False
                
                # 🔧 NUEVO: Definir si es Django Admin real o tus páginas admin
                is_django_admin_real = request.path.startswith('/admin/') and not any(
                    admin_path in request.path for admin_path in [
                        'admin-dashboard', 
                        'solicitudes-pendientes', 
                        'gestion-espacios', 
                        'gestion-usuarios',
                        'crear-usuario',
                        'editar-usuario',
                        'notificaciones-admin',
                        'reportes',
                        'revisar-solicitud'
                    ]
                )
                
                is_your_admin_page = any(
                    admin_path in request.path for admin_path in [
                        'admin-dashboard', 
                        'solicitudes-pendientes', 
                        'gestion-espacios', 
                        'gestion-usuarios',
                        'crear-usuario',
                        'editar-usuario',
                        'notificaciones-admin',
                        'reportes',
                        'revisar-solicitud'
                    ]
                )

                # Si es admin, inyecta dark_admin.css, si no, dark.css
                if 'id="darkCss"' not in body:
                    if is_django_admin_real:
                        # Django Admin Panel real
                        insert_link = f'<link id="darkCss" rel="stylesheet" href="{settings.STATIC_URL}css/dark_admin.css">'
                    else:
                        # Tus páginas normales Y tus páginas admin personalizadas
                        insert_link = f'<link id="darkCss" rel="stylesheet" href="{settings.STATIC_URL}css/dark.css" disabled>'
                    
                    # Inline high-priority overrides inserted after page styles so they win over template CSS
                    insert_style = '''<style id="dark_overrides">html[data-theme="dark"], body.dark-theme { background-color: #071126 !important; color: #e6eef8 !important; } html[data-theme="dark"] .card, body.dark-theme .card, html[data-theme="dark"] .login-container, body.dark-theme .login-container, html[data-theme="dark"] .card-body, body.dark-theme .card-body { background-color: #0f172a !important; color: #e6eef8 !important; border-color: rgba(255,255,255,0.03) !important; } html[data-theme="dark"] table th, body.dark-theme table th, html[data-theme="dark"] table td, body.dark-theme table td { color: #cbd5e1 !important; border-color: rgba(255,255,255,0.03) !important; } </style>'''
                    insert_chunk = insert_link + '\n' + insert_style
                    if '</head>' in body:
                        body = body.replace('</head>', insert_chunk + '\n</head>')
                        modified = True

                # 🔧 MODIFICADO: Insertar script theme.js para TODAS las páginas excepto Django Admin real
                if not is_django_admin_real and 'theme.js' not in body:
                    insert_script = f'<script src="{settings.STATIC_URL}js/theme.js"></script>'
                    if '</body>' in body:
                        body = body.replace('</body>', insert_script + '\n</body>')
                        modified = True

                # 🔧 MODIFICADO: Forzar data-theme=dark solo en Django Admin real
                if is_django_admin_real:
                    force_theme_script = '''<script>(function(){try{if(localStorage.getItem('theme')==='dark'){document.documentElement.setAttribute('data-theme','dark');}}catch(e){}})();</script>'''
                    if '</head>' in body and 'data-theme' not in body:
                        body = body.replace('</head>', force_theme_script + '\n</head>')
                        modified = True
                
                # 🔧 NUEVO: Para tus páginas admin, asegurar que también tengan el atributo data-theme
                if is_your_admin_page and 'data-theme' not in body:
                    force_theme_script_your_admin = '''<script>(function(){try{if(localStorage.getItem('theme')==='dark'){document.documentElement.setAttribute('data-theme','dark');document.body.classList.add('dark-theme');}}catch(e){}})();</script>'''
                    if '</head>' in body:
                        body = body.replace('</head>', force_theme_script_your_admin + '\n</head>')
                        modified = True

                # insertar un bloque de overrides al final del body para ganar sobre estilos inline en body
                if 'id="dark_overrides_body"' not in body:
                    # Este bloque incluye una regla final muy agresiva que fuerza fondos oscuros
                    # en casi todos los elementos (excluye imágenes y vídeos) para convertir
                    # cualquier fondo blanco a oscuro sin tocar el color del texto.
                    body_overrides = '''<style id="dark_overrides_body">html[data-theme="dark"], body.dark-theme { background-color:#071126 !important; color:#e6eef8 !important; } html[data-theme="dark"] [class*="card"], body.dark-theme [class*="card"], html[data-theme="dark"] [class*="panel"], body.dark-theme [class*="panel"], html[data-theme="dark"] [class*="white"], body.dark-theme [class*="white"], html[data-theme="dark"] [style*="#fff"], body.dark-theme [style*="#fff"], html[data-theme="dark"] [style*="background: white"], body.dark-theme [style*="background: white"], html[data-theme="dark"] table td, body.dark-theme table td { background-color: #0f172a !important; color: #e6eef8 !important; border-color: rgba(255,255,255,0.03) !important; }</style>'''
                    if '</body>' in body:
                        body = body.replace('</body>', body_overrides + '\n</body>')
                        modified = True

                if modified:
                    response.content = body.encode(charset)
                    if response.get('Content-Length'):
                        response['Content-Length'] = len(response.content)
                        
                # 🔧 DEBUG: Agregar log para ver qué está pasando
                print(f"🔧 [Middleware Debug] Ruta: {request.path}")
                print(f"🔧 [Middleware Debug] Es Django Admin real: {is_django_admin_real}")
                print(f"🔧 [Middleware Debug] Es tu página admin: {is_your_admin_page}")
                print(f"🔧 [Middleware Debug] Modificado: {modified}")
                        
        except Exception as e:
            print(f"❌ Error en middleware de tema: {e}")
            # no romper la respuesta si ocurre algo; solo loguear si es necesario

        return response