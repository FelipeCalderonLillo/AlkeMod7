from uuid import UUID

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import FormView

from core.forms.transfer import TransferForm
from core.models import TransferenciaPendiente
from core.services.transfers import TransferError, TransferService
from core.forms.deposit import DepositForm
from core.services.deposits import DepositError, DepositService



class TransferView(LoginRequiredMixin, FormView):
    template_name = "transactions/transfer.html"
    form_class = TransferForm
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["usuario"] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        try:
            pendiente = TransferService.crear_pendiente(
                usuario=self.request.user,
                tipo=form.cleaned_data["tipo"],
                monto=form.cleaned_data["monto"],
                cuenta_destino=form.cleaned_data.get("cuenta_destino"),
                contacto=form.cleaned_data.get("contacto"),
            )
        except TransferError as error:
            form.add_error(None, str(error))
            return self.form_invalid(form)
        
        return redirect(reverse("confirm_transfer", kwargs={"token": pendiente.token}))
    

class ConfirmTransferView(LoginRequiredMixin, View):
    template_name = "transactions/transfer_confirmation.html"
    
    def get_pendiente(self, token):
        return get_object_or_404(
            TransferenciaPendiente.objects.select_related(
                "cuenta_origen",
                "cuenta_destino",
                "cuenta_destino__usuario",
                "contacto",
            ),
            token=token,
            usuario=self.request.user,
        )
        
    def get(self, request, token):
        pendiente = self.get_pendiente(token)
        
        if pendiente.usado_en is not None:
            messages.error(request, "Esta transferencia ya fue confirmada.")
            return redirect("transfer")
        
        if timezone.now() >= pendiente.expira_en:
            messages.error(request, "La confirmación de esta transferencia ha expirado.")
            return redirect("transfer")
        
        return render(
            request,
            self.template_name,
            {"pendiente": pendiente}
        )
        
    def post(self, request, token):
        try:
            TransferService.ejecutar_pendiente(
                usuario=request.user,
                token=token,
            )
        except TransferError as error:
            messages.error(request, str(error))
            return redirect("transfer")
        
        messages.success(request, "La transferencia se realizó correctamente.")
        
        return redirect("history")
    
    
class DepositView(LoginRequiredMixin, FormView):
    template_name = "transactions/deposit.html"
    form_class = DepositForm
    
    def form_valid(self, form):
        try:
            DepositService.realizar_deposito(
                usuario=self.request.user,
                monto=form.cleaned_data["monto"],
            )
        except DepositError as error:
            form.add_error(None, str(error))
            return self.form_invalid(form)
        
        messages.success(
            self.request,
            "El depósito se realizó correctamente."
        )
        
        return redirect("history")