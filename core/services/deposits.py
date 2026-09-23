from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from core.models import Cuenta, Transaccion



MINIMO_DEPOSITO = Decimal("1000.00")


class DepositError(Exception):
    """Error de negocio relacionado con un depósito."""
    

class DepositService:
    @staticmethod
    @transaction.atomic
    def realizar_deposito(*, usuario, monto):
        if monto < MINIMO_DEPOSITO:
            raise DepositError("El monto mínimo de depósito es $1.000.")
        
        if monto != monto.to_integral_value():
            raise DepositError("El monto debe ser un número entero, sin decimales.")
        
        cuenta = (
            Cuenta.objects.select_for_update()
            .select_related("usuario")
            .get(usuario=usuario)
        )
        
        if not cuenta.usuario.is_active:
            raise DepositError("La cuenta pertenece a un usuario inactivo.")
        
        cuenta.saldo += monto
        cuenta.save(update_fields=["saldo"])
        
        transaccion = Transaccion.objects.create(
            tipo=Transaccion.Tipo.DEPOSITO,
            monto=monto,
            fecha_hora=timezone.now(),
            cuenta_destino=cuenta,
            destino_nombre=cuenta.usuario.first_name,
            destino_apellido=cuenta.usuario.last_name,
            destino_numero_cuenta=cuenta.numero_cuenta,
        )
        
        return transaccion