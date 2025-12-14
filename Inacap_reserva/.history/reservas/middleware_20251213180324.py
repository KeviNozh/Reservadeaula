from django.conf import settings

class InjectThemeMiddleware:
    """Middleware que inyecta el sistema de tema oscuro en todas las páginas HTML."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        try:
            content_type = response.get('Content-Type', '')
            if response.status_code == 200 and 'text/html' in content_type:
                charset = getattr(response, 'charset', 'utf-8') or 'utf-8'
                body = response.content.decode(charset)

                # DEBUG: Ver qué página estamos procesando
                print(f"🔧 [Middleware Tema] Procesando: {request.path}")
                
                # 1. DEFINIR SI ES DJANGO ADMIN REAL
                # Django admin real siempre tiene "/admin/" en la URL exacta
                is_django_admin_real = request.path == '/admin/' or request.path.startswith('/admin/') and '/admin/' in request.path
                
                # 2. DEFINIR SI ES PÁGINA ADMIN TUYA
                # Tus páginas admin empiezan con "admin-" o tienen nombres específicos
                is_your_admin_page = any(keyword in request.path for keyword in [
                    'admin-dashboard',
                    'solicitudes-pendientes', 
                    'gestion-espacios',
                    'gestion-usuarios',
                    'notificaciones-admin',
                    'reportes',
                    'revisar-solicitud'
                ])
                
                print(f"🔧 [Middleware Tema] Django Admin Real: {is_django_admin_real}")
                print(f"🔧 [Middleware Tema] Tu Admin Page: {is_your_admin_page}")

                modified = False
                
                # ===== INYECTAR CSS DEL TEMA PARA TODAS LAS PÁGINAS =====
                if 'id="darkCss"' not in body:
                    # TODAS las páginas (excepto Django admin real) usan dark.css
                    if is_django_admin_real:
                        insert_link = f'<link id="darkCss" rel="stylesheet" href="{settings.STATIC_URL}css/dark_admin.css">'
                    else:
                        insert_link = f'<link id="darkCss" rel="stylesheet" href="{settings.STATIC_URL}css/dark.css">'
                    
                    # Estilos override importantes para tema oscuro
                    insert_style = '''<style id="dark_overrides">
                    html[data-theme="dark"], body.dark-theme { 
                        background-color: #071126 !important; 
                        color: #e6eef8 !important; 
                    }
                    html[data-theme="dark"] .header,
                    body.dark-theme .header {
                        background-color: #1e293b !important;
                        border-color: #334155 !important;
                    }
                    html[data-theme="dark"] .card,
                    body.dark-theme .card,
                    html[data-theme="dark"] .page-header,
                    body.dark-theme .page-header,
                    html[data-theme="dark"] .filters-section,
                    body.dark-theme .filters-section {
                        background-color: #1e293b !important;
                        color: #e6eef8 !important;
                        border-color: #334155 !important;
                    }
                    html[data-theme="dark"] table,
                    body.dark-theme table,
                    html[data-theme="dark"] table th,
                    body.dark-theme table th,
                    html[data-theme="dark"] table td,
                    body.dark-theme table td {
                        background-color: #1e293b !important;
                        color: #cbd5e1 !important;
                        border-color: #334155 !important;
                    }
                    html[data-theme="dark"] .btn,
                    body.dark-theme .btn {
                        background-color: #3b82f6 !important;
                        border-color: #3b82f6 !important;
                    }
                    </style>'''
                    
                    insert_chunk = insert_link + '\n' + insert_style
                    if '</head>' in body:
                        body = body.replace('</head>', insert_chunk + '\n</head>')
                        modified = True

                # ===== INYECTAR SCRIPT theme.js PARA PÁGINAS NO-DJANGO-ADMIN =====
                # Solo inyectar theme.js si NO es Django admin real Y no está ya presente
                if not is_django_admin_real and 'theme.js' not in body:
                    insert_script = f'<script src="{settings.STATIC_URL}js/theme.js"></script>'
                    if '</body>' in body:
                        body = body.replace('</body>', insert_script + '\n</body>')
                        modified = True
                        
                        print(f"🔧 [Middleware Tema] Inyectando theme.js en: {request.path}")

                # ===== INYECTAR SCRIPT PARA APLICAR TEMA DESDE localStorage =====
                # Para TODAS las páginas (excepto Django admin real)
                if not is_django_admin_real and 'localStorage.getItem' not in body:
                    force_theme_script = '''<script>
                    (function(){
                        try {
                            const theme = localStorage.getItem('theme') || 'light';
                            if(theme === 'dark') {
                                document.documentElement.setAttribute('data-theme', 'dark');
                                document.body.classList.add('dark-theme');
                            }
                        } catch(e) {
                            console.log('Error aplicando tema:', e);
                        }
                    })();
                    </script>'''
                    
                    if '</head>' in body:
                        body = body.replace('</head>', force_theme_script + '\n</head>')
                        modified = True

                if modified:
                    response.content = body.encode(charset)
                    if response.get('Content-Length'):
                        response['Content-Length'] = len(response.content)
                        
        except Exception as e:
            print(f"❌ Error en middleware de tema: {e}")
            import traceback
            traceback.print_exc()

        return response