from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

UserModel = get_user_model()

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            print(f"🔐 Intentando autenticar: {username}")
            
            # Buscar por email o username (case insensitive)
            user = UserModel.objects.get(
                Q(email__iexact=username) | 
                Q(username__iexact=username)
            )
            print(f"✅ Usuario encontrado: {user.username}")
            
        except UserModel.DoesNotExist:
            print(f"❌ Usuario no encontrado: {username}")
            return None
        except UserModel.MultipleObjectsReturned:
            user = UserModel.objects.filter(
                Q(email__iexact=username) | 
                Q(username__iexact=username)
            ).first()
            print(f"⚠️ Múltiples usuarios, usando: {user.username}")

        # Verificar contraseña
        if user and user.check_password(password):
            print(f"✅ Contraseña correcta para: {user.username}")
            return user
        else:
            print(f"❌ Contraseña incorrecta para: {username}")
            return None

    def get_user(self, user_id):
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None