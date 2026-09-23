from django import forms

from core.models import CategoriaInteres




class InterestForm(forms.Form):
    categoria = forms.ModelChoiceField(
        queryset=CategoriaInteres.objects.all().order_by("nombre"),
        empty_label=None,
        label="Categoría de interés",
    )