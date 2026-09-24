from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views import View

from core.forms.contact import ContactForm
from core.models import Contacto
from core.services.contacts import ContactService



class ContactView(LoginRequiredMixin, View):
    template_name = "contacts/contacts.html"
    form_class = ContactForm
    
    def get(self, request):
        form = ContactForm()
        contactos = ContactService.obtener_contactos(
            usuario=request.user
        )
        
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "contactos": contactos,
            },
        )
        
    def post(self, request):
        form = ContactForm(request.POST)
        
        if not form.is_valid():
            contactos = ContactService.obtener_contactos(
                usuario=request.user
            )
            
            return render(
                request,
                self.template_name,
                {
                    "form": form,
                    "contactos": contactos,
                },
            )
            
        ContactService.crear_contacto(
            usuario=request.user,
            **form.cleaned_data,
        )
        
        messages.success(
            request,
            "Contacto creado correctamente."
        )
        
        return redirect("contacts")