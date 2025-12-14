from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

UserModel = get_user_model()

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            print(f"🔐 Intentando autenticar: {username}")
            
            # Buscar por email o username (case insensitive)
            # CORREGIDO: Usar get() para evitar múltiples resultados
            try:
                user = UserModel.objects.get(
                    Q(email__iexact=username) | 
                    Q(username__iexact=username)
                )
            except UserModel.MultipleObjectsReturned:
                # Si hay múltiples, tomar el primero que coincida con email exacto
                user = UserModel.objects.filter(email__iexact=username).first()
                if not user:
                    # Si no hay email exacto, tomar el primero
                    user = UserModel.objects.filter(
                        Q(email__iexact=username) | 
                        Q(username__iexact=username)
                    ).first()
                print(f"⚠️ Múltiples usuarios encontrados, usando: {user.username}")
            
            print(f"✅ Usuario encontrado: {user.username}")
            
            # Verificar contraseña
            if user and user.check_password(password):
                if not user.is_active:
                    print(f"⚠️ Usuario {user.username} está inactivo")
                    return None
                    
                print(f"✅ Contraseña correcta para: {user.username}")
                return user
            else:
                print(f"❌ Contraseña incorrecta para: {username}")
                return None
                
        except UserModel.DoesNotExist:
            print(f"❌ Usuario no encontrado: {username}")
            return None
        except Exception as e:
            print(f"❌ Error en autenticación: {e}")
            return None

    def get_user(self, user_id):
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None