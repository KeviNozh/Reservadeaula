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
                
                print(f"🔧 [Middleware Tema] Procesando: {request.path}")
                
                # Solo procesar si NO es una API
                if not request.path.startswith('/api/'):
                    modified = False
                    
                    # ===== 1. INYECTAR CSS DEL TEMA =====
                    if 'id="darkCss"' not in body:
                        insert_css = '''
                        <!-- Tema oscuro para sistema de reservas -->
                        <link id="darkCss" rel="stylesheet" href="/static/css/dark.css">
                        
                        <!-- Estilos override para tema oscuro -->
                        <style>
                        .dark-theme {
                            --bg-primary: #121212 !important;
                            --bg-secondary: #1e1e1e !important;
                            --bg-tertiary: #2d2d2d !important;
                            --text-primary: #ffffff !important;
                            --text-secondary: #b0b0b0 !important;
                            --border-color: #444444 !important;
                            --accent-color: #2563eb !important;
                        }
                        
                        .dark-theme body {
                            background: var(--bg-primary) !important;
                            color: var(--text-primary) !important;
                        }
                        
                        .dark-theme .header {
                            background-color: var(--bg-secondary) !important;
                            border-bottom-color: var(--border-color) !important;
                        }
                        
                        .dark-theme .page-header,
                        .dark-theme .filters-section,
                        .dark-theme .calendar-section,
                        .dark-theme .sidebar {
                            background-color: var(--bg-secondary) !important;
                            border-color: var(--border-color) !important;
                        }
                        
                        .dark-theme table,
                        .dark-theme table th,
                        .dark-theme table td {
                            background-color: var(--bg-secondary) !important;
                            color: var(--text-primary) !important;
                            border-color: var(--border-color) !important;
                        }
                        
                        .dark-theme .nav-item {
                            color: var(--text-secondary) !important;
                        }
                        
                        .dark-theme .nav-item:hover,
                        .dark-theme .nav-item.active {
                            background-color: var(--accent-color) !important;
                            color: white !important;
                        }
                        </style>
                        '''
                        
                        if '</head>' in body:
                            body = body.replace('</head>', insert_css + '\n</head>')
                            modified = True
                            print(f"✅ CSS inyectado en: {request.path}")
                    
                    # ===== 2. INYECTAR SCRIPT theme.js =====
                    if 'theme.js' not in body:
                        insert_script = '<script src="/static/js/theme.js"></script>'
                        if '</body>' in body:
                            body = body.replace('</body>', insert_script + '\n</body>')
                            modified = True
                            print(f"✅ theme.js inyectado en: {request.path}")
                    
                    # ===== 3. INYECTAR BOTÓN DE TEMA SI NO EXISTE =====
                    if 'themeToggle' not in body and 'id="themeToggle"' not in body:
                        theme_button = '''
                        <!-- Botón de cambio de tema -->
                        <button class="theme-toggle-btn" id="themeToggle" style="
                            position: fixed;
                            top: 80px;
                            right: 20px;
                            background: #2563eb;
                            color: white;
                            border: none;
                            border-radius: 50%;
                            width: 50px;
                            height: 50px;
                            font-size: 20px;
                            cursor: pointer;
                            z-index: 1000;
                            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                            display: flex;
                            align-items: center;
                            justify-content: center;
                        ">
                            🌙
                        </button>
                        
                        <script>
                        // Script inmediato para manejar el tema
                        document.addEventListener('DOMContentLoaded', function() {
                            const themeToggle = document.getElementById('themeToggle');
                            const savedTheme = localStorage.getItem('theme') || 'light';
                            
                            // Aplicar tema guardado
                            if (savedTheme === 'dark') {
                                document.body.classList.add('dark-theme');
                                document.documentElement.setAttribute('data-theme', 'dark');
                                themeToggle.textContent = '☀️';
                            } else {
                                document.body.classList.remove('dark-theme');
                                document.documentElement.setAttribute('data-theme', 'light');
                                themeToggle.textContent = '🌙';
                            }
                            
                            // Manejar clic
                            themeToggle.addEventListener('click', function() {
                                const isDark = document.body.classList.contains('dark-theme');
                                
                                if (isDark) {
                                    document.body.classList.remove('dark-theme');
                                    document.documentElement.setAttribute('data-theme', 'light');
                                    localStorage.setItem('theme', 'light');
                                    this.textContent = '🌙';
                                } else {
                                    document.body.classList.add('dark-theme');
                                    document.documentElement.setAttribute('data-theme', 'dark');
                                    localStorage.setItem('theme', 'dark');
                                    this.textContent = '☀️';
                                }
                            });
                        });
                        </script>
                        '''
                        
                        if '</body>' in body:
                            body = body.replace('</body>', theme_button + '\n</body>')
                            modified = True
                            print(f"✅ Botón de tema inyectado en: {request.path}")
                    
                    if modified:
                        response.content = body.encode(charset)
                        if response.get('Content-Length'):
                            response['Content-Length'] = len(response.content)
                            
        except Exception as e:
            print(f"❌ Error en middleware: {e}")
            import traceback
            traceback.print_exc()

        return response