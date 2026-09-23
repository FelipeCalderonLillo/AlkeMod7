from decimal import Decimal

from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from core.models import Cuenta, Perfil
from core.services.number_generator import ejecutar_con_numero_unico




class RegistrationService:
    
    @staticmethod
    def _validar_fecha_nacimiento(fecha_nacimiento):
        today = timezone.localdate()
        
        if fecha_nacimiento > today:
            raise ValueError("La fecha de nacimiento no puede ser futura.")
        
        edad = today.year - fecha_nacimiento.year - (
            (today.month, today.day)
            < (fecha_nacimiento.month, fecha_nacimiento.day)
        )
        
        if edad < 18:
            raise ValueError("El usuario debe ser mayor o igual a 18 años.")
        
    @staticmethod
    def _validar_username(username):
        if User.objects.filter(username__iexact=username).exists():
            raise ValueError("Ya existe un usuario con ese nombre de usuario.")
        
    @staticmethod
    def _validar_email(email):
        if User.objects.filter(email__iexact=email).exists():
            raise ValueError("Ya existe un usuario registrado con ese e-mail.")
    
    @staticmethod
    @transaction.atomic
    def registrar_usuario(
        *,
        username,
        password,
        first_name,
        last_name,
        email,
        fecha_nacimiento,
        trabajo="",
        biografia=""
    ):        
        RegistrationService._validar_fecha_nacimiento(fecha_nacimiento)
        
        username = username.strip().capitalize()
        first_name = first_name.strip().title()
        last_name = last_name.strip().title()
        email = email.strip().lower()
        trabajo = trabajo.strip()
        biografia = biografia.strip()
        
        RegistrationService._validar_username(username)
        RegistrationService._validar_email(email)
                
        usuario = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )
        
        Perfil.objects.create(
            usuario=usuario,
            fecha_nacimiento=fecha_nacimiento,
            trabajo=trabajo,
            biografia=biografia
        )
        
        def crear_cuenta(numero):
            return Cuenta.objects.create(
                usuario=usuario,
                numero_cuenta=numero,
                saldo=Decimal("500000.00"),
            )
            
        cuenta = ejecutar_con_numero_unico(crear_cuenta)
        
        return usuario, cuenta
    
    