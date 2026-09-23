from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.urls import path, reverse
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404

from core.models import Perfil, Cuenta, Contacto, CategoriaInteres, Transaccion

# Register your models here.

admin.site.unregister(User)

@admin.register(User)
class UsuarioAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_active",
    )
    
    list_filter = ("is_active",)
    
    fieldsets = (
        ("Información de autenticación", {
            "fields": ("username", "password"),
        }),
        ("Información personal", {
            "fields": ("first_name", "last_name", "email"),
        }),
        ("Estado", {
            "fields": ("is_active",),
        }),
    )
    
    readonly_fields = (
        "username",
        "first_name",
        "last_name",
        "email",
    )
    
    #No se puede desactivar administrativo mientras tenga privilegios.
    def save_model(self, request, obj, form, change):
        if change:
            usuario_original = User.objects.get(pk=obj.pk)
            
            if (
                usuario_original.is_staff
                or usuario_original.is_superuser
            ) and not obj.is_active:
                obj.is_active = True
                
        super().save_model(request, obj, form, change)
    
    def has_delete_permission(self, request, obj =None):
        return False
    
    
@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = (
        "usuario",
        "fecha_nacimiento",
        "trabajo",
    )
    
    search_fields = (
        "usuario__username",
        "usuario__email",
    )
    
    readonly_fields = (
        "usuario",
        "trabajo",
        "fecha_nacimiento",
        "biografia",
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj =None):
        return False
    
    def has_delete_permission(self, request, obj =None):
        return False
    
    
@admin.register(Cuenta)
class CuentaAdmin(admin.ModelAdmin):
    list_display = (
        "numero_cuenta",
        "usuario",
        "saldo",
        "creada_en",
        "historial_contraloria",
    )
    
    search_fields = (
        "numero_cuenta",
        "usuario__username",
        "usuario__email",
    )
    
    readonly_fields = (
        "usuario",
        "numero_cuenta",
        "saldo",
        "creada_en",
    )
    
    def get_urls(self):
        urls = super().get_urls()
        
        custom_urls = [
            path(
                "<path:object_id>/auditoria/",
                self.admin_site.admin_view(self.auditoria_view),
                name="core_cuenta_auditoria",
            ),
        ]
        
        return custom_urls + urls
    
    def historial_contraloria(self, obj):
        url = reverse(
            "admin:core_cuenta_auditoria",
            args=[obj.pk],
        )
        
        return format_html(
            '<a href="{}">Ver historial</a>',
            url,
        )
        
    historial_contraloria.short_description = "Contraloría"
    
    def auditoria_view(self, request, object_id):
        cuenta = get_object_or_404(Cuenta, pk=object_id)
        
        if not self.has_view_permission(request, cuenta):
            raise PermissionDenied
        
        if request.method == "POST":
            transacciones = (
                Transaccion.objects.filter(
                    Q(cuenta_origen=cuenta) |
                    Q(cuenta_destino=cuenta)
                ).order_by("-fecha_hora")
            )
            
            context = {
                **self.admin_site.each_context(request),
                "title": "Historial de cuenta",
                "cuenta": cuenta,
                "transacciones": transacciones,
            }
            
            return TemplateResponse(
                request,
                "admin/core/cuenta/auditoria_historial.html",
                context,
            )
            
        context = {
            **self.admin_site.each_context(request),
            "title": "Confirmar consulta de contraloría",
            "cuenta": cuenta,
        }
        
        return TemplateResponse(
            request,
            "admin/core/cuenta/confirmar_auditoria.html",
            context,
        )
        
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj =None):
        return False
    
    def has_delete_permission(self, request, obj =None):
        return False
    
    
@admin.register(Contacto)
class ContactoAdmin(admin.ModelAdmin):
    list_display = (
        "usuario",
        "nombre",
        "apellido",
        "banco",
        "numero_cuenta",
    )
    
    search_fields = (
        "usuario__username",
        "nombre",
        "apellido",
        "numero_cuenta",
    )
    
    readonly_fields = (
        "usuario",
        "nombre",
        "apellido",
        "banco",
        "numero_cuenta",
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj =None):
        return False
    
    def has_delete_permission(self, request, obj =None):
        return False
    
    
@admin.register(Transaccion)
class TransaccionAdmin(admin.ModelAdmin):
    list_display = (
        "tipo",
        "monto",
        "fecha_hora",
        "cuenta_origen",
        "cuenta_destino",
        "contacto",
    )
    
    list_filter = ("tipo",)
    
    search_fields = (
        "origen_nombre",
        "origen_apellido",
        "origen_numero_cuenta",
        "destino_nombre",
        "destino_apellido",
        "destino_numero_cuenta",
    )
    
    readonly_fields = (
        "tipo",
        "monto",
        "fecha_hora",
        "cuenta_origen",
        "cuenta_destino",
        "contacto",
        "origen_nombre",
        "origen_apellido",
        "origen_numero_cuenta",
        "destino_nombre",
        "destino_apellido",
        "destino_numero_cuenta",
        "destino_banco",
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj =None):
        return False
    
    def has_delete_permission(self, request, obj =None):
        return False
    
    
@admin.register(CategoriaInteres)
class CategoriaInteresAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)