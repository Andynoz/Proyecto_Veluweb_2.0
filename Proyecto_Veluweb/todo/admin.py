
from django.contrib import admin
from .models import Cliente ,Producto

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'apellido', 'correo', 'telefono')
    search_fields = ('nombre', 'apellido', 'correo')
    list_filter = ('apellido',)
    
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'precio', 'stock', 'get_estado_display')
    search_fields = ('codigo', 'nombre')