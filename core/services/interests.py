from django.db import transaction

from core.models import CategoriaInteres




class InterestService:
    @staticmethod
    def obtener_categorias():
        return CategoriaInteres.objects.all().order_by("nombre")
    
    @staticmethod
    @transaction.atomic
    def suscribir_usuario(*, usuario, categoria):
        usuario.categorias_interes.add(categoria)
        
    @staticmethod
    @transaction.atomic
    def desuscribir_usuario(*, usuario, categoria):
        usuario.categorias_interes.remove(categoria)