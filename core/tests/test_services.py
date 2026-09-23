from unittest.mock import patch
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from core.models import Contacto, Cuenta, Perfil, Transaccion, CategoriaInteres, TransferenciaPendiente
from core.services.number_generator import ejecutar_con_numero_unico, generar_numero_cuenta
from core.services.registration import RegistrationService
from core.services.profile import ProfileService
from core.services.contacts import ContactService
from core.services.interests import InterestService
from core.services.reports import ReportService
from core.services.transfers import TransferError, TransferService


class NumberGeneratorTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username='UsuarioNumero',
            password='Password123!'
        )
        
    def test_genera_numero_con_formato_correcto(self):
        numero = generar_numero_cuenta()
        
        self.assertRegex(
            numero,
            r"^\d{3}-\d{4}-\d{4}$"
        )
        
    def test_numero_generado_no_existe_en_cuenta(self):
        cuenta = Cuenta.objects.create(
            usuario=self.usuario,
            numero_cuenta='123-4567-8901'
        )
        
        numero = generar_numero_cuenta()
        
        self.assertNotEqual(
            numero,
            cuenta.numero_cuenta
        )
        
    def test_numero_generado_no_existe_en_contactos(self):
        contacto = Contacto.objects.create(
            usuario=self.usuario,
            nombre='Juan',
            apellido='Pérez',
            banco=Contacto.Banco.GOLIATH,
            numero_cuenta='123-4567-8901',
        )
        
        numero = generar_numero_cuenta()
        
        self.assertNotEqual(numero, contacto.numero_cuenta)
        
    def test_numero_no_se_repite_entre_cuenta_y_contactos(self):
        Cuenta.objects.create(
            usuario=self.usuario,
            numero_cuenta='123-4567-8901'
        )
        
        contacto = Contacto.objects.create(
            usuario=self.usuario,
            nombre='Juan',
            apellido='Pérez',
            banco=Contacto.Banco.GOLIATH,
            numero_cuenta='987-6543-2109'
        )
        
        numero = generar_numero_cuenta()
        
        self.assertNotIn(
            numero,
            {
                '123-4567-8901',
                contacto.numero_cuenta,
            },
        )
        
    @patch(
        "core.services.number_generator._generar_numero_aleatorio"
    )
    def test_reintenta_si_el_numero_ya_existe(self, mock_generador):
        Cuenta.objects.create(
            usuario=self.usuario,
            numero_cuenta='123-4567-8901'
        )
        
        mock_generador.side_effect = [
            '123-4567-8901',
            '987-6543-2109'
        ]
        
        numero = generar_numero_cuenta()
        
        self.assertEqual(numero, '987-6543-2109')
        
    @patch(
        "core.services.number_generator._generar_numero_aleatorio"
    )
    def test_reintenta_si_ocurre_integrity_error(self, mock_generador):
        mock_generador.side_effect = [
            "123-4567-8901",
            "987-6543-2109"
        ]
        
        intentos = []
        
        def creador(numero):
            intentos.append(numero)
            
            if len(intentos) == 1:
                raise IntegrityError()
            
            return numero
        
        resultado = ejecutar_con_numero_unico(creador)
        
        self.assertEqual(resultado, '987-6543-2109')
        self.assertEqual(intentos, [
            '123-4567-8901',
            '987-6543-2109'
        ],)
        
        
