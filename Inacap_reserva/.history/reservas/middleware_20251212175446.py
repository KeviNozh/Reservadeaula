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
                    if '</head>' in body:
                        body = body.replace('</head>', insert_link + '\n</head>')
                        modified = True

                # insertar script theme.js antes de </body> si no existe
                if 'theme.js' not in body:
                    insert_script = f'<script src="{settings.STATIC_URL}js/theme.js"></script>'
                    if '</body>' in body:
                        body = body.replace('</body>', insert_script + '\n</body>')
                        modified = True

                if modified:
                    response.content = body.encode(charset)
                    if response.get('Content-Length'):
                        response['Content-Length'] = len(response.content)
        except Exception:
            # no romper la respuesta si ocurre algo; solo loguear si es necesario
            pass

        return response
