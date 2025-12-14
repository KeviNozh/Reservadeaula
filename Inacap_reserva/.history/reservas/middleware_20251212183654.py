from django.conf import settings


class InjectThemeMiddleware:
    """Middleware que inyecta el link al CSS oscuro y el script `theme.js`
    en todas las respuestas HTML si no están presentes. Útil para asegurar
    cobertura global sin editar cada plantilla.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print("🔧 [Middleware de Tema] Se está ejecutando para:", request.path)  # <-- Agrega esta línea
        response = self.get_response(request)

        try:
            content_type = response.get('Content-Type', '')
            if response.status_code == 200 and 'text/html' in content_type:
                # decodificar con el charset de la respuesta o utf-8
                charset = getattr(response, 'charset', 'utf-8') or 'utf-8'
                body = response.content.decode(charset)

                modified = False

                # insertar link#darkCss antes de </head> si no existe
                if 'id="darkCss"' not in body:
                    insert_link = f'<link id="darkCss" rel="stylesheet" href="{settings.STATIC_URL}css/dark.css" disabled>'
                    # Inline high-priority overrides inserted after page styles so they win over template CSS
                    insert_style = '''<style id="dark_overrides">html[data-theme="dark"], body.dark-theme { background-color: #071126 !important; color: #e6eef8 !important; } html[data-theme="dark"] .card, body.dark-theme .card, html[data-theme="dark"] .login-container, body.dark-theme .login-container, html[data-theme="dark"] .card-body, body.dark-theme .card-body { background-color: #0f172a !important; color: #e6eef8 !important; border-color: rgba(255,255,255,0.03) !important; } html[data-theme="dark"] table th, body.dark-theme table th, html[data-theme="dark"] table td, body.dark-theme table td { color: #cbd5e1 !important; border-color: rgba(255,255,255,0.03) !important; } </style>'''
                    insert_chunk = insert_link + '\n' + insert_style
                    if '</head>' in body:
                        body = body.replace('</head>', insert_chunk + '\n</head>')
                        modified = True

                # insertar script theme.js antes de </body> si no existe
                if 'theme.js' not in body:
                    insert_script = f'<script src="{settings.STATIC_URL}js/theme.js"></script>'
                    if '</body>' in body:
                        body = body.replace('</body>', insert_script + '\n</body>')
                        modified = True

                # insertar un bloque de overrides al final del body para ganar sobre estilos inline en body
                if 'id="dark_overrides_body"' not in body:
                    # Este bloque incluye una regla final muy agresiva que fuerza fondos oscuros
                    # en casi todos los elementos (excluye imágenes y vídeos) para convertir
                    # cualquier fondo blanco a oscuro sin tocar el color del texto.
                    body_overrides = '''<style id="dark_overrides_body">html[data-theme="dark"], body.dark-theme { background-color:#071126 !important; color:#e6eef8 !important; } html[data-theme="dark"] [class*="card"], body.dark-theme [class*="card"], html[data-theme="dark"] [class*="panel"], body.dark-theme [class*="panel"], html[data-theme="dark"] [class*="white"], body.dark-theme [class*="white"], html[data-theme="dark"] [style*="#fff"], body.dark-theme [style*="#fff"], html[data-theme="dark"] [style*="background: white"], body.dark-theme [style*="background: white"], html[data-theme="dark"] table td, body.dark-theme table td { background-color: #0f172a !important; color: #e6eef8 !important; border-color: rgba(255,255,255,0.03) !important; } /* Regla final: forzar fondo oscuro en casi todos los elementos, excepto medios */ html[data-theme="dark"] *:not(img):not(svg):not(canvas):not(video):not(.no-force-dark) { background-color: #07070a !important; }</style>'''
                    if '</body>' in body:
                        body = body.replace('</body>', body_overrides + '\n</body>')
                        modified = True

                if modified:
                    response.content = body.encode(charset)
                    if response.get('Content-Length'):
                        response['Content-Length'] = len(response.content)
        except Exception:
            # no romper la respuesta si ocurre algo; solo loguear si es necesario
            pass

        return response
