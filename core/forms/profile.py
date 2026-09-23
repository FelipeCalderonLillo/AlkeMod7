from django import forms
from django.contrib.auth.models import User

from core.services.profile import ProfileService





class ProfileForm(forms.Form):
    username = forms.CharField(max_length=50, label="Usuario")
    trabajo = forms.CharField(max_length=100, required=False, label="Trabajo")
    biografia = forms.CharField(max_length=500, required=False, widget=forms.Textarea, label="Biografía")
    
    def __init__(self, *args, usuario, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario = usuario
        
    def clean_username(self):
        username = (self.cleaned_data["username"].strip().capitalize())
        
        if User.objects.filter(username__iexact=username).exclude(pk=self.usuario.pk).exists():
            raise forms.ValidationError("Ya existe un usuario con ese nombre de usuario.")
        
        return username
    
    def clean_trabajo(self):
        return self.cleaned_data["trabajo"].strip()
    
    def clean_biografia(self):
        return self.cleaned_data["biografia"].strip()