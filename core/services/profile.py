from django.db import transaction



class ProfileService:
    @staticmethod
    @transaction.atomic
    def actualizar_perfil(
        *,
        usuario,
        username,
        trabajo,
        biografia,
    ):
        
        usuario.username = username
        usuario.save(update_fields=["username"])
        
        perfil = usuario.perfil
        
        perfil.trabajo = trabajo
        perfil.biografia = biografia
        perfil.save(update_fields=["trabajo", "biografia"])
        
        return usuario, perfil