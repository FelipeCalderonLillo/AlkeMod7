from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect




class ActiveUserMiddleware:
    """
    Impide que un usuario cuya cuenta fue desactivada continúe usando una sesión existente.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        rutas_excluidas = (
            "/admin/",
            "/login/",
            "/logout/",
            "/registro/",
        )
        
        if (
            request.user.is_authenticated
            and not request.user.is_active
            and not request.path.startswith(rutas_excluidas)
        ):
            logout(request)
            
            messages.error(
                request,
                "Tu cuenta está inactiva. "
                "Contacta a la administración para solicitar su reactivación.",
            )
            
            return redirect("login")
        
        return self.get_response(request)