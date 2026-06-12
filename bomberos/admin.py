from django.contrib import admin
from .models import UserProfile, Tenant, Modulo, TenantModulo

@admin.register(UserProfile)
class AuthorAdmin(admin.ModelAdmin):
    pass

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'subdominio', 'creado_en', 'is_active')
    search_fields = ('nombre', 'subdominio')

@admin.register(Modulo)
class ModuloAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'clave', 'is_active')
    search_fields = ('nombre', 'clave')

@admin.register(TenantModulo)
class TenantModuloAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'modulo', 'fecha_activacion', 'is_active')
    list_filter = ('tenant', 'modulo', 'is_active')