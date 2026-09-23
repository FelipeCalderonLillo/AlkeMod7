from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from core.models import Contacto, CategoriaInteres, Cuenta, TransferenciaPendiente
from core.forms.registration import RegistrationForm
from core.services.registration import RegistrationService
from core.forms.profile import ProfileForm
from core.forms.contact import ContactForm
from core.forms.interest import InterestForm
from core.forms.reports import ReportForm
from core.forms.transfer import TransferForm


class RegistrationFormTests(TestCase):
    def _datos_validos(self):
        fecha_nacimiento = timezone.localdate().replace(
            year=timezone.localdate().year - 20
        )
        
        return {
            "username": "usuario",
            "password": "Password123!",
            "first_name": "juan",
            "last_name": "perez",
            "email": "usuario@example.com",
            "fecha_nacimiento": fecha_nacimiento,
            "trabajo": "Desarrollador",
            "biografia": "Una biografía de prueba",
        }
        
    def test_formulario_valido(self):
        form = RegistrationForm(data=self._datos_validos())
        
        self.assertTrue(form.is_valid())
        
    def test_normaliza_datos(self):
        datos = self._datos_validos()
        
        datos.update({
            "username": "  uSuArIo  ",
            "first_name": "  juan carlos  ",
            "last_name": "  perez gomez  ",
            "email": "  USUARIO@EXAMPLE.COM  ",
            "trabajo": "  Desarrollador  ",
            "biografia": "  Texto de prueba  ",
        })
        
        form = RegistrationForm(data=datos)
        
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["username"], "Usuario")
        self.assertEqual(form.cleaned_data["first_name"], "Juan Carlos")
        self.assertEqual(form.cleaned_data["last_name"], "Perez Gomez")
        self.assertEqual(form.cleaned_data["email"], "usuario@example.com")
        self.assertEqual(form.cleaned_data["trabajo"], "Desarrollador")
        self.assertEqual(form.cleaned_data["biografia"], "Texto de prueba")
        
    def test_rechaza_username_repetido(self):
        datos = self._datos_validos()
        
        RegistrationService.registrar_usuario(**datos)
        
        datos["email"] = "otro@example.com"
        
        form = RegistrationForm(data=datos)
        
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)
        
    def test_rechaza_email_repetido(self):
        datos = self._datos_validos()
        
        RegistrationService.registrar_usuario(**datos)
        
        datos["username"] = "otro_usuario"
        
        form = RegistrationForm(data=datos)
        
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        
    def test_rechaza_menor_de_18(self):
        datos = self._datos_validos()
        
        datos["fecha_nacimiento"] = (
            timezone.localdate().replace(
                year=timezone.localdate().year - 18
            ) + timedelta(days=1)
        )
        
        form = RegistrationForm(data=datos)
        
        self.assertFalse(form.is_valid())
        self.assertIn("fecha_nacimiento", form.errors)
        
    def test_rechaza_fecha_futura(self):
        datos = self._datos_validos()
        
        datos["fecha_nacimiento"] = (
            timezone.localdate() + timedelta(days=1)
        )
        
        form = RegistrationForm(data=datos)
        
        self.assertFalse(form.is_valid())
        self.assertIn("fecha_nacimiento", form.errors)
        
        
class ProfileFormTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username="Usuario",
            password="Password123!",
            first_name="Juan",
            last_name="Perez",
            email="usuario@example.com",
        )
        
    def _datos_validos(self):
        return {
            "username": "NuevoUsuario",
            "trabajo": "Desarrollador",
            "biografia": "Una biografía actualizada"
        }
    
    def test_formulario_valido(self):
        form = ProfileForm(
            data=self._datos_validos(),
            usuario=self.usuario
        )
        
        self.assertTrue(form.is_valid())
        
    def test_normaliza_datos(self):
        datos = self._datos_validos()
        
        datos.update({
            "username": " nUeVoUsUaRiO ",
            "trabajo": " Desarrollador web ",
            "biografia": " Nueva biografía "
        })
        
        form = ProfileForm(
            data=datos,
            usuario=self.usuario
        )
        
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["username"], "Nuevousuario")
        self.assertEqual(form.cleaned_data["trabajo"], "Desarrollador web")
        self.assertEqual(form.cleaned_data["biografia"], "Nueva biografía")
        
    def test_permite_conservar_el_mismo_username(self):
        datos = self._datos_validos()
        
        datos["username"] = "Usuario"
        
        form = ProfileForm(
            data=datos,
            usuario=self.usuario
        )
        
        self.assertTrue(form.is_valid())
        
    def test_rechaza_username_de_otro_usuario(self):
        User.objects.create_user(
            username="OtroUsuario",
            password="Password123!",
            email="otro@example.com"
        )
        
        datos = self._datos_validos()
        datos["username"] = "otroUsuario"
        
        form = ProfileForm(
            data=datos,
            usuario=self.usuario
        )
        
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)
        
    def test_no_contiene_campos_no_editables(self):
        form = ProfileForm(usuario=self.usuario)
        
        self.assertNotIn("first_name", form.fields)
        self.assertNotIn("last_name", form.fields)
        self.assertNotIn("fecha_nacimiento", form.fields)
        
        
