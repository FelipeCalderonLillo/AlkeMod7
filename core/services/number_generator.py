import secrets

from django.db import IntegrityError
from core.models import Cuenta, Contacto


MAX_INTENTOS = 5

def _generar_numero_aleatorio():
    # Genera un número aleatorio con formato xxx-xxxx-xxxx.
    
    numero = secrets.randbelow(100_000_000_000)
    
    digitos = f"{numero:011d}"
    
    return (
        f"{digitos[:3]}-"
        f"{digitos[3:7]}-"
        f"{digitos[7:]}"
    )
    
def _numero_disponible(numero):
    # Comprueba que el número no exista ni en Cuenta ni en Contacto.
    
    existe_en_cuentas = Cuenta.objects.filter(numero_cuenta=numero).exists()
    
    existe_en_contactos = Contacto.objects.filter(numero_cuenta=numero).exists()
    
    return not (existe_en_cuentas or existe_en_contactos)

def generar_numero_cuenta():
    # Genera un número de cuenta disponible globalmente. 
    # La comprobación se realiza contra Cuenta y Contacto.
    
    for _ in range(MAX_INTENTOS):
        numero = _generar_numero_aleatorio()
        
        if _numero_disponible(numero):
            return numero
        
    raise RuntimeError("No fue posible generar un número de cuenta disponible.")

def ejecutar_con_numero_unico(creador):
    """ Ejecuta operación de creación utilizando un número generado.
    
    Si ocurre una colisión de unicidad durante la inserción, vuelve a generar el número hasta el máximo de intentos. """
    
    for _ in range(MAX_INTENTOS):
        numero = _generar_numero_aleatorio()
        
        if not _numero_disponible(numero):
            continue
        
        try:
            return creador(numero)
        except IntegrityError:
            continue
        
    raise RuntimeError("No fue posible completar la creación con un número disponible.")