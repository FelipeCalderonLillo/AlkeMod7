from datetime import datetime, time, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import FormView

from core.forms.reports import ReportForm
from core.services.reports import ReportService



class ReportView(LoginRequiredMixin, FormView):
    template_name = "reports/reports.html"
    form_class = ReportForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        contexto_reporte = self._obtener_contexto_reporte(self.request.GET or None)
        
        context.update(contexto_reporte)
        
        return context
    
    def form_valid(self, form):
        fecha_inicio = form.cleaned_data.get("fecha_inicio")
        fecha_fin = form.cleaned_data.get("fecha_fin")
        
        params = {}
        
        if fecha_inicio:
            params["fecha_inicio"] = fecha_inicio.isoformat()
            
        if fecha_fin:
            params["fecha_fin"] = fecha_fin.isoformat()
            
        return redirect(f"{self.request.path}?{'&'.join(f'{clave}={valor}' for clave, valor in params.items())}")
    
    def _obtener_contexto_reporte(self, queryparams):
        fecha_inicio = None
        fecha_fin = None
        
        if queryparams:
            form = self.form_class(queryparams)
            
            if form.is_valid():
                fecha_inicio = form.cleaned_data.get("fecha_inicio")
                fecha_fin = form.cleaned_data.get("fecha_fin")
                
        if not fecha_inicio and not fecha_fin:
            fecha_fin = timezone.localdate()
            fecha_inicio = fecha_fin - timedelta(days=30)
            form = self.form_class(initial={
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
            })
        else:
            form = self.form_class(queryparams) if queryparams else self.form_class()
                
        fecha_inicio_datetime = self._convertir_inicio(fecha_inicio)
        fecha_fin_datetime = self._convertir_fin(fecha_fin)
        
        transacciones = ReportService.obtener_transacciones(
            usuario=self.request.user,
            fecha_inicio=fecha_inicio_datetime,
            fecha_fin=fecha_fin_datetime,
        )
        
        resumen = ReportService.obtener_resumen(
            usuario=self.request.user,
            fecha_inicio=fecha_inicio_datetime,
            fecha_fin=fecha_fin_datetime,
        )
        
        ingresos = resumen.get("ingresos", 0) or 0
        egresos = resumen.get("egresos", 0) or 0
        resumen["balance"] = ingresos - egresos
        
        return {
            "form": form,
            "transacciones": transacciones,
            "resumen": resumen,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
        }
        
    @staticmethod
    def _convertir_inicio(fecha):
        if fecha is None:
            return None
        
        fecha_datetime = datetime.combine(fecha, time.min)
        
        return timezone.make_aware(
            fecha_datetime,
            timezone.get_current_timezone(),
        )
        
    @staticmethod
    def _convertir_fin(fecha):
        if fecha is None:
            return None
        
        fecha_datetime = datetime.combine(fecha, time.max)
        
        return timezone.make_aware(
            fecha_datetime,
            timezone.get_current_timezone(),
        )