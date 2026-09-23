from django import forms
from django.contrib.auth.models import User

from core.services.registration import RegistrationService

class RegistrationForm(forms.Form):
    username = forms.CharField(max_length=50, label='Usuario')
    password = forms.CharField(min_length=8, widget=forms.PasswordInput, label='Contraseña')
    confirmar_password = forms.CharField(min_length=8, widget=forms.PasswordInput, label="Confirmar contraseña")
    first_name = forms.CharField(max_length=150, label='Nombre')
    last_name = forms.CharField(max_length=150, label='Apellido')
    email = forms.EmailField(label='Email')
    fecha_nacimiento = forms.DateField(label='Fecha de nacimiento', widget=forms.DateInput(attrs={'type':'date'}))
    
    def clean(self):
        cleaned_data = super().clean()
        
        password = cleaned_data.get("password")
        confirmar_password = cleaned_data.get("confirmar_password")
        
        if (
            password and confirmar_password
            and password != confirmar_password
        ):
            self.add_error(
                "confirmar_password",
                "Las contraseñas no coinciden.",
            )
    
    def clean_username(self):
        username = self.cleaned_data['username'].strip().capitalize()
        
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Ya existe un usuario con ese nombre de usuario.")
        
        return username
    
    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe un usuario registrado con ese e-mail.")
        
        return email
    
    def clean_first_name(self):
        return self.cleaned_data['first_name'].strip().title()
    
    def clean_last_name(self):
        return self.cleaned_data['last_name'].strip().title()
        
    def clean_fecha_nacimiento(self):
        fecha_nacimiento = self.cleaned_data['fecha_nacimiento']
        
        try:
            RegistrationService._validar_fecha_nacimiento(fecha_nacimiento)
        except ValueError as error:
            raise forms.ValidationError(str(error))
        
        return fecha_nacimiento
    