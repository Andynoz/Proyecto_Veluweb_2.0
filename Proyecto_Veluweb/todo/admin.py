
from django.contrib import admin
from .models import Cliente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'apellido', 'correo', 'telefono')
    search_fields = ('nombre', 'apellido', 'correo')
    list_filter = ('apellido',)