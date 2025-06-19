
from django.urls import path
from django.conf.urls.static import static
from . import views
from django.conf import settings

urlpatterns = [
    path('', views.home, name='home'),
    path('tabla/', views.tabla, name='tabla'),
    path('agregar/', views.agregar, name='agregar'),
    path('editar/<int:cliente_id>/', views.editar, name='editar'),
    path('eliminar/<int:cliente_id>/', views.eliminar, name='eliminar'),
    path('index/', views.index, name='index'),
    path('signIn/', views.signIn, name='signIn'),
    path('logout/', views.signout, name='logout'),
    path('registro/', views.registro, name='registro'),
    path('recuperacion/', views.recuperacion, name='recuperacion'),
    path('recuperar/', views.recuperar_contrasena, name='recuperar_contrasena'),
    path('recuperacion/enviado/', views.correo_enviado, name='correo_enviado'),
    path('recuperacion/confirmar/', views.confirmar_contrasena, name='confirmar_contrasena'),
    path('recuperacion/completado/', views.contrasena_cambiada, name='contrasena_cambiada'),
    path('verificar-codigo/', views.verificar_codigo, name='verificar_codigo'),
    path('nueva-contrasena/', views.nueva_contrasena, name='nueva_contrasena'),
    path('bienvenida/', views.bienvenida, name='bienvenida'),
# CRUD Productos
    path('productos/', views.productos_index, name='productos_index'),
    path('productos/crear/', views.crear_producto, name='crear_producto'),
    path('productos/editar/<int:pk>/', views.editar_producto, name='editar_producto'),
    path('productos/eliminar/<int:pk>/', views.eliminar_producto, name='eliminar_producto'),
# CRUD Facturas
    path('facturas/', views.lista_facturas, name='lista_facturas'),
    path('facturas/crear/', views.crear_factura, name='crear_factura'),
    path('facturas/<int:pk>/', views.detalle_factura, name='detalle_factura'),
    path('facturas/<int:pk>/editar/', views.editar_factura, name='editar_factura'),
    path('facturas/<int:pk>/eliminar/', views.eliminar_factura, name='eliminar_factura'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)