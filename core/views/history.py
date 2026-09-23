from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views.generic import ListView

from core.models import Transaccion




class HistoryView(LoginRequiredMixin, ListView):
    template_name = "history/history.html"
    context_object_name = "transacciones"
    
    def get_queryset(self):
        cuenta = self.request.user.cuenta
        
        return(
            Transaccion.objects.filter(
                Q(cuenta_origen=cuenta) |
                Q(cuenta_destino=cuenta)
            ).order_by("-fecha_hora")
        )