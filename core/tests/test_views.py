from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User, Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import Cuenta, Perfil, Transaccion, Contacto, CategoriaInteres, TransferenciaPendiente
from core.views.auth import RegistrationView
from core.views.interests import InterestForm
from core.forms.registration import RegistrationForm
from core.forms.contact import ContactForm
from core.forms.transfer import TransferForm
from core.views.transactions import ConfirmTransferView, TransferView


class RegistrationViewTests(TestCase):
    
    def _datos_validos(self):
        today = timezone.localdate()
        
        return {
            "username": "usuario",
            "password": "Password123!",
            "first_name": "Juan",
            "last_name": "Perez",
            "email": "usuario@example.com",
            "fecha_nacimiento": date(
                today.year - 20,
                today.month,
                today.day,
            ),
            "trabajo": "Desarrollador",
            "biografia": "Biografía de prueba",
        }
        
    def test_get_registro_responde_correctamente(self):
        response = self.client.get(reverse("registro"))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auth/registro.html")
        
    def test_get_registro_contiene_registration_form(self):
        response = self.client.get(reverse("registro"))
        
        self.assertIsInstance(response.context["form"], RegistrationForm)
        
    def test_post_invalido_no_crea_usuario(self):
        datos = self._datos_validos()
        
        datos["email"] = ""
        
        response = self.client.post(reverse("registro"), data=datos)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 0)
        
    def test_post_valido_crea_usuario_perfil_y_cuenta(self):
        datos = self._datos_validos()
        
        response = self.client.post(reverse("registro"), data=datos)
        
        self.assertEqual(response.status_code, 302)
        
        usuario = User.objects.get(username="Usuario")
        
        self.assertTrue(Perfil.objects.filter(usuario=usuario).exists())
        self.assertTrue(Cuenta.objects.filter(usuario=usuario).exists())
        
    def test_post_valido_redirige_al_login(self):
        datos = self._datos_validos()
        
        response = self.client.post(reverse("registro"), data=datos)
        
        self.assertRedirects(response, reverse("login"))
        
    def test_post_valido_muestra_mensaje_de_exito(self):
        datos = self._datos_validos()
        
        response = self.client.post(reverse("registro"), data=datos)
        
        mensajes = list(response.wsgi_request._messages)
        
        self.assertEqual(len(mensajes), 1)
        self.assertEqual(str(mensajes[0]), "Registro completado correctamente. Ya puedes iniciar sesión.")
        
        
class AuthenticationViewTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username="Usuario",
            password="Password123!",
            first_name="Juan",
            last_name="Perez",
            email="usuario@example.com"
        )
        
        Perfil.objects.create(
            usuario=self.usuario,
            fecha_nacimiento=date(2000, 1, 1)
        )
        
        Cuenta.objects.create(
            usuario=self.usuario,
            numero_cuenta="123-4567-8901"
        )
        
    def test_get_login_responde_correctamente(self):
        response = self.client.get(reverse("login"))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auth/login.html")
        
    def test_invalido_no_autentica_usuario(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": "Usuario",
                "password": "PasswordIncorrecta!",
            }
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        
    def test_login_valido_autentica_y_redirige_al_dashboard(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": "Usuario",
                "password": "Password123!"
            },
        )
        
        self.assertRedirects(response, reverse("dashboard"))
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        
    def test_dashboard_requiere_autenticacion(self):
        response = self.client.get(reverse("dashboard"))
        
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")
        
    def test_usuario_autenticado_puede_acceder_al_dashboard(self):
        self.client.login(
            username="Usuario",
            password="Password123!"
        )
        
        response = self.client.get(reverse("dashboard"))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/dashboard.html")
        
    def test_logout_cierra_la_sesion_y_redirige(self):
        self.client.login(
            username="Usuario",
            password="Password123!"
        )
        
        self.assertTrue(self.client.session.get("_auth_user_id"))
        
        response = self.client.post(reverse("logout"))
        
        self.assertRedirects(response, "/")
        self.assertNotIn("_auth_user_id", self.client.session)
        
    def test_usuario_no_autenticado_no_puede_acceder_al_dashboard_despues_del_logout(self):
        self.client.login(
            username="Usuario",
            password="Password123!"
        )
        
        self.client.post(reverse("logout"))
        
        response = self.client.get(reverse("dashboard"))
        
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")
        
        
class ProfileViewTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username="UsuarioPrueba",
            password="password123",
            first_name="Juan",
            last_name="Pérez",
            email="juan@example.com",
        )

        Perfil.objects.create(
            usuario=self.usuario,
            fecha_nacimiento=date(1990, 5, 10),
            trabajo="Desarrollador",
            biografia="Biografía inicial",
        )
        
    def test_usuario_no_autenticado_es_redirigido_al_login(self):
        response = self.client.get("/profile/")
        
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)
        
    def test_usuario_autenticado_puede_acceder_al_perfil(self):
        self.client.login(
            username="UsuarioPrueba",
            password="password123",
        )
        
        response = self.client.get("/profile/")
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile/profile.html")
        
    def test_get_carga_datos_actuales_del_perfil(self):
        self.client.login(
            username="UsuarioPrueba",
            password="password123",
        )
        
        response = self.client.get("/profile/")
        
        form = response.context["form"]
        
        self.assertEqual(form.initial["username"], "UsuarioPrueba")
        self.assertEqual(form.initial["trabajo"], "Desarrollador")
        self.assertEqual(form.initial["biografia"], "Biografía inicial")
        
    def test_post_valido_actualiza_perfil(self):
        self.client.login(
            username="UsuarioPrueba",
            password="password123",
        )

        response = self.client.post(
            "/profile/",
            {
                "username": "NuevoUsuario",
                "trabajo": "Ingeniero de software",
                "biografia": "Nueva biografía",
            },
        )

        self.assertRedirects(response, "/profile/")

        self.usuario.refresh_from_db()
        self.usuario.perfil.refresh_from_db()

        self.assertEqual(self.usuario.username, "Nuevousuario")
        self.assertEqual(self.usuario.perfil.trabajo, "Ingeniero de software")
        self.assertEqual(self.usuario.perfil.biografia, "Nueva biografía")

    def test_post_invalido_no_modifica_perfil(self):
        self.client.login(username="UsuarioPrueba", password="password123")

        response = self.client.post(
            "/profile/",
            {
                "username": "",
                "trabajo": "Nuevo trabajo",
                "biografia": "Nueva biografía",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.usuario.refresh_from_db()
        self.usuario.perfil.refresh_from_db()

        self.assertEqual(self.usuario.username, "UsuarioPrueba")
        self.assertEqual(self.usuario.perfil.trabajo, "Desarrollador")
        self.assertEqual(self.usuario.perfil.biografia, "Biografía inicial")

    def test_formulario_no_contiene_datos_no_editables(self):
        self.client.login(
            username="UsuarioPrueba",
            password="password123",
        )

        response = self.client.get("/profile/")

        form = response.context["form"]

        self.assertNotIn("first_name", form.fields)
        self.assertNotIn("last_name", form.fields)
        self.assertNotIn("fecha_nacimiento", form.fields)
        
        
class DashboardViewTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username="UsuarioDashboard",
            password="Password123!",
            first_name="Juan",
            last_name="Perez",
            email="dashboard@example.com",
        )
        
        Perfil.objects.create(
            usuario=self.usuario,
            fecha_nacimiento=date(1990, 1, 1)
        )
        
        self.cuenta = Cuenta.objects.create(
            usuario=self.usuario,
            numero_cuenta="111-2222-3333",
            saldo=500000,
        )
        
    def test_dashboard_muestra_cuenta_del_usuario(self):
        self.client.login(
            username="UsuarioDashboard",
            password="Password123!",
        )
        
        response = self.client.get(reverse("dashboard"))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["cuenta"], self.cuenta)
        
    def estes_dashboard_muestra_saldo_de_la_cuenta(self):
        self.client.login(
            username="UsuarioDashboard",
            password="Password123!",
        )
        
        response = self.client.get(reverse("dashboard"))
        
        self.assertEqual(response.context["cuenta"].saldo, 500000)
        
    def test_dashboard_no_muestra_mas_de_tres_transacciones(self):
        otra_cuenta = Cuenta.objects.create(
            usuario=User.objects.create(
                username="OtroUsuario",
                password="Password123!",
            ),
            numero_cuenta="444-5555-6666",
            saldo=500000,
        )
        
        for i in range(4):
            Transaccion.objects.create(
                tipo=Transaccion.Tipo.TRANSFERENCIA_INTERNA,
                monto=1000,
                fecha_hora=timezone.now(),
                cuenta_origen=self.cuenta,
                cuenta_destino=otra_cuenta,
                origen_nombre="Juan",
                origen_apellido="Perez",
                origen_numero_cuenta=self.cuenta.numero_cuenta,
                destino_nombre="Otro",
                destino_apellido="Usuario",
                destino_numero_cuenta=otra_cuenta.numero_cuenta,
            )
            
        self.client.login(
            username="UsuarioDashboard",
            password="Password123!",
        )
        
        response = self.client.get(reverse("dashboard"))
        
        self.assertEqual(len(response.context["transacciones"]), 3)
        
    def test_dashboard_muestra_transacciones_donde_cuenta_es_origen(self):
        otra_cuenta = Cuenta.objects.create(
            usuario=User.objects.create_user(
                username="OtroUsuario",
                password="Password123!",
            ),
            numero_cuenta="444-5555-6666",
            saldo=500000,
        )
        
        transaccion = Transaccion.objects.create(
            tipo=Transaccion.Tipo.TRANSFERENCIA_INTERNA,
            monto=1000,
            fecha_hora=timezone.now(),
            cuenta_origen=self.cuenta,
            cuenta_destino=otra_cuenta,
            origen_nombre="Juan",
            origen_apellido="Perez",
            origen_numero_cuenta=self.cuenta.numero_cuenta,
            destino_nombre="Otro",
            destino_apellido="Usuario",
            destino_numero_cuenta=otra_cuenta.numero_cuenta,
        )
        
        self.client.login(
            username="UsuarioDashboard",
            password="Password123!",
        )
        
        response = self.client.get(reverse("dashboard"))
        
        self.assertIn(transaccion, response.context["transacciones"])
        
    def test_dashboard_muestra_transacciones_donde_cuenta_es_destino(self):
        otra_cuenta = Cuenta.objects.create(
            usuario=User.objects.create_user(
                username="OtroUsuario",
                password="Password123!",
            ),
            numero_cuenta="444-5555-6666",
            saldo=500000,
        )
        
        transaccion = Transaccion.objects.create(
            tipo=Transaccion.Tipo.TRANSFERENCIA_INTERNA,
            monto=1000,
            fecha_hora=timezone.now(),
            cuenta_origen=otra_cuenta,
            cuenta_destino=self.cuenta,
            origen_nombre="Otro",
            origen_apellido="Usuario",
            origen_numero_cuenta=otra_cuenta.numero_cuenta,
            destino_nombre="Juan",
            destino_apellido="Perez",
            destino_numero_cuenta=self.cuenta.numero_cuenta,
        )
        
        self.client.login(
            username="UsuarioDashboard",
            password="Password123!",
        )
        
        response = self.client.get(reverse("dashboard"))
        
        self.assertIn(transaccion, response.context["transacciones"])
        
        
class ContactViewTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username="Usuario",
            password="password123",
        )
        
        self.otro_usuario = User.objects.create_user(
            username="OtroUsuario",
            password="password123",
        )
        
        self.url = reverse("contacts")
        
    def test_usuario_no_autenticado_es_redirigido_al_login(self):
        response = self.client.get(self.url)
        
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")
        
    def test_usuario_autenticado_puede_acceder(self):
        self.client.login(
            username="Usuario",
            password="password123",
        )
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        
    def test_get_muestra_solo_los_contactos_del_usuario(self):
        Contacto.objects.create(
            usuario=self.usuario,
            nombre="Juan",
            apellido="Pérez",
            banco=Contacto.Banco.GRINGOTTS,
            numero_cuenta="111-1111-1111",
        )
        
        Contacto.objects.create(
            usuario=self.otro_usuario,
            nombre="Ana",
            apellido="Gómez",
            banco=Contacto.Banco.GOLIATH,
            numero_cuenta="222-2222-2222",
        )
        
        self.client.login(
            username="Usuario",
            password="password123"
        )
        
        response = self.client.get(self.url)
        
        contactos = response.context["contactos"]
        
        self.assertEqual(contactos.count(), 1)
        self.assertEqual(contactos.first().nombre, "Juan")
        
    def test_get_incluye_el_formulario(self):
        self.client.login(
            username="Usuario",
            password="password123"
        )
        
        response = self.client.get(self.url)
        
        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], ContactForm)
        
    def test_post_valido_crea_contacto(self):
        self.client.login(
            username="Usuario",
            password="password123"
        )
        
        response = self.client.post(
            self.url,
            {
                "nombre": "Juan",
                "apellido": "Pérez",
                "banco": Contacto.Banco.GRINGOTTS,
            },
        )
        
        self.assertRedirects(response, self.url)
        
        contacto = Contacto.objects.get()
        
        self.assertEqual(contacto.usuario, self.usuario)
        self.assertEqual(contacto.nombre, "Juan")
        self.assertEqual(contacto.apellido, "Pérez")
        
    def test_post_invalido_no_crea_contacto(self):
        self.client.login(
            username="Usuario",
            password="password123"
        )
        
        response = self.client.post(
            self.url,
            {
                "nombre": "",
                "apellido": "Pérez",
                "banco": Contacto.Banco.GRINGOTTS,
            },
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Contacto.objects.count(), 0)
        
    def test_contacto_creado_queda_asociado_al_usuario_autenticado(self):
        self.client.login(
            username="Usuario",
            password="password123"
        )
        
        self.client.post(
            self.url,
            {
                "nombre": "Juan",
                "apellido": "Pérez",
                "banco": Contacto.Banco.BANKS_BANK,
            },
        )
        
        contacto = Contacto.objects.get()
        
        self.assertEqual(contacto.usuario_id, self.usuario.id)
        self.assertNotEqual(contacto.usuario_id, self.otro_usuario.id)
        
        
class InterestsViewTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username="Usuario",
            password="password123",
        )
        
        self.otro_usuario = User.objects.create_user(
            username="OtroUsuario",
            password="password123",
        )
        
        self.ahorro = CategoriaInteres.objects.create(
            nombre="Ahorro"
        )
        
        self.inversiones = CategoriaInteres.objects.create(
            nombre="Inversiones"
        )
        
        self.viajes = CategoriaInteres.objects.create(
            nombre="Viajes"
        )
        
        self.url = reverse("interests")
        
    def test_usuario_no_autenticado_es_redirigido_al_login(self):
        response = self.client.get(self.url)
        
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")
        
    def test_usuario_autenticado_puede_acceder(self):
        self.client.login(
            username="Usuario",
            password="password123"
        )
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        
    def test_get_incluye_el_formulario(self):
        self.client.login(
            username="Usuario",
            password="password123",
        )
        
        response = self.client.get(self.url)
        
        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], InterestForm)
        
    def test_get_muestra_todas_las_categorias(self):
        self.client.login(
            username="Usuario",
            password="password123",
        )
        
        response = self.client.get(self.url)
        
        categorias = response.context["categorias"]
        
        self.assertEqual(categorias.count(), 3)
        
    def test_get_muestra_solo_las_suscripciones_del_usuario(self):
        self.usuario.categorias_interes.add(self.ahorro)
        self.otro_usuario.categorias_interes.add(self.viajes)
        
        self.client.login(
            username="Usuario",
            password="password123",
        )
        
        response = self.client.get(self.url)
        
        suscripciones = response.context["categorias_suscritas"]
        
        self.assertEqual(suscripciones.count(), 1)
        self.assertEqual(suscripciones.first(), self.ahorro)
        
    def test_post_agrega_categoria(self):
        self.client.login(
            username="Usuario",
            password="password123",
        )
        
        response = self.client.post(
            self.url,
            {
                "categoria": self.ahorro.id,
                "accion": "suscribir",
            },
        )
        
        self.assertRedirects(response, self.url)
        self.assertTrue(self.usuario.categorias_interes.filter(id=self.ahorro.id).exists())
        
    def test_post_desuscribir_elimina_suscripcion(self):
        self.usuario.categorias_interes.add(self.ahorro)
        
        self.client.login(
            username="Usuario",
            password="password123",
        )
        
        response = self.client.post(
            self.url,
            {
                "categoria": self.ahorro.id,
                "accion": "desuscribir",
            },
        )
        
        self.assertRedirects(response, self.url)
        self.assertFalse(self.usuario.categorias_interes.filter(id=self.ahorro.id).exists())
        
    def test_post_suscribir_no_afecta_a_otro_usuario(self):
        self.client.login(
            usename="Usuario",
            password="password123",
        )
        
        self.otro_usuario.categorias_interes.add(self.viajes)
        
        self.client.post(
            self.url,
            {
                "categoria": self.ahorro.id,
                "accion": "suscribir",
            },
        )
        
        self.assertFalse(self.otro_usuario.categorias_interes.filter(id=self.ahorro.id).exists())
        self.assertTrue(self.otro_usuario.categorias_interes.filter(id=self.viajes.id).exists())
        
    def test_post_con_categoria_invalida_no_modifica_suscripciones(self):
        self.client.login(
            username="Usuario",
            password="password123",
        )
        
        response = self.client.post(
            self.url,
            {
                "categoria": 9999,
                "accion": "suscribir",
            },
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.usuario.categorias_interes.count(), 0)
        
    def test_post_con_accion_invalida_no_modifica_suscripciones(self):
        self.client.login(
            username="Usuario",
            password="password123",
        )
        
        response = self.client.post(
            self.url,
            {
                "categoria": self.ahorro.id,
                "accion": "otra_accion",
            },
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.usuario.categorias_interes.count(), 0)
        
        
class HistoryViewTests(TestCase):
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
        
        self.url = reverse("history")
        
    def test_usuario_no_autenticado_es_redirigido_al_login(self):
        response = self.client.get(self.url)
        
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")
        
    def test_usuario_autenticado_puede_acceder(self):
        self.client.login(
            username="Usuario",
            password="password123",
        )
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        
    def test_get_incluye_las_transacciones_de_la_cuenta(self):
        transaccion = Transaccion.objects.create(
            tipo=Transaccion.Tipo.DEPOSITO,
            monto=Decimal("1000.00"),
            fecha_hora=timezone.now(),
            cuenta_destino=self.cuenta,
        )
        
        self.client.login(
            username="Usuario",
            password="password123",
        )
        
        response = self.client.get(self.url)
        
        transacciones = response.context["transacciones"]
        
        self.assertEqual(transacciones.count(), 1)
        self.assertEqual(transacciones.first(), transaccion)
        
    def test_get_incluye_transferencias_donde_usuario_es_origen(self):
        transaccion = Transaccion.objects.create(
            tipo=Transaccion.Tipo.TRANSFERENCIA_INTERNA,
            monto=Decimal("1000.00"),
            fecha_hora=timezone.now(),
            cuenta_origen=self.otra_cuenta,
            cuenta_destino=self.cuenta,
        )
        
        self.client.login(
            username="Usuario",
            password="password123",
        )
        
        response = self.client.get(self.url)
        
        transacciones = response.context["transacciones"]
        
        self.assertIn(transaccion, transacciones)
        
    def test_no_muestra_transacciones_de_otra_cuenta(self):
        transaccion = Transaccion.objects.create(
            tipo=Transaccion.Tipo.DEPOSITO,
            monto=Decimal("1000.00"),
            fecha_hora=timezone.now(),
            cuenta_destino=self.otra_cuenta,
        )
        
        self.client.login(
            username="Usuario",
            password="password123",
        )
        
        response = self.client.get(self.url)
        
        transacciones = response.context["transacciones"]
        
        self.assertNotIn(transaccion, transacciones)
        
    def test_transacciones_se_ordenan_de_la_mas_reciente_a_la_mas_antigua(self):
        ahora = timezone.now()
        
        antigua = Transaccion.objects.create(
            tipo=Transaccion.Tipo.DEPOSITO,
            monto=Decimal("1000.00"),
            fecha_hora=ahora - timezone.timedelta(days=2),
            cuenta_destino=self.cuenta,
        )
        
        reciente = Transaccion.objects.create(
            tipo=Transaccion.Tipo.DEPOSITO,
            monto=Decimal("1000.00"),
            fecha_hora=ahora,
            cuenta_destino=self.cuenta,
        )
        
        self.client.login(
            username="Usuario",
            password="password123",
        )
        
        response = self.client.get(self.url)
        
        transacciones = list(response.context["transacciones"])
        
        self.assertEqual(transacciones, [reciente, antigua])
        
        
class ReportsViewTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username="usuario1",
            password="password123",
            first_name="Juan",
            last_name="Pérez",
        )

        Perfil.objects.create(
            usuario=self.usuario,
            fecha_nacimiento=date(1990, 1, 1),
        )

        self.cuenta = Cuenta.objects.create(
            usuario=self.usuario,
            numero_cuenta="123-4567-8901",
        )
        
    def test_usuario_autenticado_puede_ver_reportes(self):
        self.client.login(username="usuario1", password="password123")
        
        response = self.client.get(reverse("reports"))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/reports.html")
        
    def test_usuario_no_autenticado_es_redirigido_desde_reportes(self):
        response = self.client.get(reverse("reports"))
        
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)
        
    def test_reportes_muestra_resumen(self):
        self.client.login(username="usuario1", password="password123")
        
        cuenta = self.usuario.cuenta
        
        Transaccion.objects.create(
            tipo=Transaccion.Tipo.DEPOSITO,
            monto="100000.00",
            fecha_hora=timezone.now(),
            cuenta_destino=cuenta,
        )
        
        response = self.client.get(reverse("reports"))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["resumen"]["ingresos"], 100000)
        self.assertEqual(response.context["resumen"]["cantidad_transacciones"], 1)
        
    def test_reportes_muestra_transacciones_del_usuario(self):
        self.client.login(username="usuario1", password="password123")
        
        cuenta = self.usuario.cuenta
        
        transaccion = Transaccion.objects.create(
            tipo=Transaccion.Tipo.DEPOSITO,
            monto="50000.00",
            fecha_hora=timezone.now(),
            cuenta_destino=cuenta,
        )
        
        response = self.client.get(reverse("reports"))
        
        self.assertIn(transaccion, response.context["transacciones"])
        
    def test_reportes_filtra_por_periodo(self):
        self.client.login(username="usuario1", password="password123")
        
        cuenta = self.usuario.cuenta
        ahora = timezone.now()
        
        transaccion_dentro = Transaccion.objects.create(
            tipo=Transaccion.Tipo.DEPOSITO,
            monto="50000.00",
            fecha_hora=ahora - timedelta(days=2),
            cuenta_destino=cuenta,
        )
        
        transaccion_fuera = Transaccion.objects.create(
            tipo=Transaccion.Tipo.DEPOSITO,
            monto="70000.00",
            fecha_hora=ahora - timedelta(days=10),
            cuenta_destino=cuenta,
        )
        
        fecha_inicio = (ahora - timedelta(days=3)).date()
        fecha_fin = ahora.date()
        
        response = self.client.get(
            reverse("reports"),
            {
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
            },
        )
        
        transacciones = response.context["transacciones"]
        
        self.assertIn(transaccion_dentro, transacciones)
        self.assertNotIn(transaccion_fuera, transacciones)
        
    def test_reportes_con_fechas_invalidas_no_aplica_filtro(self):
        self.client.login(username="usuario1", password="password123")
        
        response = self.client.get(
            reverse("reports"),
            {
                "fecha_inicio": "2026-09-20",
                "fecha_fin": "2026-09-10",
            },
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("transacciones", response.context)
        
        
class AdminTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin",
            password="admin123",
            email="admin@example.com",
            is_staff=True,
        )
        
        self.usuario = User.objects.create_user(
            username="usuario1",
            password="password123",
            email="usuario@example.com",
            first_name="Juan",
            last_name="Pérez",
        )
        
        Perfil.objects.create(
            usuario=self.usuario,
            fecha_nacimiento=date(1990, 1, 1),
        )
        
        self.cuenta = Cuenta.objects.create(
            usuario=self.usuario,
            numero_cuenta = "123-4567-8901",
        )
        
        self.transaccion = Transaccion.objects.create(
            tipo=Transaccion.Tipo.DEPOSITO,
            monto=1000,
            fecha_hora=timezone.now(),
            cuenta_destino=self.cuenta,
        )
        
        permisos = Permission.objects.filter(
            codename__in=[
                "view_user",
                "change_user",
                "view_perfil",
                "view_cuenta",
                "view_contacto",
                "view_transaccion",
                "view_categoriainteres",
                "add_categoriainteres",
                "change_categoriainteres",
                "delete_categoriainteres",
            ]
        )

        self.admin.user_permissions.set(permisos)
        
    def test_administrador_puede_acceder_al_panel_admin(self):
        self.client.login(
            username="admin",
            password="admin123",
        )
        
        response = self.client.get("/admin/")
        
        self.assertEqual(response.status_code, 200)
        
    def test_usuario_no_puede_acceder_al_panel_admin(self):
        self.client.login(
            username="usuario1",
            password="password123",
        )
        
        response = self.client.get("/admin/")
        
        self.assertEqual(response.status_code, 302)
        
    def test_administrador_puede_consultar_usuarios(self):
        self.client.login(
            username="admin",
            password="admin123",
        )
        
        response = self.client.get("/admin/auth/user/")
        
        self.assertEqual(response.status_code, 200)
        
    def test_administrador_puede_desactivar_usuario(self):
        self.client.login(
            username="admin",
            password="admin123",
        )
        
        response = self.client.post(
            f"/admin/auth/user/{self.usuario.pk}/change/",
            {
                "username": self.usuario.username,
                "first_name": self.usuario.first_name,
                "last_name": self.usuario.last_name,
                "email": self.usuario.email,
                "is_active": False,
                "password": self.usuario.password,
            },
        )
        
        self.assertEqual(response.status_code, 302)
        self.usuario.refresh_from_db()
        self.assertFalse(self.usuario.is_active)
        
    def test_administrador_no_puede_eliminar_usuario(self):
        self.client.login(
            username="admin",
            password="admin123",
        )
        
        response = self.client.get(
            f"/admin/auth/user/{self.usuario.pk}/delete/"
        )
        
        self.assertEqual(response.status_code, 403)
        
    def test_cuenta_es_solo_lectura_para_administrador(self):
        self.client.login(
            username="admin",
            password="admin123",
        )
        
        response = self.client.get(
            f"/admin/core/cuenta/"
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.cuenta.numero_cuenta)
        
    def test_transaccion_no_puede_crearse_desde_admin(self):
        self.client.login(
            username="admin",
            password="admin123",
        )
        
        response = self.client.get(
            "/admin/core/transaccion/add/"
        )
        
        self.assertEqual(response.status_code, 403)
        
    def test_transaccion_no_puede_eliminarse_desde_admin(self):
        self.client.login(
            username="admin",
            password="admin123",
        )
        
        response = self.client.get(
            f"/admin/core/transaccion/{self.transaccion.pk}/delete/"
        )
        
        self.assertEqual(response.status_code, 403)
        
    def test_administrador_debe_confirmar_antes_de_ver_historial(self):
        self.client.login(
            username="admin",
            password="admin123",
        )
        
        response = self.client.get(
            f"/admin/core/cuenta/{self.cuenta.pk}/auditoria/"
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Confirmar consulta de contraloría")
        self.assertContains(response, self.cuenta.numero_cuenta)
        
    def test_administrador_puede_confirmar_historial_despues_de_confirmar(self):
        self.client.login(
            username="admin",
            password="admin123",
        )
        
        response = self.client.post(
            f"/admin/core/cuenta/{self.cuenta.pk}/auditoria/"
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Historial de cuenta")
        self.assertContains(response, self.cuenta.numero_cuenta)
        self.assertContains(response, "Depósito")
        
    def test_usuario_normal_no_puede_consultar_contraloria(self):
        self.client.logout()
        
        self.client.login(
            username="usuario1",
            password="password123",
        )
        
        response = self.client.get(
            f"/admin/core/cuenta/{self.cuenta.pk}/auditoria/"
        )
        
        self.assertEqual(response.status_code, 302)
        
        
class TransferViewTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username="Usuario",
            password="password123",
            first_name="Juan",
            last_name="Pérez",
            email="usuario@example.com",
        )

        self.otro_usuario = User.objects.create_user(
            username="OtroUsuario",
            password="password123",
            first_name="Ana",
            last_name="Gómez",
            email="otro@example.com",
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

        self.contacto = Contacto.objects.create(
            usuario=self.usuario,
            nombre="Carlos",
            apellido="Pérez",
            banco=Contacto.Banco.GRINGOTTS,
            numero_cuenta="333-3333-3333",
        )

        self.url = reverse("transfer")

    def test_usuario_no_autenticado_es_redirigido_al_login(self):
        response = self.client.get(self.url)

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={self.url}",
        )

    def test_usuario_autenticado_puede_acceder_a_transferencias(self):
        self.client.login(
            username="Usuario",
            password="password123",
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "transactions/transfer.html",
        )

    def test_get_incluye_transfer_form(self):
        self.client.login(
            username="Usuario",
            password="password123",
        )

        response = self.client.get(self.url)

        self.assertIn("form", response.context)
        self.assertIsInstance(
            response.context["form"],
            TransferForm,
        )

    def test_get_formulario_muestra_cuentas_de_otros_usuarios(self):
        self.client.login(
            username="Usuario",
            password="password123",
        )

        response = self.client.get(self.url)

        form = response.context["form"]

        cuentas = list(
            form.fields["cuenta_destino"].queryset
        )

        self.assertIn(self.otra_cuenta, cuentas)
        self.assertNotIn(self.cuenta, cuentas)

    def test_get_formulario_muestra_solo_contactos_del_usuario(self):
        otro_contacto = Contacto.objects.create(
            usuario=self.otro_usuario,
            nombre="Pedro",
            apellido="Gómez",
            banco=Contacto.Banco.GOLIATH,
            numero_cuenta="444-4444-4444",
        )

        self.client.login(
            username="Usuario",
            password="password123",
        )

        response = self.client.get(self.url)

        form = response.context["form"]

        contactos = list(
            form.fields["contacto"].queryset
        )

        self.assertIn(self.contacto, contactos)
        self.assertNotIn(otro_contacto, contactos)

    def test_post_transferencia_interna_crea_pendiente_y_redirige_a_confirmacion(self):
        self.client.login(
            username="Usuario",
            password="password123",
        )

        response = self.client.post(
            self.url,
            {
                "tipo": TransferenciaPendiente.Tipo.INTERNA,
                "monto": "1000",
                "cuenta_destino": self.otra_cuenta.id,
                "contacto": "",
            },
        )

        self.assertEqual(response.status_code, 302)

        pendiente = TransferenciaPendiente.objects.get()

        self.assertRedirects(
            response,
            reverse(
                "confirm_transfer",
                kwargs={"token": pendiente.token},
            ),
        )

        self.assertEqual(
            pendiente.usuario,
            self.usuario,
        )

        self.assertEqual(
            pendiente.tipo,
            TransferenciaPendiente.Tipo.INTERNA,
        )

        self.assertEqual(
            pendiente.monto,
            Decimal("1000.00"),
        )

    def test_post_transferencia_externa_crea_pendiente_y_redirige_a_confirmacion(self):
        self.client.login(
            username="Usuario",
            password="password123",
        )

        response = self.client.post(
            self.url,
            {
                "tipo": TransferenciaPendiente.Tipo.EXTERNA,
                "monto": "1000",
                "cuenta_destino": "",
                "contacto": self.contacto.id,
            },
        )

        self.assertEqual(response.status_code, 302)

        pendiente = TransferenciaPendiente.objects.get()

        self.assertRedirects(
            response,
            reverse(
                "confirm_transfer",
                kwargs={"token": pendiente.token},
            ),
        )

        self.assertEqual(
            pendiente.usuario,
            self.usuario,
        )

        self.assertEqual(
            pendiente.tipo,
            TransferenciaPendiente.Tipo.EXTERNA,
        )

    def test_post_invalido_no_crea_transferencia_pendiente(self):
        self.client.login(
            username="Usuario",
            password="password123",
        )

        response = self.client.post(
            self.url,
            {
                "tipo": TransferenciaPendiente.Tipo.INTERNA,
                "monto": "500",
                "cuenta_destino": self.otra_cuenta.id,
                "contacto": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            TransferenciaPendiente.objects.count(),
            0,
        )

    def test_transferencia_interna_muestra_pantalla_de_confirmacion(self):
        self.client.login(
            username="Usuario",
            password="password123",
        )

        pendiente = TransferenciaPendiente.objects.create(
            usuario=self.usuario,
            tipo=TransferenciaPendiente.Tipo.INTERNA,
            monto=Decimal("1000.00"),
            cuenta_origen=self.cuenta,
            cuenta_destino=self.otra_cuenta,
            expira_en=timezone.now() + timedelta(minutes=5),
        )

        url = reverse(
            "confirm_transfer",
            kwargs={"token": pendiente.token},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(
            response,
            "transactions/transfer_confirmation.html",
        )

        self.assertEqual(
            response.context["pendiente"],
            pendiente,
        )

    def test_transferencia_externa_muestra_pantalla_de_confirmacion(self):
        self.client.login(
            username="Usuario",
            password="password123",
        )

        pendiente = TransferenciaPendiente.objects.create(
            usuario=self.usuario,
            tipo=TransferenciaPendiente.Tipo.EXTERNA,
            monto=Decimal("1000.00"),
            cuenta_origen=self.cuenta,
            contacto=self.contacto,
            expira_en=timezone.now() + timedelta(minutes=5),
        )

        url = reverse(
            "confirm_transfer",
            kwargs={"token": pendiente.token},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(
            response,
            "transactions/transfer_confirmation.html",
        )

        self.assertEqual(
            response.context["pendiente"],
            pendiente,
        )

    def test_usuario_no_autenticado_no_puede_acceder_a_confirmacion(self):
        pendiente = TransferenciaPendiente.objects.create(
            usuario=self.usuario,
            tipo=TransferenciaPendiente.Tipo.INTERNA,
            monto=Decimal("1000.00"),
            cuenta_origen=self.cuenta,
            cuenta_destino=self.otra_cuenta,
            expira_en=timezone.now() + timedelta(minutes=5),
        )

        url = reverse(
            "confirm_transfer",
            kwargs={"token": pendiente.token},
        )

        response = self.client.get(url)

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={url}",
        )

    def test_usuario_no_puede_ver_pendiente_de_otro_usuario(self):
        self.client.login(
            username="Usuario",
            password="password123",
        )

        pendiente = TransferenciaPendiente.objects.create(
            usuario=self.otro_usuario,
            tipo=TransferenciaPendiente.Tipo.INTERNA,
            monto=Decimal("1000.00"),
            cuenta_origen=self.otra_cuenta,
            cuenta_destino=self.cuenta,
            expira_en=timezone.now() + timedelta(minutes=5),
        )

        url = reverse(
            "confirm_transfer",
            kwargs={"token": pendiente.token},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_confirmacion_expirada_redirige_a_transferencia(self):
        self.client.login(
            username="Usuario",
            password="password123",
        )

        pendiente = TransferenciaPendiente.objects.create(
            usuario=self.usuario,
            tipo=TransferenciaPendiente.Tipo.INTERNA,
            monto=Decimal("1000.00"),
            cuenta_origen=self.cuenta,
            cuenta_destino=self.otra_cuenta,
            expira_en=timezone.now() - timedelta(minutes=1),
        )

        url = reverse(
            "confirm_transfer",
            kwargs={"token": pendiente.token},
        )

        response = self.client.get(url)

        self.assertRedirects(
            response,
            self.url,
        )

        mensajes = list(
            response.wsgi_request._messages
        )

        self.assertEqual(len(mensajes), 1)
        self.assertEqual(
            str(mensajes[0]),
            "La confirmación de esta transferencia ha expirado.",
        )

    def test_post_confirmacion_ejecuta_transferencia_y_redirige_a_historial(self):
        self.client.login(
            username="Usuario",
            password="password123",
        )

        saldo_origen_inicial = self.cuenta.saldo
        saldo_destino_inicial = self.otra_cuenta.saldo

        pendiente = TransferenciaPendiente.objects.create(
            usuario=self.usuario,
            tipo=TransferenciaPendiente.Tipo.INTERNA,
            monto=Decimal("1000.00"),
            cuenta_origen=self.cuenta,
            cuenta_destino=self.otra_cuenta,
            expira_en=timezone.now() + timedelta(minutes=5),
        )

        url = reverse(
            "confirm_transfer",
            kwargs={"token": pendiente.token},
        )

        response = self.client.post(url)

        self.assertRedirects(
            response,
            reverse("history"),
        )

        self.cuenta.refresh_from_db()
        self.otra_cuenta.refresh_from_db()
        pendiente.refresh_from_db()

        self.assertEqual(
            self.cuenta.saldo,
            saldo_origen_inicial - Decimal("1000.00"),
        )

        self.assertEqual(
            self.otra_cuenta.saldo,
            saldo_destino_inicial + Decimal("1000.00"),
        )

        self.assertIsNotNone(pendiente.usado_en)

        self.assertEqual(
            Transaccion.objects.count(),
            1,
        )

    def test_post_confirmacion_muestra_mensaje_de_exito(self):
        self.client.login(
            username="Usuario",
            password="password123",
        )

        pendiente = TransferenciaPendiente.objects.create(
            usuario=self.usuario,
            tipo=TransferenciaPendiente.Tipo.EXTERNA,
            monto=Decimal("1000.00"),
            cuenta_origen=self.cuenta,
            contacto=self.contacto,
            expira_en=timezone.now() + timedelta(minutes=5),
        )

        url = reverse(
            "confirm_transfer",
            kwargs={"token": pendiente.token},
        )

        response = self.client.post(url)

        mensajes = list(
            response.wsgi_request._messages
        )

        self.assertEqual(len(mensajes), 1)
        self.assertEqual(
            str(mensajes[0]),
            "La transferencia se realizó correctamente.",
        )

    def test_post_confirmacion_expirada_no_ejecuta_transferencia(self):
        self.client.login(
            username="Usuario",
            password="password123",
        )

        pendiente = TransferenciaPendiente.objects.create(
            usuario=self.usuario,
            tipo=TransferenciaPendiente.Tipo.INTERNA,
            monto=Decimal("1000.00"),
            cuenta_origen=self.cuenta,
            cuenta_destino=self.otra_cuenta,
            expira_en=timezone.now() - timedelta(minutes=1),
        )

        saldo_inicial = self.cuenta.saldo

        url = reverse(
            "confirm_transfer",
            kwargs={"token": pendiente.token},
        )

        response = self.client.post(url)

        self.assertRedirects(
            response,
            self.url,
        )

        self.cuenta.refresh_from_db()

        self.assertEqual(
            self.cuenta.saldo,
            saldo_inicial,
        )

        self.assertEqual(
            Transaccion.objects.count(),
            0,
        )