from django.db import models
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db.models import Q
from django.core.validators import MinValueValidator
import uuid

# Create your models here.

class Perfil(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.PROTECT, related_name='perfil')
    trabajo = models.CharField(max_length=100, blank=True)
    fecha_nacimiento = models.DateField()
    biografia = models.CharField(max_length=500, blank=True)
    
    def __str__(self):
        return f"Perfil de {self.usuario.username}"
    
    
class Cuenta(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.PROTECT, related_name='cuenta')
    numero_cuenta = models.CharField(max_length=13, unique=True, validators=[
        RegexValidator(
            regex=r"^\d{3}-\d{4}-\d{4}$",
            message="El número de cuenta debe tener el formato xxx-xxxx-xxxx.",
        )
    ])
    saldo = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("500000.00"),
                                validators=[
                                    MinValueValidator(Decimal("0.00"))
                                ])
    creada_en = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(saldo__gte=0),
                name="cuenta_saldo_no_negativo",
            ),
        ]
        
    def __str__(self):
        return self.numero_cuenta
    
    
class Contacto(models.Model):
    
    class Banco(models.TextChoices):
        GRINGOTTS = "GRINGOTTS", "Gringotts Wizarding Bank"
        GOLIATH = "GOLIATH", "Goliath National Bank"
        BANKS_BANK = "BANKS_BANK", "Bank's Bank"
        
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, related_name='contactos',)
    nombre = models.CharField(max_length=150)
    apellido = models.CharField(max_length=150)
    banco = models.CharField(max_length=30, choices=Banco.choices)
    numero_cuenta = models.CharField(
        max_length=13,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^\d{3}-\d{4}-\d{4}$",
                message='El número de cuenta debe tener el formato xxx-xxxx-xxxx.'
            )
        ],
    )
    
    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.numero_cuenta}"
    
    
class CategoriaInteres(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    usuarios = models.ManyToManyField(User, related_name='categorias_interes', blank=True)
    
    def __str__(self):
        return self.nombre
    
    
class TransferenciaPendiente(models.Model):
    class Tipo(models.TextChoices):
        INTERNA = "INTERNA", "Transferencia interna"
        EXTERNA = "EXTERNA", "Transferencia externa"
        
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, related_name="transferencias_pendientes")
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    monto = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("1000.00"))])
    cuenta_origen = models.ForeignKey(Cuenta, on_delete=models.PROTECT, related_name="transferencias_pendientes_origen", null=True, blank=True)
    cuenta_destino = models.ForeignKey(Cuenta, on_delete=models.PROTECT, related_name="transferencias_pendientes_destino", null=True, blank=True)
    contacto = models.ForeignKey(Contacto, on_delete=models.PROTECT, related_name="transferencias_pendientes_contacto", null=True, blank=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    creado_en = models.DateTimeField(auto_now_add=True)
    expira_en = models.DateTimeField()
    usado_en = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(tipo="INTERNA", cuenta_destino__isnull=False, contacto__isnull=True) |
                    Q(tipo="EXTERNA", cuenta_destino__isnull=True, contacto__isnull=False)
                ),
                name="transferencia_pendiente_combinacion_valida",
            ),
            models.CheckConstraint(
                condition=Q(monto__gte=Decimal("1000.00")),
                name="transferencia_pendiente_monto_minimo",
            ),
        ]
        
    def __str__(self):
        return f"{self.get_tipo_display()} - ${self.monto}"
    
    
class Transaccion(models.Model):
    
    class Tipo(models.TextChoices):
        DEPOSITO = "DEPOSITO", "Depósito"
        TRANSFERENCIA_INTERNA = "TRANSFERENCIA_INTERNA", "Transferencia interna"
        TRANSFERENCIA_EXTERNA = "TRANSFERENCIA_EXTERNA", "Transferencia externa"
        
    tipo = models.CharField(max_length=30, choices=Tipo.choices)
    monto = models.DecimalField(max_digits=12, decimal_places=2,
                                validators=[
                                    MinValueValidator(Decimal('0.01')),
                                ])
    fecha_hora = models.DateTimeField()
    cuenta_origen = models.ForeignKey(
        Cuenta,
        on_delete=models.PROTECT,
        related_name='transacciones_origen',
        null=True,
        blank=True,
    )
    cuenta_destino = models.ForeignKey(
        Cuenta,
        on_delete=models.PROTECT,
        related_name='transacciones_destino',
        null=True,
        blank=True,
    )
    contacto = models.ForeignKey(
        Contacto,
        on_delete=models.PROTECT,
        related_name='transacciones',
        null=True,
        blank=True,
    )
    origen_nombre = models.CharField(max_length=150, blank=True)
    origen_apellido = models.CharField(max_length=150, blank=True)
    origen_numero_cuenta = models.CharField(max_length=13, blank=True)
    destino_nombre = models.CharField(max_length=150, blank=True)
    destino_apellido = models.CharField(max_length=150, blank=True)
    destino_numero_cuenta = models.CharField(max_length=13, blank=True)
    destino_banco = models.CharField(max_length=30, blank=True)
    
    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(monto__gt=0),
                name='transaccion_monto_positivo'
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        tipo='DEPOSITO',
                        cuenta_origen__isnull=True,
                        cuenta_destino__isnull=False,
                        contacto__isnull=True,
                    )
                    |
                    Q(
                        tipo='TRANSFERENCIA_INTERNA',
                        cuenta_origen__isnull=False,
                        cuenta_destino__isnull=False,
                        contacto__isnull=True,
                    )
                    |
                    Q(
                        tipo='TRANSFERENCIA_EXTERNA',
                        cuenta_origen__isnull=False,
                        cuenta_destino__isnull=True,
                        contacto__isnull=False
                    )
                ),
                name='transaccion_combinacion_valida',
            ),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_display()} - ${self.monto}"