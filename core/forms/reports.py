from django import forms



class ReportForm(forms.Form):
    fecha_inicio = forms.DateField(
        required=False,
        label="Fecha de inicio",
        widget=forms.DateInput(
            attrs={"type": "date"}
        ),
    )
    fecha_fin = forms.DateField(
        required=False,
        label="Fecha de término",
        widget=forms.DateInput(
            attrs={"type": "date"}
        ),
    )
    
    def clean(self):
        cleaned_data = super().clean()
        
        fecha_inicio = cleaned_data.get("fecha_inicio")
        fecha_fin = cleaned_data.get("fecha_fin")
        
        if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
            raise forms.ValidationError("La fecha de inicio no puede ser posterior a la fecha de término.")
        
        return cleaned_data