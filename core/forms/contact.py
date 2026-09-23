from django import forms

from core.models import Contacto




class ContactForm(forms.ModelForm):
    class Meta:
        model = Contacto
        fields = ("nombre", "apellido", "banco")
        labels = {
            "nombre": "Nombre",
            "apellido": "Apellido",
            "banco": "Banco",
        }
        
    def clean_nombre(self):
            return self.cleaned_data["nombre"].strip().title()
        
    def clean_apellido(self):
            return self.cleaned_data["apellido"].strip().title()
    
    def clean_banco(self):
        return self.cleaned_data["banco"].strip()
    
    def clean_numero_cuenta(self):
        return self.cleaned_data["numero_cuenta"].strip()