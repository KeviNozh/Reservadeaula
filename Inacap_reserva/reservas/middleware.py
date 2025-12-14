from django.conf import settings

class InjectThemeMiddleware:
    """Middleware que inyecta el sistema de tema oscuro en todas las páginas."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        try:
            content_type = response.get('Content-Type', '')
            if response.status_code == 200 and 'text/html' in content_type:
                charset = getattr(response, 'charset', 'utf-8') or 'utf-8'
                body = response.content.decode(charset)
                
                # DEBUG
                print(f"🔧 [Middleware Tema] Procesando: {request.path}")
                
                # Solo procesar páginas HTML (no APIs, no admin Django)
                if not request.path.startswith('/api/') and not request.path.startswith('/admin/'):
                    modified = False
                    
                    # ===== 1. INYECTAR CSS DEL TEMA SI NO EXISTE =====
                    if 'id="darkCss"' not in body and 'dark.css' not in body:
                        insert_css = f'''
                        <!-- Tema oscuro para sistema de reservas -->
                        <link id="darkCss" rel="stylesheet" href="{settings.STATIC_URL}css/dark.css">
                        '''
                        
                        if '</head>' in body:
                            body = body.replace('</head>', insert_css + '\n</head>')
                            modified = True
                            print(f"✅ CSS del tema inyectado en: {request.path}")
                    
                    # ===== 2. INYECTAR SCRIPT theme.js SI NO EXISTE =====
                    if 'theme.js' not in body and 'theme.js' not in body:
                        insert_script = f'<script src="{settings.STATIC_URL}js/theme.js"></script>'
                        
                        if '</body>' in body:
                            body = body.replace('</body>', insert_script + '\n</body>')
                            modified = True
                            print(f"✅ theme.js inyectado en: {request.path}")
                    
                    # ===== 3. INYECTAR SCRIPT INMEDIATO PARA APLICAR TEMA =====
                    if 'localStorage.getItem' not in body:
                        apply_theme_script = '''
                        <script>
                        // Aplicar tema inmediatamente al cargar
                        (function() {
                            try {
                                const savedTheme = localStorage.getItem('theme') || 'light';
                                const html = document.documentElement;
                                const body = document.body;
                                
                                if (savedTheme === 'dark') {
                                    html.setAttribute('data-theme', 'dark');
                                    body.classList.add('dark-theme');
                                    body.classList.remove('light-theme');
                                } else {
                                    html.setAttribute('data-theme', 'light');
                                    body.classList.remove('dark-theme');
                                    body.classList.add('light-theme');
                                }
                            } catch(e) {
                                console.log('Error aplicando tema:', e);
                            }
                        })();
                        </script>
                        '''
                        
                        if '</head>' in body:
                            body = body.replace('</head>', apply_theme_script + '\n</head>')
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