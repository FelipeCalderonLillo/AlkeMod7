from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import FormView

from core.forms.interest import InterestForm
from core.services.interests import InterestService


class InterestView(LoginRequiredMixin, FormView):
    template_name = "interests/interests.html"
    form_class = InterestForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context["categorias"] = InterestService.obtener_categorias()
        context["categorias_suscritas"] = self.request.user.categorias_interes.all()
        
        return context
    
    def form_valid(self, form):
        categoria = form.cleaned_data["categoria"]
        accion = self.request.POST.get("accion")
        
        if accion == "suscribir":
            InterestService.suscribir_usuario(
                usuario=self.request.user,
                categoria=categoria,
            )
            
            messages.success(self.request, "Te has suscrito a la categoría correctamente.")
            
        elif accion == "desuscribir":
            InterestService.desuscribir_usuario(
                usuario=self.request.user,
                categoria=categoria,
            )
            
            messages.success(self.request, "Has cancelado la suscripción correctamente.")
            
        else:
            form.add_error(None, "La acción solicitada no es válida.")
            return self.form_invalid(form)
        
        return redirect("interests")