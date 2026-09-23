from decimal import Decimal

from django import forms

from core.models import Contacto, Cuenta, TransferenciaPendiente




class TransferForm(forms.Form):
    tipo = forms.ChoiceField(choices=TransferenciaPendiente.Tipo.choices, label="Tipo de transferencia")
    monto = forms.DecimalField(
        min_value=Decimal("1000.00"),
        max_digits=12,
        decimal_places=2,
        label="Monto",
        widget=forms.NumberInput(
            attrs={
                "min": "1000",
                "step": "1",
            }
        ),
    )
    cuenta_destino = forms.ModelChoiceField(
        queryset=Cuenta.objects.none(),
        required=False,
        label="Cuenta de destino",
    )
    contacto = forms.ModelChoiceField(
        queryset=Contacto.objects.none(),
        required=False,
        label="Contacto",
    )
    
    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.usuario = usuario
        
        if usuario is not None:
            self.fields["cuenta_destino"].queryset = (
                Cuenta.objects.filter(usuario__is_active=True)
                .exclude(usuario=usuario)
                .select_related("usuario")
                .order_by("usuario__last_name", "usuario__first_name")
            )
            
            self.fields["contacto"].queryset = (
                Contacto.objects.filter(usuario=usuario).order_by("apellido", "nombre")
            )

    def clean_monto(self):
        monto = self.cleaned_data["monto"]
        
        if monto != monto.to_integral_value():
            raise forms.ValidationError("El monto debe ser un número entero, sin decimales.")
        
        if monto < Decimal("1000.00"):
            raise forms.ValidationError("El monto mínimo de transferencia es $1000.")
        
        return monto
    
    def clean(self):
        cleaned_data = super().clean()
        
        tipo = cleaned_data.get("tipo")
        cuenta_destino = cleaned_data.get("cuenta_destino")
        contacto = cleaned_data.get("contacto")
        
        if tipo == TransferenciaPendiente.Tipo.INTERNA:
            if cuenta_destino is None:
                self.add_error(
                    "cuenta_destino",
                    "Debes seleccionar una cuenta de destino",
                )
                
            if contacto is not None:
                self.add_error(
                    "contacto",
                    "Una transferencia interna no utiliza un contacto."
                )
                
        elif tipo == TransferenciaPendiente.Tipo.EXTERNA:
            if contacto is None:
                self.add_error(
                    "contacto",
                    "Debes seleccionar un contacto."
                )
                
            if cuenta_destino is not None:
                self.add_error(
                    "cuenta_destino",
                    "Una transferencia externa no utiliza cuenta de destino"
                )
                
        return cleaned_data