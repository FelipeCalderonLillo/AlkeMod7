from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import TemplateView

from core.forms.registration import RegistrationForm
from core.services.registration import RegistrationService



class RegistrationView(View):
    template_name = 'auth/registro.html'
    
    def get(self, request):
        form = RegistrationForm()
        
        return render(request, self.template_name, {"form": form})
    
    def post(self, request):
        form = RegistrationForm(request.POST)
        
        if not form.is_valid():
            return render(request, self.template_name, {"form":form})
        
        try:
            datos = form.cleaned_data.copy()
            datos.pop("confirmar_password")
            
            RegistrationService.registrar_usuario(**datos)
        except ValueError as error:
            form.add_error(None, str(error))
            
            return render(request, self.template_name, {"form": form})
        
        messages.success(request, "Registro completado correctamente. Ya puedes iniciar sesión.")
        
        return redirect("login")
    
    
class HomeView(TemplateView):
    template_name = "home/home.html"