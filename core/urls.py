from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from core.views.auth import RegistrationView, HomeView
from core.views.dashboard import DashboardView
from core.views.profile import ProfileView
from core.views.contacts import ContactView
from core.views.interests import InterestView
from core.views.history import HistoryView
from core.views.reports import ReportView
from core.views.transactions import TransferView, ConfirmTransferView, DepositView
from core.forms.authentication import ActiveUserAuthenticationForm


urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('registro/', RegistrationView.as_view(), name='registro'),
    path('login/', LoginView.as_view(template_name='auth/login.html', authentication_form=ActiveUserAuthenticationForm), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('contacts/', ContactView.as_view(), name='contacts'),
    path('interests/', InterestView.as_view(), name='interests'),
    path('history/', HistoryView.as_view(), name='history'),
    path('reports/', ReportView.as_view(), name='reports'),
    path('transfer/', TransferView.as_view(), name='transfer'),
    path('transfer/confirm/<uuid:token>/', ConfirmTransferView.as_view(), name='confirm_transfer'),
    path('deposit/', DepositView.as_view(), name='deposit'),
]