class ContactFormTests(TestCase):
    def test_formulario_valido(self):
        form = ContactForm(
            data={
                "nombre": "Juan",
                "apellido": "Perez",
                "banco": Contacto.Banco.GRINGOTTS,
            }
        )
        
        self.assertTrue(form.is_valid())
        
    def test_nombre_y_apellido_se_normalizan(self):
        form = ContactForm(
            data={
                "nombre": "  juan  ",
                "apellido": "  perez  ",
                "banco": Contacto.Banco.GOLIATH,
            }
        )
        
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["nombre"], "Juan")
        self.assertEqual(form.cleaned_data["apellido"], "Perez")
        
    def test_formulario_no_contiene_usuario(self):
        form = ContactForm()
        
        self.assertNotIn("usuario", form.fields)
        
    def test_formulario_no_contiene_numero_de_cuenta(self):
        form = ContactForm()
        
        self.assertNotIn("numero_cuenta", form.fields)
        
    def test_banco_es_obligatorio(self):
        form = ContactForm(
            data={
                "nombre": "Juan",
                "apellido": "Perez",
                "banco": "",
            }
        )
        
        self.assertFalse(form.is_valid())
        self.assertIn("banco", form.errors)
        
        
class InterestFormTests(TestCase):
    def setUp(self):
        self.ahorro = CategoriaInteres.objects.create(
            nombre="Ahorro"
        )
        
        self.viajes = CategoriaInteres.objects.create(
            nombre="Viajes"
        )
        
    def test_formulario_valido_con_categoria_existente(self):
        form = InterestForm(data={"categoria": self.ahorro.id})
        
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["categoria"], self.ahorro)
        
    def test_formulario_invalido_sin_categoria(self):
        form = InterestForm(data={})
        
        self.assertFalse(form.is_valid())
        self.assertIn("categoria", form.errors)
        
    def test_formulario_rechaza_categoria_inexistente(self):
        form = InterestForm(data={"categoria": 9999})
        
        self.assertFalse(form.is_valid())
        self.assertIn("categoria", form.errors)
        
    def test_formulario_muestra_las_categorias_disponibles(self):
        form = InterestForm()
        
        opciones = list(form.fields["categoria"].queryset)
        
        self.assertEqual(opciones, [self.ahorro, self.viajes])
        
        
class ReportFormTests(TestCase):
    def test_formulario_valido_sin_fechas(self):
        form = ReportForm(data={})
        
        self.assertTrue(form.is_valid())
        
    def test_formulario_valido_con_periodo(self):
        form = ReportForm(
            data={
                "fecha_inicio": "2026-01-01",
                "fecha_fin": "2026-01-31",
            }
        )
        
        self.assertTrue(form.is_valid())
        
    def test_formulario_invalido_si_inicio_es_posterior_a_fin(self):
        form = ReportForm(
            data={
                "fecha_inicio": "2026-02-01",
                "fecha_fin": "2026-01-31",
            }
        )
        
        self.assertFalse(form.is_valid())
        self.assertTrue(form.non_field_errors())
        
    def test_formulario_invalido_con_fecha_incorrecta(self):
        form = ReportForm(
            data={
                "fecha_inicio": "fecha-invalida",
                "fecha_fin": "2026-01-31",
            }
        )
        
        self.assertFalse(form.is_valid())
        self.assertIn("fecha_inicio", form.errors)
        
    def test_formulario_permite_solo_fecha_inicio(self):
        form = ReportForm(
            data={
                "fecha_inicio": "2026-01-01",                
            }
        )
        
        self.assertTrue(form.is_valid())
        
    def test_formulario_permite_solo_fecha_fin(self):
        form = ReportForm(
            data={                
                "fecha_fin": "2026-01-31",
            }
        )
        
        self.assertTrue(form.is_valid())
        
        
class TransferFormTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username="usuario1",
            password="password123",
            first_name="Juan",
            last_name="Pérez",
        )
        
        self.otro_usuario = User.objects.create_user(
            username="usuario2",
            password="password123",
            first_name="María",
            last_name="González",
        )
        
        self.cuenta_usuario = Cuenta.objects.create(
            usuario=self.usuario,
            numero_cuenta="123-4567-8901",
            saldo=Decimal("500000.00"),
        )
        
        self.cuenta_otro_usuario = Cuenta.objects.create(
            usuario=self.otro_usuario,
            numero_cuenta="987-6543-2109",
            saldo=Decimal("500000.00"),
        )
        
        self.contacto_usuario = Contacto.objects.create(
            usuario=self.usuario,
            nombre="Pedro",
            apellido="Ramírez",
            banco=Contacto.Banco.GRINGOTTS,
            numero_cuenta="111-2222-3333",
        )

        self.contacto_otro_usuario = Contacto.objects.create(
            usuario=self.otro_usuario,
            nombre="Ana",
            apellido="López",
            banco=Contacto.Banco.GOLIATH,
            numero_cuenta="444-5555-6666",
        )
        
    def test_formulario_transferencia_interna_valido(self):
        form = TransferForm(
            data={
                "tipo": TransferenciaPendiente.Tipo.INTERNA,
                "monto": "1000",
                "cuenta_destino": self.cuenta_otro_usuario.pk,
                "contacto": "",
            },
            usuario=self.usuario,
        )
        
        self.assertTrue(form.is_valid())
        
    def test_formulario_transferencia_externa_valido(self):
        form = TransferForm(
            data={
                "tipo": TransferenciaPendiente.Tipo.EXTERNA,
                "monto": "1000",
                "cuenta_destino": "",
                "contacto": self.contacto_usuario.pk,
            },
            usuario=self.usuario,
        )
        
        self.assertTrue(form.is_valid())
        
    def test_monto_minimo_es_1000(self):
        form = TransferForm(
            data={
                "tipo": TransferenciaPendiente.Tipo.INTERNA,
                "monto": "999",
                "cuenta_destino": self.cuenta_otro_usuario.pk,
                "contacto": "",
            },
            usuario=self.usuario,
        )
        
        self.assertFalse(form.is_valid())
        self.assertIn("monto", form.errors)
        
    def test_monto_con_decimales_es_rechazado(self):
        form = TransferForm(
            data={
                "tipo": TransferenciaPendiente.Tipo.INTERNA,
                "monto": "1000.50",
                "cuenta_destino": self.cuenta_otro_usuario.pk,
                "contacto": "",
            },
            usuario=self.usuario,
        )
        
        self.assertFalse(form.is_valid())
        self.assertIn("monto", form.errors)
        
    def test_transferencia_interna_requiere_cuenta_destino(self):
        form = TransferForm(
            data={
                "tipo": TransferenciaPendiente.Tipo.INTERNA,
                "monto": "1000",
                "cuenta_destino": "",
                "contacto": "",
            },
            usuario=self.usuario,
        )
        
        self.assertFalse(form.is_valid())
        self.assertIn("cuenta_destino", form.errors)
        
    def test_transferencia_externa_requiere_contacto(self):
        form = TransferForm(
            data={
                "tipo": TransferenciaPendiente.Tipo.EXTERNA,
                "monto": "1000",
                "cuenta_destino": "",
                "contacto": "",
            },
            usuario=self.usuario,
        )
        
        self.assertFalse(form.is_valid())
        self.assertIn("contacto", form.errors)
        
    def test_transferencia_interna_no_acepta_contactos(self):
        form = TransferForm(
            data={
                "tipo": TransferenciaPendiente.Tipo.INTERNA,
                "monto": "1000",
                "cuenta_destino": self.cuenta_otro_usuario.pk,
                "contacto": self.contacto_usuario.pk,
            },
            usuario=self.usuario,
        )
        
        self.assertFalse(form.is_valid())
        self.assertIn("contacto", form.errors)
        
    def test_transferencia_externa_no_acepta_cuenta_destino(self):
        form = TransferForm(
            data={
                "tipo": TransferenciaPendiente.Tipo.EXTERNA,
                "monto": "1000",
                "cuenta_destino": self.cuenta_otro_usuario.pk,
                "contacto": self.contacto_usuario.pk,
            },
            usuario=self.usuario,
        )
        
        self.assertFalse(form.is_valid())
        self.assertIn("cuenta_destino", form.errors)
        
    def test_usuario_no_puede_seleccionar_su_propia_cuenta(self):
        form = TransferForm(
            data={
                "tipo": TransferenciaPendiente.Tipo.INTERNA,
                "monto": "1000",
                "cuenta_destino": self.cuenta_usuario.pk,
                "contacto": "",
            },
            usuario=self.usuario,
        )
        
        self.assertFalse(form.is_valid())
        self.assertIn("cuenta_destino", form.errors)
        
    def test_usuario_solo_ve_cuentas_de_otros_usuarios_activos(self):
        form = TransferForm(usuario=self.usuario)
        
        cuentas = list(form.fields["cuenta_destino"].queryset)
        
        self.assertIn(self.cuenta_otro_usuario, cuentas)
        self.assertNotIn(self.cuenta_usuario, cuentas)
        
    def test_usuario_solo_ve_sus_propios_contactos(self):
        form = TransferForm(usuario=self.usuario)
        
        contactos = list(form.fields["contacto"].queryset)
        
        self.assertIn(self.contacto_usuario, contactos)
        self.assertNotIn(self.contacto_otro_usuario, contactos)