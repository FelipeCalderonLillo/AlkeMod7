from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views.generic import TemplateView

from core.models import Transaccion

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        cuenta = self.request.user.cuenta
        
        transacciones = (
            Transaccion.objects.filter(
                Q(cuenta_origen = cuenta)| 
                Q(cuenta_destino=cuenta))
        ).order_by("-fecha_hora")[:3]
        
        context["cuenta"] = cuenta
        context["transacciones"] = transacciones
        
        return context