from datetime import timedelta

from django.db.models import Q, Sum
from django.utils import timezone

from core.models import Transaccion



class ReportService:
    @staticmethod
    def obtener_transacciones(*, usuario, fecha_inicio=None, fecha_fin=None):
        cuenta = usuario.cuenta
        
        if fecha_fin is None:
            fecha_fin = timezone.now()
            
        if fecha_inicio is None:
            fecha_inicio = fecha_fin - timedelta(days=30)
            
        return(
            Transaccion.objects.filter(
                Q(cuenta_origen=cuenta) |
                Q(cuenta_destino=cuenta),
                fecha_hora__gte=fecha_inicio,
                fecha_hora__lte=fecha_fin,
            ).order_by("-fecha_hora")
        )
        
    @staticmethod
    def obtener_resumen(*, usuario, fecha_inicio=None, fecha_fin=None):
        transacciones = ReportService.obtener_transacciones(
            usuario=usuario,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )
        
        cuenta = usuario.cuenta
        
        ingresos = transacciones.filter(
            cuenta_destino=cuenta
        ).aggregate(
            total=Sum("monto")
        )["total"] or 0
        
        egresos = transacciones.filter(
            cuenta_origen=cuenta
        ).aggregate(
            total=Sum("monto")
        )["total"] or 0
        
        return{
            "ingresos": ingresos,
            "egresos": egresos,
            "cantidad_transacciones": transacciones.count(),
        }