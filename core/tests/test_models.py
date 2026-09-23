from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from core.models import Cuenta, Perfil, CategoriaInteres, Contacto, Transaccion

class PerfilModelTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username='UsuarioTest',
            password='Password123!',
            first_name='Juan',
            last_name='Perez',
        )
        
    def test_crear_perfil(self):
        perfil = Perfil.objects.create(
            usuario=self.usuario,
            fecha_nacimiento=date(1990,5,10),
        )
        
        self.assertEqual(perfil.usuario, self.usuario)
        self.assertEqual(perfil.fecha_nacimiento, date(1990, 5, 10))
        
        
    def test_trabajo_y_biografia_son_opcionales(self):
        perfil = Perfil.objects.create(
            usuario=self.usuario,
            fecha_nacimiento=date(1900, 5, 10),
        )
        
        self.assertEqual(perfil.trabajo, "")
        self.assertEqual(perfil.biografia, "")
        
        
class CuentaModelTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username='UsuarioTest',
            password='Password123!',
        )
        
    def test_crear_cuenta_con_saldo_inicial(self):
        cuenta = Cuenta.objects.create(
            usuario=self.usuario,
            numero_cuenta='123-4567-8901',
        )
        
        self.assertEqual(cuenta.saldo, Decimal('500000.00'))
        
    def test_numero_cuenta_debe_ser_unico(self):
        Cuenta.objects.create(
            usuario=self.usuario,
            numero_cuenta='123-4567-8901',
        )
        
        usuario_2 = User.objects.create_user(
            username='UsuarioTest2',
            password='Password123!',
        )
        
        with self.assertRaises(IntegrityError):
            Cuenta.objects.create(
                usuario=usuario_2,
                numero_cuenta='123-4567-8901',
            )
            
    def test_saldo_negativo_no_es_valido(self):
        cuenta = Cuenta(
            usuario=self.usuario,
            numero_cuenta='123-4567-8901',
            saldo=Decimal('-1.00'),
        )
        
        with self.assertRaises(ValidationError):
            cuenta.full_clean()
            
            
class ContactoModelTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username='UsuarioContacto',
            password='Password123!',
        )
        
    def test_crear_contacto(self):
        contacto = Contacto.objects.create(
            usuario=self.usuario,
            nombre='Harry',
            apellido='Potter',
            banco=Contacto.Banco.GRINGOTTS,
            numero_cuenta='123-4567-8902',
        )
        
        self.assertEqual(contacto.usuario, self.usuario)
        self.assertEqual(contacto.nombre, 'Harry')
        self.assertEqual(contacto.apellido, 'Potter')
        self.assertEqual(contacto.banco, contacto.Banco.GRINGOTTS)
        
    def test_numero_cuenta_de_contacto_debe_ser_unico(self):
        Contacto.objects.create(
            usuario=self.usuario,
            nombre='Harry',
            apellido='Potter',
            banco=Contacto.Banco.GRINGOTTS,
            numero_cuenta='123-4567-8902'
        )
        
        usuario_2 = User.objects.create_user(
            username='UsuarioContacto2',
            password='Password123!',
        )
        
        with self.assertRaises(IntegrityError):
            Contacto.objects.create(
                usuario=usuario_2,
                nombre='Ron',
                apellido='Weasley',
                banco=Contacto.Banco.GOLIATH,
                numero_cuenta='123-4567-8902'
            )
            
            
class CategoriaInteresModelTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username='UsuarioCategoria',
            password='Password123!',
        )
        
    def test_crear_categoria_interes(self):
        categoria = CategoriaInteres.objects.create(
            nombre='Ahorro'
        )
        
        self.assertEqual(categoria.nombre, 'Ahorro')
        
    def test_usuario_puede_tener_varias_categorias(self):
        categoria_ahorro = CategoriaInteres.objects.create(
            nombre='Ahorro'
        )
        categoria_viajes = CategoriaInteres.objects.create(
            nombre='Viajes'
        )
        
        self.usuario.categorias_interes.add(categoria_ahorro, categoria_viajes)
        
        self.assertEqual(self.usuario.categorias_interes.count(), 2)
        
    def test_categoria_puede_tener_varios_usuarios(self):
        categoria = CategoriaInteres.objects.create(
            nombre='Ahorro'
        )
        
        usuario_2 = User.objects.create_user(
            username='UsuarioCategoria2',
            password='Password123!'
        )
        
        categoria.usuarios.add(self.usuario, usuario_2)
        
        self.assertEqual(categoria.usuarios.count(), 2)
        
        
class TransaccionModelTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username='UsuarioTransaccion',
            password='Password123!'
        )
        self.cuenta = Cuenta.objects.create(
            usuario=self.usuario,
            numero_cuenta='123-4567-8901'
        )
        
    def test_crear_deposito(self):
        transaccion = Transaccion.objects.create(
            tipo=Transaccion.Tipo.DEPOSITO,
            monto=Decimal('1000.00'),
            fecha_hora=timezone.now(),
            cuenta_destino=self.cuenta,
        )
        
        self.assertEqual(transaccion.tipo, Transaccion.Tipo.DEPOSITO)
        self.assertEqual(transaccion.monto, Decimal('1000.00'))
        
    def test_transaccion_puede_relacionarse_con_cuentas(self):
        usuario_2 = User.objects.create_user(
            username='UsuarioDestino',
            password='Password123!'
        )
        
        cuenta_destino = Cuenta.objects.create(
            usuario=usuario_2,
            numero_cuenta='987-6543-2109'
        )
        
        transaccion = Transaccion.objects.create(
            tipo=Transaccion.Tipo.TRANSFERENCIA_INTERNA,
            monto=Decimal('10000.00'),
            fecha_hora=timezone.now(),
            cuenta_origen=self.cuenta,
            cuenta_destino=cuenta_destino
        )
        
        self.assertEqual(transaccion.cuenta_origen, self.cuenta)
        self.assertEqual(transaccion.cuenta_destino, cuenta_destino)
        
    def test_transaccion_puede_relacionarse_con_contacto(self):
        contacto = Contacto.objects.create(
            usuario=self.usuario,
            nombre='Juan',
            apellido='Pérez',
            banco=Contacto.Banco.GOLIATH,
            numero_cuenta='456-7890-1234'
        )
        
        transaccion = Transaccion.objects.create(
            tipo=Transaccion.Tipo.TRANSFERENCIA_EXTERNA,
            monto=Decimal('15000.00'),
            fecha_hora=timezone.now(),
            cuenta_origen=self.cuenta,
            contacto=contacto
        )
        
        self.assertEqual(transaccion.contacto, contacto)
        
    def test_transaccion_conserva_datos_historicos(self):
        contacto = Contacto.objects.create(
            usuario=self.usuario,
            nombre='Ana',
            apellido='Gómez',
            banco=Contacto.Banco.GOLIATH,
            numero_cuenta='456-7890-1234'
        )
        
        transaccion = Transaccion.objects.create(
            tipo=Transaccion.Tipo.TRANSFERENCIA_EXTERNA,
            monto=Decimal('20000.00'),
            fecha_hora=timezone.now(),
            cuenta_origen=self.cuenta,
            contacto=contacto,
            origen_nombre='Juan',
            origen_apellido='Pérez',
            origen_numero_cuenta='123-4567-8901',
            destino_nombre='Ana',
            destino_apellido='Gómez',
            destino_numero_cuenta='456-7890-1234',
            destino_banco='Goliath National Bank',
        )
        
        self.assertEqual(transaccion.origen_nombre, 'Juan')
        self.assertEqual(transaccion.origen_apellido, 'Pérez')
        self.assertEqual(transaccion.origen_numero_cuenta, '123-4567-8901')
        self.assertEqual(transaccion.destino_nombre, 'Ana')
        self.assertEqual(transaccion.destino_apellido, 'Gómez')
        self.assertEqual(transaccion.destino_numero_cuenta, '456-7890-1234')
        self.assertEqual(transaccion.destino_banco, 'Goliath National Bank')
        
    def test_no_se_permite_monto_cero(self):
        with self.assertRaises(IntegrityError):
            Transaccion.objects.create(
                tipo=Transaccion.Tipo.DEPOSITO,
                monto=Decimal('0.00'),
                fecha_hora=timezone.now(),
                cuenta_destino=self.cuenta,
            )
            
    def test_no_se_permite_monto_negativo(self):
        with self.assertRaises(IntegrityError):
            Transaccion.objects.create(
                tipo=Transaccion.Tipo.DEPOSITO,
                monto=Decimal('-1000.00'),
                fecha_hora=timezone.now(),
                cuenta_destino=self.cuenta,
            )
            
    def test_deposito_no_puede_tener_cuentas_ni_contacto(self):
        usuario_2 = User.objects.create_user(
            username='UsuarioDepositoInvalido',
            password='Password123!'
        )
        cuenta_destino = Cuenta.objects.create(
            usuario=usuario_2,
            numero_cuenta='321-6547-8901'
        )
        
        with self.assertRaises(IntegrityError):
            Transaccion.objects.create(
                tipo=Transaccion.Tipo.DEPOSITO,
                monto=Decimal('5000.00'),
                fecha_hora=timezone.now(),
                cuenta_origen=self.cuenta,
                cuenta_destino=cuenta_destino,
            )
            
    def test_transferencia_interna_debe_tener_origen_y_destino(self):
        with self.assertRaises(IntegrityError):
            Transaccion.objects.create(
                tipo=Transaccion.Tipo.TRANSFERENCIA_INTERNA,
                monto=Decimal('10000.00'),
                fecha_hora=timezone.now(),
                cuenta_origen=self.cuenta
            )
            
    def test_transferencia_externa_debe_tener_origen_y_contacto(self):
        with self.assertRaises(IntegrityError):
            Transaccion.objects.create(
                tipo=Transaccion.Tipo.TRANSFERENCIA_EXTERNA,
                monto=Decimal('10000.00'),
                fecha_hora=timezone.now(),
                cuenta_origen=self.cuenta
            )
            
    def test_deposito_debe_tener_cuenta_destino(self):
        transaccion = Transaccion(
            tipo=Transaccion.Tipo.DEPOSITO,
            monto=Decimal("1000.00"),
            fecha_hora=timezone.now(),
            cuenta_destino=self.cuenta,
        )

        transaccion.full_clean()

        self.assertEqual(
            transaccion.cuenta_destino,
            self.cuenta,
        )
        
    def test_deposito_sin_cuenta_destino_es_invalido(self):
        transaccion = Transaccion(
            tipo=Transaccion.Tipo.DEPOSITO,
            monto=Decimal("1000.00"),
            fecha_hora=timezone.now(),
        )

        with self.assertRaises(ValidationError):
            transaccion.full_clean()