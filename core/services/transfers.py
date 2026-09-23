from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from core.models import Cuenta, Transaccion, TransferenciaPendiente


MINIMO_TRANSFERENCIA = Decimal("1000.00")
DURACION_TOKEN = timedelta(minutes=5)



class TransferError(Exception):
    """Error de negocio relacionado con una transferencia"""
    

class TransferService:
    @staticmethod
    @transaction.atomic
    def crear_pendiente(
        *,
        usuario,
        tipo,
        monto,
        cuenta_destino=None,
        contacto=None,
    ):
        if monto < MINIMO_TRANSFERENCIA:
            raise TransferError("El monto mínimo de transferencia es $1.000")
        
        if monto != monto.to_integral_value():
            raise TransferError("El monto debe ser un número entero, sin decimales.")
        
        cuenta_origen = Cuenta.objects.get(usuario=usuario)
        
        if tipo == TransferenciaPendiente.Tipo.INTERNA:
            return TransferService._crear_pendiente_interna(
                usuario=usuario,
                cuenta_origen=cuenta_origen,
                cuenta_destino=cuenta_destino,
                contacto=contacto,
                monto=monto,
            )
            
        if tipo == TransferenciaPendiente.Tipo.EXTERNA:
            return TransferService._crear_pendiente_externa(
                usuario=usuario,
                cuenta_origen=cuenta_origen,
                contacto=contacto,
                cuenta_destino=cuenta_destino,
                monto=monto,
            )
            
        raise TransferError("El tipo de transferencia no es válido.")
    
    @staticmethod
    def _crear_pendiente_interna(
        *,
        usuario,
        cuenta_origen,
        cuenta_destino,
        contacto,
        monto,
    ):
        if contacto is not None:
            raise TransferError("Una transferencia interna no utiliza un contacto.")
        
        if cuenta_destino is None:
            raise TransferError("La transferencia interna requiere una cuenta de destino.")
        
        if cuenta_destino.usuario_id == usuario.id:
            raise TransferError("No puedes transferir dinero a tu propia cuenta.")
        
        if not cuenta_destino.usuario.is_active:
            raise TransferError("La cuenta de destino no pertenece a un usuario activo.")
        
        if cuenta_origen.pk == cuenta_destino.pk:
            raise TransferError("No puedes transferir dinero a tu propia cuenta.")
        
        if cuenta_origen.saldo < monto:
            raise TransferError("saldo insuficiente para realizar la transferencia.")
        
        return TransferenciaPendiente.objects.create(
            usuario=usuario,
            tipo=TransferenciaPendiente.Tipo.INTERNA,
            monto=monto,
            cuenta_origen=cuenta_origen,
            cuenta_destino=cuenta_destino,
            expira_en=timezone.now() + DURACION_TOKEN,
        )
        
    @staticmethod
    def _crear_pendiente_externa(
        *,
        usuario,
        cuenta_origen,
        contacto,
        cuenta_destino,
        monto,
    ):
        if cuenta_destino is not None:
            raise TransferError("Una transferencia externa no utiliza una cuenta de destino.")
        
        if contacto is None:
            raise TransferError("La transferencia externa requiere un contacto.")
        
        if contacto.usuario_id != usuario.id:
            raise TransferError("El contacto seleccionado no pertenece al usuario.")
        
        if cuenta_origen.saldo < monto:
            raise TransferError("Saldo insuficiente para realizar la transferencia.")
        
        return TransferenciaPendiente.objects.create(
            usuario=usuario,
            tipo=TransferenciaPendiente.Tipo.EXTERNA,
            monto=monto,
            cuenta_origen=cuenta_origen,
            contacto=contacto,
            expira_en=timezone.now() + DURACION_TOKEN,
        )
        
    @staticmethod
    @transaction.atomic
    def ejecutar_pendiente(*, usuario, token):
        try:
            pendiente = (
                TransferenciaPendiente.objects.select_for_update()
                .select_related(
                    "usuario",
                    "cuenta_origen",
                    "cuenta_destino",
                    "contacto",
                    "contacto__usuario",
                ).get(
                    token=token,
                    usuario=usuario,
                )
            )
        except TransferenciaPendiente.DoesNotExist:
            raise TransferError("La transferencia pendiente no existe.")
        
        ahora = timezone.now()
        
        if pendiente.usado_en is not None:
            raise TransferError("El token de confirmación ya fue utilizado.")
        
        if ahora >= pendiente.expira_en:
            raise TransferError("El token de confirmación ha expirado.")
        
        cuenta_origen= (
            Cuenta.objects.select_for_update()
            .select_related("usuario").get(pk=pendiente.cuenta_origen_id)
        )
        
        cuenta_destino = None
        
        if pendiente.tipo == TransferenciaPendiente.Tipo.INTERNA:
            cuenta_destino = (
                Cuenta.objects.select_for_update()
                .select_related("usuario").get(pk=pendiente.cuenta_destino_id)
            )
            
            if cuenta_destino.usuario_id == usuario.id:
                raise TransferError("No puedes transferir dinero a tu propia cuenta.")
            
            if not cuenta_destino.usuario.is_active:
                raise TransferError("La cuenta de destino no pertenece a un usuario activo.")
            
        if cuenta_origen.saldo < pendiente.monto:
            raise TransferError("Saldo insuficiente para realizar la transferencia.")
        
        origen_nombre = cuenta_origen.usuario.first_name
        origen_apellido = cuenta_origen.usuario.last_name
        origen_numero_cuenta = cuenta_origen.numero_cuenta
        
        cuenta_origen.saldo -= pendiente.monto
        cuenta_origen.save(update_fields=["saldo"])
        
        if pendiente.tipo == TransferenciaPendiente.Tipo.INTERNA:
            cuenta_destino.saldo += pendiente.monto
            cuenta_destino.save(update_fields=["saldo"])
            
            transaccion = Transaccion.objects.create(
                tipo=Transaccion.Tipo.TRANSFERENCIA_INTERNA,
                monto=pendiente.monto,
                fecha_hora=ahora,
                cuenta_origen=cuenta_origen,
                cuenta_destino=cuenta_destino,
                origen_nombre=origen_nombre,
                origen_apellido=origen_apellido,
                origen_numero_cuenta=origen_numero_cuenta,
                destino_nombre=cuenta_destino.usuario.first_name,
                destino_apellido=cuenta_destino.usuario.last_name,
                destino_numero_cuenta=cuenta_destino.numero_cuenta,
            )
            
        elif pendiente.tipo == TransferenciaPendiente.Tipo.EXTERNA:
            contacto = pendiente.contacto
            
            transaccion = Transaccion.objects.create(
                tipo=Transaccion.Tipo.TRANSFERENCIA_EXTERNA,
                monto=pendiente.monto,
                fecha_hora=ahora,
                cuenta_origen=cuenta_origen,
                contacto=contacto,
                origen_nombre=origen_nombre,
                origen_apellido=origen_apellido,
                origen_numero_cuenta=origen_numero_cuenta,
                destino_nombre=contacto.nombre,
                destino_apellido=contacto.apellido,
                destino_numero_cuenta=contacto.numero_cuenta,
                destino_banco=contacto.get_banco_display(),
            )
            
        else:
            raise TransferError("El tipo de transferencia pendiente no es válido.")
        
        pendiente.usado_en = ahora
        pendiente.save(update_fields=["usado_en"])
        
        return transaccion