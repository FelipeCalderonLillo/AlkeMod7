from decimal import Decimal

from django import forms 

class DepositForm(forms.Form):
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
    
    def clean(self):
        monto = self.cleaned_data["monto"]
        
        if monto != monto.to_integral_value():
            raise forms.ValidationError("El monto debe ser un número entero, sin decimales.")
        
        if monto < Decimal("1000.00"):
            raise forms.ValidationError("El monto mínimo de depósito es $1.000.")
        
        return monto
    
    