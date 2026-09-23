from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import FormView

from core.forms.profile import ProfileForm
from core.services.profile import ProfileService


class ProfileView(LoginRequiredMixin, FormView):
    template_name = "profile/profile.html"
    form_class = ProfileForm
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["usuario"] = self.request.user
        return kwargs
    
    def get_initial(self):
        initial = super().get_initial()
        
        initial.update({
            "username": self.request.user.username,
            "trabajo": self.request.user.perfil.trabajo,
            "biografia": self.request.user.perfil.biografia,
        })
        return initial
    
    def form_valid(self, form):
        ProfileService.actualizar_perfil(
            usuario=self.request.user,
            **form.cleaned_data,
        )
        
        messages.success(self.request, "Perfil actualizado correctamente.")
        
        return redirect("profile")