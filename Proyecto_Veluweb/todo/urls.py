from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from . import views


urlpatterns = [
    # Home y clientes
    path('', views.home, name='home'),
    path('tabla/', views.tabla, name='tabla'),
    path('agregar/', views.agregar, name='agregar'),
    path('detalle/<int:pk>/', views.detalle_cliente, name='detalle_cliente'),
    path('editar/<int:cliente_id>/', views.editar, name='editar'),
    path('eliminar/<int:cliente_id>/', views.eliminar, name='eliminar'),

    # Autentificacion
    path('index/', views.index, name='index'),
    path('signIn/', views.signIn, name='signIn'),
    path('logout/', views.signout, name='logout'),
    path('roles/', views.roles, name='roles'),
    path('registro/', views.registro, name='registro'),

    # Recuperacion de contraseña
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
    path('productos/<int:pk>/', views.detalle_producto, name='detalle_producto'), 
    path('productos/<int:pk>/editar/', views.editar_producto, name='editar_producto'),
    path('productos/<int:pk>/toggle/', views.toggle_estado_producto, name='toggle_estado_producto'),
    path('productos/inactivos/', views.productos_inactivos, name='productos_inactivos'),



    # CRUD Facturas
    path('facturas/', views.lista_facturas, name='lista_facturas'),
    path('facturas/crear/', views.crear_factura, name='crear_factura'),
    path('ajax/obtener-precio/', views.obtener_precio_producto, name='obtener_precio_producto'),
    path('facturas/<int:pk>/', views.detalle_factura, name='detalle_factura'),
    path('facturas/<int:pk>/editar/', views.editar_factura, name='editar_factura'),
    path('facturas/<int:pk>/eliminar/', views.eliminar_factura, name='eliminar_factura'),
    path('estadisticas/', views.estadisticas_view, name='estadisticas'),
    path('productos/<int:pk>/editar/', views.editar_producto, name='editar_producto'),


    # Exportar a Excel
    path('estadisticas/exportar_excel/', views.exportar_excel, name='exportar_excel'),

    # Enviar factura por email
    path("facturas/<int:pk>/enviar/", views.enviar_factura_email, name="enviar_factura"),
]

# Para servir archivos multimedia en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
