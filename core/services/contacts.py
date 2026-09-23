from django.db import transaction

from core.models import Contacto
from core.services.number_generator import ejecutar_con_numero_unico



class ContactService:
    @staticmethod
    def obtener_contactos(*, usuario):
        return Contacto.objects.filter(
            usuario=usuario,
        ).order_by("apellido", "nombre")
    
    @staticmethod
    @transaction.atomic
    def crear_contacto(*, usuario, nombre, apellido, banco,):
        def crear(numero_cuenta):
            return Contacto.objects.create(
                usuario=usuario,
                nombre=nombre,
                apellido=apellido,
                banco=banco,
                numero_cuenta=numero_cuenta,
            )
            
        return ejecutar_con_numero_unico(crear)