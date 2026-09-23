from django import forms 
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

class ActiveUserAuthenticationForm(AuthenticationForm):
    def clean(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")
        
        if username and password:
            User = get_user_model()
            
            try:
                usuario = User.objects.get(
                    username__iexact=username
                )
            except User.DoesNotExist:
                usuario = None
                
            if (
                usuario is not None
                and not usuario.is_active
                and usuario.check_password(password)
            ):
                raise ValidationError(
                    "Tu cuenta está inactiva. "
                    "Contacta a la administración para solicitar su reactivación."
                )
                
        return super().clean()