class RegistrationServiceTests(TestCase):
    
    def test_registra_usuario_perfil_y_cuenta(self):
        usuario, cuenta = RegistrationService.registrar_usuario(
            username=' usuarioNuevo ',
            password='Password123!',
            first_name=' juan ',
            last_name=' perez ',
            email='JUAN@EXAMPLE.COM',
            fecha_nacimiento=date(1995, 5, 10),
            trabajo=' Ingeniero ',
            biografia=' Mi biografía '
        )
        
        self.assertIsNotNone(usuario.pk)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Cuenta.objects.count(), 1)
        
    def test_normaliza_datos_del_usuario(self):
        usuario, cuenta = RegistrationService.registrar_usuario(
            username=" uSuArIo ",
            password="Password123!",
            first_name=" jUaN ",
            last_name=" péRez góMez ",
            email=" JUAN@EXAMPLE.COM ",
            fecha_nacimiento=date(1995, 5, 10),
            trabajo=" Ingeniero ",
            biografia=" Texto de prueba ",
        )
        
        self.assertEqual(usuario.username, "Usuario")
        self.assertEqual(usuario.first_name, "Juan")
        self.assertEqual(usuario.last_name, "Pérez Gómez")
        self.assertEqual(usuario.email, "juan@example.com")
        self.assertEqual(usuario.perfil.trabajo, "Ingeniero")
        self.assertEqual(usuario.perfil.biografia, "Texto de prueba")
        
    def test_cuenta_recibe_saldo_inicial(self):
        usuario, cuenta = RegistrationService.registrar_usuario(
            username="UsuarioSaldo",
            password="Password123!",
            first_name="Ana",
            last_name="Gómez",
            email="ana@example.com",
            fecha_nacimiento=date(1990, 1, 1),
        )
        
        self.assertEqual(cuenta.saldo, Decimal('500000.00'))
        
    def test_cuenta_recibe_numero_generado(self):
        usuario, cuenta = RegistrationService.registrar_usuario(
            username="UsuarioNumeroRegistro",
            password="Password123!",
            first_name="Pedro",
            last_name="Gómez",
            email="pedro@example.com",
            fecha_nacimiento=date(1990, 1, 1),
        )
        
        self.assertRegex(
            cuenta.numero_cuenta,
            r"^\d{3}-\d{4}-\d{4}$",
        )
        
    def test_usuario_queda_con_password_hasheado(self):
        usuario, cuenta = RegistrationService.registrar_usuario(
            username="UsuarioPassword",
            password="Password123!",
            first_name="Luis",
            last_name="Gómez",
            email="luis@example.com",
            fecha_nacimiento=date(1990, 1, 1),
        )
        
        self.assertNotEqual(usuario.password, "Password123!")
        self.assertTrue(usuario.check_password("Password123!"))
        
    @patch("core.services.registration.Perfil.objects.create")
    def test_registro_es_atomico_si_falla_la_creacion_del_perfil(self, mock_crear_perfil):
        mock_crear_perfil.side_effect = RuntimeError("Error de prueba")
        
        with self.assertRaises(RuntimeError):
            RegistrationService.registrar_usuario(
                username="UsuarioRollback",
                password="Password123!",
                first_name="Carlos",
                last_name="Pérez",
                email="carlos@example.com",
                fecha_nacimiento=date(1990, 1, 1),
            )
            
            self.assertEqual(User.objects.count(), 0)
            self.assertEqual(Perfil.objects.count(), 0)
            self.assertEqual(Cuenta.objects.count(), 0)
            
    def test_registro_usuario_con_18_anios_exactos(self):
        today = timezone.localdate()
        
        fecha_nacimiento = today.replace(year=today.year - 18)
        
        usuario, cuenta = RegistrationService.registrar_usuario(
            username="usuario18",
            password="Password123!",
            first_name="Juan",
            last_name="Perez",
            email="juan18@example.com",
            fecha_nacimiento=fecha_nacimiento,
        )
        
        self.assertIsNotNone(usuario)
        self.assertIsNotNone(cuenta)
        
    def test_rechaza_usuario_menor_de_18_anios(self):
        today = timezone.localdate()
        
        fecha_nacimiento = today.replace(
            year=today.year - 18
        ) + timedelta(days=1)
        
        with self.assertRaises(ValueError):
            RegistrationService.registrar_usuario(
                username="menor",
                password="Password123!",
                first_name="Juan",
                last_name="Perez",
                email="menor@example.com",
                fecha_nacimiento=fecha_nacimiento,
            )
            
    def test_rechaza_fecha_de_nacimiento_futura(self):
        fecha_nacimiento = timezone.localdate() + timedelta(days=1)
        
        with self.assertRaises(ValueError):
            RegistrationService.registrar_usuario(
                username="futuro",
                password="Password123!",
                first_name="Juan",
                last_name="Perez",
                email="futuro@example.com",
                fecha_nacimiento=fecha_nacimiento,
            )
            
    def test_fecha_invalida_no_crea_perfil_ni_cuenta(self):
        today = timezone.localdate()
        
        fecha_nacimiento = today.replace(
            year=today.year - 18
        ) + timedelta(days=1)
        
        with self.assertRaises(ValueError):
            RegistrationService.registrar_usuario(
                username="rollbackedad",
                password="Password123!",
                first_name="Juan",
                last_name="Perez",
                email="rollbackedad@example.com",
                fecha_nacimiento=fecha_nacimiento,
            )
            
            self.assertFalse(User.objects.filter(username="Rollbackedad").exists())
            self.assertFalse(Perfil.objects.filter(usuario="Rollbackedad").exists())
            self.assertFalse(Cuenta.objects.filter(usuario="Rollbackedad").exists())
            
    def test_registra_usuario_con_email_nuevo(self):
        fecha_nacimiento = timezone.localdate().replace(
            year=timezone.localdate().year - 20
        )
        
        usuario, cuenta = RegistrationService.registrar_usuario(
            username="emailnuevo",
            password="Password123!",
            first_name="Juan",
            last_name="Perez",
            email="nuevo@example.com",
            fecha_nacimiento=fecha_nacimiento,
        )
        
        self.assertEqual(usuario.email, "nuevo@example.com")
        self.assertIsNotNone(cuenta)
        
    def test_rechaza_email_repetido(self):
        fecha_nacimiento = timezone.localdate().replace(
            year=timezone.localdate().year - 20
        )
        
        RegistrationService.registrar_usuario(
            username="primerusuario",
            password="Password123!",
            first_name="Juan",
            last_name="Perez",
            email="repetido@example.com",
            fecha_nacimiento=fecha_nacimiento,
        )
        
        with self.assertRaises(ValueError):
            RegistrationService.registrar_usuario(
                username="segundousuario",
                password="Password123!",
                first_name="Pedro",
                last_name="Gomez",
                email="repetido@example.com",
                fecha_nacimiento=fecha_nacimiento,
            )
            
    def test_rechaza_email_repetido_sin_importar_mayusculas(self):
        fecha_nacimiento = timezone.localdate().replace(
            year=timezone.localdate().year - 20
        )
        
        RegistrationService.registrar_usuario(
            username="primerusuario",
            password="Password123!",
            first_name="Juan",
            last_name="Perez",
            email="usuario@example.com",
            fecha_nacimiento=fecha_nacimiento,
        )
        
        with self.assertRaises(ValueError):
            RegistrationService.registrar_usuario(
                username="segundousuario",
                password="Password123!",
                first_name="Pedro",
                last_name="Gomez",
                email="USUARIO@EXAMPLE.COM",
                fecha_nacimiento=fecha_nacimiento,
            )
            
    def test_rechaza_username_repetido(self):
        fecha_nacimiento = timezone.localdate().replace(
            year=timezone.localdate().year - 20
        )
        
        RegistrationService.registrar_usuario(
            username="usuarioexistente",
            password="Password123!",
            first_name="Juan",
            last_name="Perez",
            email="primer@example.com",
            fecha_nacimiento=fecha_nacimiento,
        )
        
        with self.assertRaises(ValueError):
            RegistrationService.registrar_usuario(
                username="usuarioexistente",
                password="Password123!",
                first_name="Pedro",
                last_name="Gomez",
                email="segundo@example.com",
                fecha_nacimiento=fecha_nacimiento,
            )
            
    def test_rechaza_username_repetido_sin_importar_mayusculas(self):
        fecha_nacimiento = timezone.localdate().replace(
            year=timezone.localdate().year - 20
        )
        
        RegistrationService.registrar_usuario(
            username="UsuarioExistente",
            password="Password123!",
            first_name="Juan",
            last_name="Perez",
            email="primer@example.com",
            fecha_nacimiento=fecha_nacimiento,
        )
        
        with self.assertRaises(ValueError):
            RegistrationService.registrar_usuario(
                username="USUARIOEXISTENTE",
                password="Password123!",
                first_name="Pedro",
                last_name="Gomez",
                email="segundo@example.com",
                fecha_nacimiento=fecha_nacimiento,
            )
            
            
class ProfileServiceTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username="Usuario",
            password="Password123!",
            first_name="Juan",
            last_name="Perez",
            email="usuario@example.com",
        )
        
        self.perfil = Perfil.objects.create(
            usuario=self.usuario,
            fecha_nacimiento=date(2000, 1, 1),
            trabajo="Ingeniero",
            biografia="Biografía original",
        )
        
    def test_actualiza_username(self):
        ProfileService.actualizar_perfil(
            usuario=self.usuario,
            username="NuevoUsuario",
            trabajo=self.perfil.trabajo,
            biografia=self.perfil.biografia,
        )
        
        self.usuario.refresh_from_db()
        
        self.assertEqual(self.usuario.username, "NuevoUsuario")
        
    def test_actualiza_trabajo(self):
        ProfileService.actualizar_perfil(
            usuario=self.usuario,
            username=self.usuario.username,
            trabajo="Desarrollador",
            biografia=self.perfil.biografia,
        )
        
        self.perfil.refresh_from_db()
        
        self.assertEqual(self.perfil.trabajo, "Desarrollador")
        
    def test_actualiza_biografia(self):
        ProfileService.actualizar_perfil(
            usuario=self.usuario,
            username=self.usuario.username,
            trabajo=self.perfil.trabajo,
            biografia="Nueva biografía",
        )
        
        self.perfil.refresh_from_db()
        
        self.assertEqual(self.perfil.biografia, "Nueva biografía")
        
    def test_actualiza_usuario_y_perfil(self):
        ProfileService.actualizar_perfil(
            usuario=self.usuario,
            username="NuevoUsuario",
            trabajo="Desarrollador",
            biografia="Nueva biografía",
        )
        
        self.usuario.refresh_from_db()
        self.perfil.refresh_from_db()
        
        self.assertEqual(self.usuario.username, "NuevoUsuario")
        self.assertEqual(self.perfil.trabajo, "Desarrollador")
        self.assertEqual(self.perfil.biografia, "Nueva biografía")
        
    def test_no_modifica_datos_no_editables(self):
        nombre_original = self.usuario.first_name
        apellido_original = self.usuario.last_name
        fecha_original = self.perfil.fecha_nacimiento
        
        ProfileService.actualizar_perfil(
            usuario=self.usuario,
            username="NuevoUsuario",
            trabajo="Desarrollador",
            biografia="Nueva biografía",
        )
        
        self.usuario.refresh_from_db()
        self.perfil.refresh_from_db()
        
        self.assertEqual(self.usuario.first_name, nombre_original)
        self.assertEqual(self.usuario.last_name, apellido_original)
        self.assertEqual(self.perfil.fecha_nacimiento, fecha_original)
        
        
class ContactServiceTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username="Usuario",
            password="password123!",
        )
        
    def test_crear_contacto(self):
        contacto = ContactService.crear_contacto(
            usuario=self.usuario,
            nombre="Juan",
            apellido="Pérez",
            banco=Contacto.Banco.GRINGOTTS,
        )
        
        self.assertIsNotNone(contacto.pk)
        self.assertEqual(contacto.usuario, self.usuario)
        self.assertEqual(contacto.nombre, "Juan")
        self.assertEqual(contacto.apellido, "Pérez")
        self.assertEqual(contacto.banco, Contacto.Banco.GRINGOTTS)
        
    def test_crear_contacto_genera_numero(self):
        contacto = ContactService.crear_contacto(
            usuario=self.usuario,
            nombre="Juan",
            apellido="Pérez",
            banco=Contacto.Banco.GRINGOTTS,
        )
        
        self.assertRegex(contacto.numero_cuenta, r"^\d{3}-\d{4}-\d{4}$")
        
    def test_numero_contacto_es_unico(self):
        contacto_1 = ContactService.crear_contacto(
            usuario=self.usuario,
            nombre="Juan",
            apellido="Pérez",
            banco=Contacto.Banco.GRINGOTTS,
        )
        
        contacto_2 = ContactService.crear_contacto(
            usuario=self.usuario,
            nombre="Ana",
            apellido="Gómez",
            banco=Contacto.Banco.GOLIATH,
        )
        
        self.assertNotEqual(contacto_1.numero_cuenta, contacto_2.numero_cuenta)
        
    def test_contacto_pertenece_al_usuario_que_lo_crea(self):
        contacto = ContactService.crear_contacto(
            usuario=self.usuario,
            nombre="Juan",
            apellido="Pérez",
            banco=Contacto.Banco.BANKS_BANK,
        )
        
        self.assertEqual(contacto.usuario_id, self.usuario.id)
        
        
class InterestServiceTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username="Usuario",
            password="password123"
        )
        
        self.ahorro = CategoriaInteres.objects.create(nombre="Ahorro")
        self.viajes = CategoriaInteres.objects.create(nombre="Viajes")
        
    def test_obtener_categorias_devuelve_todas_las_categorias(self):
        categorias = InterestService.obtener_categorias()
        
        self.assertEqual(categorias.count(), 2)
        self.assertIn(self.ahorro, categorias)
        self.assertIn(self.viajes, categorias)
        
    def test_suscribir_usuario_agrega_categoria(self):
        InterestService.suscribir_usuario(
            usuario=self.usuario,
            categoria=self.ahorro,
        )
        
        self.assertTrue(self.usuario.categorias_interes.filter(id=self.ahorro.id).exists())
        
    def test_desuscribir_usuario_elimina_solo_la_suscripcion(self):
        self.usuario.categorias_interes.add(self.ahorro)
        
        InterestService.desuscribir_usuario(
            usuario=self.usuario,
            categoria=self.ahorro
        )
        
        self.assertFalse(self.usuario.categorias_interes.filter(id=self.ahorro.id).exists())
        self.assertTrue(CategoriaInteres.objects.filter(id=self.ahorro.id).exists())
        
    def test_suscribir_dos_veces_no_crea_duplicados(self):
        InterestService.suscribir_usuario(
            usuario=self.usuario,
            categoria=self.ahorro
        )
        
        InterestService.suscribir_usuario(
            usuario=self.usuario,
            categoria=self.ahorro
        )
        
        self.assertEqual(self.usuario.categorias_interes.filter(id=self.ahorro.id).count(), 1)
        
        
class ReportServiceTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username="Usuario",
            password="password123",
        )
        
        self.otro_usuario = User.objects.create_user(
            username="OtroUsuario",
            password="password123",
        )
        
        self.cuenta = Cuenta.objects.create(
            usuario=self.usuario,
            numero_cuenta="111-1111-1111",
            saldo=Decimal("500000.00"),
        )
        
        self.otra_cuenta = Cuenta.objects.create(
            usuario=self.otro_usuario,
            numero_cuenta="222-2222-2222",
            saldo=Decimal("500000.00"),
        )
        
        self.ahora = timezone.now()
        
    def crear_transaccion(
        self,
        *,
        tipo,
        monto,
        fecha_hora,
        cuenta_origen=None,
        cuenta_destino=None,
        contacto=None,
    ):
        return Transaccion.objects.create(
            tipo=tipo,
            monto=monto,
            fecha_hora=fecha_hora,
            cuenta_origen=cuenta_origen,
            cuenta_destino=cuenta_destino,
            contacto=contacto,
        )
        
    def test_obtener_transacciones_usa_ultimos_30_dias_por_defecto(self):
        reciente = self.crear_transaccion(
            tipo=Transaccion.Tipo.DEPOSITO,
            monto=Decimal("1000.00"),
            fecha_hora=self.ahora - timedelta(days=10),
            cuenta_destino=self.cuenta,
        )

        antigua = self.crear_transaccion(
            tipo=Transaccion.Tipo.DEPOSITO,
            monto=Decimal("2000.00"),
            fecha_hora=self.ahora - timedelta(days=40),
            cuenta_destino=self.cuenta,
        )
        
        transacciones = ReportService.obtener_transacciones(
            usuario=self.usuario,
            fecha_fin=self.ahora,
        )
        
        self.assertIn(reciente, transacciones)
        self.assertNotIn(antigua, transacciones)
        
    def test_obtener_transacciones_acepta_periodo_explicito(self):
        transaccion = self.crear_transaccion(
            tipo=Transaccion.Tipo.DEPOSITO,
            monto=Decimal("1000.00"),
            fecha_hora=self.ahora - timedelta(days=60),
            cuenta_destino=self.cuenta,
        )
        
        transacciones = ReportService.obtener_transacciones(
            usuario=self.usuario,
            fecha_inicio=self.ahora - timedelta(days=90),
            fecha_fin=self.ahora,
        )
        
        self.assertIn(transaccion, transacciones)
        
    def test_obtener_transacciones_no_muestra_transacciones_ajenas(self):
        transaccion = self.crear_transaccion(
            tipo=Transaccion.Tipo.DEPOSITO,
            monto=Decimal("1000.00"),
            fecha_hora=self.ahora,
            cuenta_destino=self.otra_cuenta,
        )
        
        transacciones = ReportService.obtener_transacciones(
            usuario=self.usuario,
            fecha_fin=self.ahora,
        )
        
        self.assertNotIn(transaccion, transacciones)
        
    def test_resumen_calcula_ingresos(self):
        self.crear_transaccion(
            tipo=Transaccion.Tipo.DEPOSITO,
            monto=Decimal("1000.00"),
            fecha_hora=self.ahora,
            cuenta_destino=self.cuenta,
        )
        
        self.crear_transaccion(
            tipo=Transaccion.Tipo.TRANSFERENCIA_INTERNA,
            monto=Decimal("2000.00"),
            fecha_hora=self.ahora,
            cuenta_origen=self.otra_cuenta,
            cuenta_destino=self.cuenta,
        )
        
        resumen = ReportService.obtener_resumen(
            usuario=self.usuario,
            fecha_fin=self.ahora,
        )
        
        self.assertEqual(resumen["ingresos"], Decimal("3000.00"))
        
    def test_resumen_calcula_egresos(self):
        self.crear_transaccion(
            tipo=Transaccion.Tipo.TRANSFERENCIA_INTERNA,
            monto=Decimal("1000.00"),
            fecha_hora=self.ahora,
            cuenta_origen=self.cuenta,
            cuenta_destino=self.otra_cuenta,
        )
        
        resumen = ReportService.obtener_resumen(
            usuario=self.usuario,
            fecha_fin=self.ahora,
        )
        
        self.assertEqual(resumen["egresos"], Decimal("1000.00"))
        
    def test_resumen_calcula_ingresos_y_egresos_independientemente(self):
        self.crear_transaccion(
            tipo=Transaccion.Tipo.DEPOSITO,
            monto=Decimal("5000.00"),
            fecha_hora=self.ahora,
            cuenta_destino=self.cuenta,
        )
        
        self.crear_transaccion(
            tipo=Transaccion.Tipo.TRANSFERENCIA_INTERNA,
            monto=Decimal("2000.00"),
            fecha_hora=self.ahora,
            cuenta_origen=self.cuenta,
            cuenta_destino=self.otra_cuenta,
        )
        
        resumen = ReportService.obtener_resumen(
            usuario=self.usuario,
            fecha_fin=self.ahora,
        )
        
        self.assertEqual(resumen["ingresos"], Decimal("5000.00"))
        self.assertEqual(resumen["egresos"], Decimal("2000.00"))
        
    def test_resumen_cuenta_cantidad_de_transacciones(self):
        self.crear_transaccion(
            tipo=Transaccion.Tipo.DEPOSITO,
            monto=Decimal("1000.00"),
            fecha_hora=self.ahora,
            cuenta_destino=self.cuenta,
        )
        
        self.crear_transaccion(
            tipo=Transaccion.Tipo.TRANSFERENCIA_INTERNA,
            monto=Decimal("2000.00"),
            fecha_hora=self.ahora,
            cuenta_origen=self.cuenta,
            cuenta_destino=self.otra_cuenta,
        )
        
        resumen = ReportService.obtener_resumen(
            usuario=self.usuario,
            fecha_fin=self.ahora,
        )
        
        self.assertEqual(resumen["cantidad_transacciones"], 2)
        
        
class TransferServiceTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username="usuario1",
            password="password123",
            first_name="Juan",
            last_name="Pérez",
            email="juan@example.com",
        )

        self.otro_usuario = User.objects.create_user(
            username="usuario2",
            password="password123",
            first_name="María",
            last_name="González",
            email="maria@example.com",
        )

        self.cuenta_origen = Cuenta.objects.create(
            usuario=self.usuario,
            numero_cuenta="123-4567-8901",
            saldo=Decimal("500000.00"),
        )

        self.cuenta_destino = Cuenta.objects.create(
            usuario=self.otro_usuario,
            numero_cuenta="987-6543-2109",
            saldo=Decimal("200000.00"),
        )

        self.contacto = Contacto.objects.create(
            usuario=self.usuario,
            nombre="Pedro",
            apellido="Ramírez",
            banco=Contacto.Banco.GRINGOTTS,
            numero_cuenta="111-2222-3333",
        )

        self.otro_contacto = Contacto.objects.create(
            usuario=self.otro_usuario,
            nombre="Ana",
            apellido="López",
            banco=Contacto.Banco.GOLIATH,
            numero_cuenta="444-5555-6666",
        )
        
    def test_crear_pendiente_transferencia_interna(self):
        pendiente = TransferService.crear_pendiente(
            usuario=self.usuario,
            tipo=TransferenciaPendiente.Tipo.INTERNA,
            monto=Decimal("1000.00"),
            cuenta_destino=self.cuenta_destino,
        )
        
        self.assertIsNotNone(pendiente.pk)
        self.assertEqual(pendiente.tipo, TransferenciaPendiente.Tipo.INTERNA)
        self.assertEqual(pendiente.monto, Decimal("1000.00"))
        self.assertEqual(pendiente.cuenta_origen, self.cuenta_origen)
        self.assertEqual(pendiente.cuenta_destino, self.cuenta_destino)
        self.assertIsNone(pendiente.contacto)
        self.assertIsNotNone(pendiente.token)
        
    def test_crear_pendiente_transferencia_externa(self):
        pendiente = TransferService.crear_pendiente(
            usuario=self.usuario,
            tipo=TransferenciaPendiente.Tipo.EXTERNA,
            monto=Decimal("1000.00"),
            contacto=self.contacto,
        )
        
        self.assertIsNotNone(pendiente.pk)
        self.assertEqual(pendiente.tipo, TransferenciaPendiente.Tipo.EXTERNA)
        self.assertEqual(pendiente.monto, Decimal("1000.00"))
        self.assertEqual(pendiente.cuenta_origen, self.cuenta_origen)
        self.assertEqual(pendiente.contacto, self.contacto)
        self.assertIsNone(pendiente.cuenta_destino)
        self.assertIsNotNone(pendiente.token)
        
    def test_rechaza_monto_menor_al_minimo(self):
        with self.assertRaises(TransferError):
            TransferService.crear_pendiente(
                usuario=self.usuario,
                tipo=TransferenciaPendiente.Tipo.INTERNA,
                monto=Decimal("999.00"),
                cuenta_destino=self.cuenta_destino,
            )
            
        self.assertFalse(TransferenciaPendiente.objects.exists())
            
    def test_rechaza_monto_con_decimales(self):
        with self.assertRaises(TransferError):
            TransferService.crear_pendiente(
                usuario=self.usuario,
                tipo=TransferenciaPendiente.Tipo.INTERNA,
                monto=Decimal("1000.50"),
                cuenta_destino=self.cuenta_destino,
            )
            
        self.assertFalse(TransferenciaPendiente.objects.exists())
            
    def test_rechaza_transferencia_interna_a_la_propia_cuenta(self):
        with self.assertRaises(TransferError):
            TransferService.crear_pendiente(
                usuario=self.usuario,
                tipo=TransferenciaPendiente.Tipo.INTERNA,
                monto=Decimal("1000.00"),
                cuenta_destino=self.cuenta_origen,
            )
            
        self.assertFalse(TransferenciaPendiente.objects.exists())
            
    def test_rechaza_transferencia_interna_sin_cuenta_destino(self):
        with self.assertRaises(TransferError):
            TransferService.crear_pendiente(
                usuario=self.usuario,
                tipo=TransferenciaPendiente.Tipo.INTERNA,
                monto=Decimal("1000.00"),
            )
            
        self.assertFalse(TransferenciaPendiente.objects.exists())
            
    def test_rechaza_transferencia_externa_sin_contacto(self):
        with self.assertRaises(TransferError):
            TransferService.crear_pendiente(
                usuario=self.usuario,
                tipo=TransferenciaPendiente.Tipo.EXTERNA,
                monto=Decimal("1000.00"),
            )
            
        self.assertFalse(TransferenciaPendiente.objects.exists())
            
    def test_rechaza_contacto_de_otro_usuario(self):
        with self.assertRaises(TransferError):
            TransferService.crear_pendiente(
                usuario=self.usuario,
                tipo=TransferenciaPendiente.Tipo.EXTERNA,
                monto=Decimal("1000.00"),
                contacto=self.otro_contacto,
            )
            
        self.assertFalse(TransferenciaPendiente.objects.exists())
            
    def test_rechaza_saldo_insuficiente(self):
        monto = Decimal("500001.00")
        
        with self.assertRaises(TransferError):
            TransferService.crear_pendiente(
                usuario=self.usuario,
                tipo=TransferenciaPendiente.Tipo.INTERNA,
                monto=monto,
                cuenta_destino=self.cuenta_destino,
            )
            
        self.assertEqual(self.cuenta_origen.saldo, Decimal("500000.00"))
        self.assertFalse(TransferenciaPendiente.objects.exists())
        
    def test_puede_transferir_todo_el_saldo(self):
        pendiente = TransferService.crear_pendiente(
            usuario=self.usuario,
            tipo=TransferenciaPendiente.Tipo.INTERNA,
            monto=Decimal("500000.00"),
            cuenta_destino=self.cuenta_destino,
        )
        
        transaccion = TransferService.ejecutar_pendiente(
            usuario=self.usuario,
            token=pendiente.token,
        )
        
        self.cuenta_origen.refresh_from_db()
        self.cuenta_destino.refresh_from_db()
        
        self.assertEqual(transaccion.tipo, Transaccion.Tipo.TRANSFERENCIA_INTERNA)
        self.assertEqual(self.cuenta_origen.saldo, Decimal("0.00"))
        self.assertEqual(self.cuenta_destino.saldo, Decimal("700000.00"))
        
    def test_transferencia_interna_actualiza_saldos(self):
        pendiente = TransferService.crear_pendiente(
            usuario=self.usuario,
            tipo=TransferenciaPendiente.Tipo.INTERNA,
            monto=Decimal("100000.00"),
            cuenta_destino=self.cuenta_destino,
        )
        
        transaccion = TransferService.ejecutar_pendiente(
            usuario=self.usuario,
            token=pendiente.token,
        )
        
        self.cuenta_origen.refresh_from_db()
        self.cuenta_destino.refresh_from_db()
        
        self.assertEqual(self.cuenta_origen.saldo, Decimal("400000.00"))
        self.assertEqual(self.cuenta_destino.saldo, Decimal("300000.00"))
        self.assertEqual(transaccion.monto, Decimal("100000.00"))
        
    def test_transferencia_interna_crea_transaccion(self):
        pendiente = TransferService.crear_pendiente(
            usuario=self.usuario,
            tipo=TransferenciaPendiente.Tipo.INTERNA,
            monto=Decimal("100000.00"),
            cuenta_destino=self.cuenta_destino,
        )

        transaccion = TransferService.ejecutar_pendiente(
            usuario=self.usuario,
            token=pendiente.token,
        )

        self.assertEqual(Transaccion.objects.count(), 1)
        self.assertEqual(transaccion.cuenta_origen, self.cuenta_origen)
        self.assertEqual(transaccion.cuenta_destino, self.cuenta_destino)
        self.assertIsNone(transaccion.contacto)
        
    def test_transferencia_interna_guarda_snapshots(self):
        pendiente = TransferService.crear_pendiente(
            usuario=self.usuario,
            tipo=TransferenciaPendiente.Tipo.INTERNA,
            monto=Decimal("100000.00"),
            cuenta_destino=self.cuenta_destino,
        )

        transaccion = TransferService.ejecutar_pendiente(
            usuario=self.usuario,
            token=pendiente.token,
        )
        
        self.assertEqual(transaccion.origen_nombre, "Juan")
        self.assertEqual(transaccion.origen_apellido, "Pérez")
        self.assertEqual(transaccion.origen_numero_cuenta, "123-4567-8901")
        self.assertEqual(transaccion.destino_nombre, "María")
        self.assertEqual(transaccion.destino_apellido, "González")
        self.assertEqual(transaccion.destino_numero_cuenta, "987-6543-2109")
        
    def test_transferencia_externa_descuenta_saldo(self):
        pendiente = TransferService.crear_pendiente(
            usuario=self.usuario,
            tipo=TransferenciaPendiente.Tipo.EXTERNA,
            monto=Decimal("100000.00"),
            contacto=self.contacto,
        )

        transaccion = TransferService.ejecutar_pendiente(
            usuario=self.usuario,
            token=pendiente.token,
        )

        self.cuenta_origen.refresh_from_db()
        
        self.assertEqual(self.cuenta_origen.saldo, Decimal("400000.00"))
        self.assertEqual(transaccion.tipo, Transaccion.Tipo.TRANSFERENCIA_EXTERNA)
        self.assertEqual(transaccion.contacto, self.contacto)
        self.assertIsNone(transaccion.cuenta_destino)
        
    def test_transferencia_externa_guarda_snapshots(self):
        pendiente = TransferService.crear_pendiente(
            usuario=self.usuario,
            tipo=TransferenciaPendiente.Tipo.EXTERNA,
            monto=Decimal("100000.00"),
            contacto=self.contacto,
        )

        transaccion = TransferService.ejecutar_pendiente(
            usuario=self.usuario,
            token=pendiente.token,
        )
        
        self.assertEqual(transaccion.destino_nombre, "Pedro")
        self.assertEqual(transaccion.destino_apellido, "Ramírez")
        self.assertEqual(transaccion.destino_numero_cuenta, "111-2222-3333")
        self.assertEqual(transaccion.destino_banco, "Gringotts Wizarding Bank")
        
    def test_token_se_consume_despues_de_transferencia_exitosa(self):
        pendiente = TransferService.crear_pendiente(
            usuario=self.usuario,
            tipo=TransferenciaPendiente.Tipo.INTERNA,
            monto=Decimal("1000.00"),
            cuenta_destino=self.cuenta_destino,
        )

        TransferService.ejecutar_pendiente(
            usuario=self.usuario,
            token=pendiente.token,
        )

        pendiente.refresh_from_db()
        
        self.assertIsNotNone(pendiente.usado_en)
        
    def test_token_no_puede_utilizarse_dos_veces(self):
        pendiente = TransferService.crear_pendiente(
            usuario=self.usuario,
            tipo=TransferenciaPendiente.Tipo.INTERNA,
            monto=Decimal("1000.00"),
            cuenta_destino=self.cuenta_destino,
        )

        TransferService.ejecutar_pendiente(
            usuario=self.usuario,
            token=pendiente.token,
        )

        with self.assertRaises(TransferError):
            TransferService.ejecutar_pendiente(
                usuario=self.usuario,
                token=pendiente.token,
            )
            
        self.assertEqual(Transaccion.objects.count(), 1)
        
    def test_token_expirado_no_puede_utilizarse(self):
        pendiente = TransferService.crear_pendiente(
            usuario=self.usuario,
            tipo=TransferenciaPendiente.Tipo.INTERNA,
            monto=Decimal("1000.00"),
            cuenta_destino=self.cuenta_destino,
        )

        pendiente.expira_en = timezone.now() - timedelta(minutes=1)
        pendiente.save(update_fields=["expira_en"])

        with self.assertRaises(TransferError):
            TransferService.ejecutar_pendiente(
                usuario=self.usuario,
                token=pendiente.token,
            )

        self.cuenta_origen.refresh_from_db()
        
        self.assertEqual(self.cuenta_origen.saldo, Decimal("500000.00"))
        self.assertEqual(Transaccion.objects.count(), 0)
        
    def test_saldo_insuficiente_al_confirmar_no_modifica_cuentas(self):
        pendiente = TransferService.crear_pendiente(
            usuario=self.usuario,
            tipo=TransferenciaPendiente.Tipo.INTERNA,
            monto=Decimal("1000.00"),
            cuenta_destino=self.cuenta_destino,
        )

        self.cuenta_origen.saldo = Decimal("0.00")
        self.cuenta_origen.save(update_fields=["saldo"])

        with self.assertRaises(TransferError):
            TransferService.ejecutar_pendiente(
                usuario=self.usuario,
                token=pendiente.token,
            )

        self.cuenta_origen.refresh_from_db()
        self.cuenta_destino.refresh_from_db()
        
        self.assertEqual(self.cuenta_origen.saldo, Decimal("0.00"))
        self.assertEqual(self.cuenta_destino.saldo, Decimal("200000.00"))
        self.assertEqual(Transaccion.objects.count(), 0)
        
        pendiente.refresh_from_db()
        
        self.assertIsNone(pendiente.usado_en)