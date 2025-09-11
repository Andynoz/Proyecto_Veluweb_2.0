from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from .models import Cliente, Producto, Factura, DetalleFactura
from .forms import ClienteForm
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User, Group
from django.contrib import messages
from .models import PasswordResetToken
from django.utils import timezone
from django.core.mail import send_mail
from datetime import timedelta, date, datetime
from django.db import IntegrityError
from django.contrib.auth.backends import ModelBackend
from .forms import ProductoForm
from .forms import FacturaForm, DetalleFacturaFormSet, DetalleFacturaForm
from django.forms import modelformset_factory
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.core.cache import cache
import random
from django.db.models import Q, Sum, Count, F
from django.db.models.functions import TruncDay
import json
from django.views.decorators.http import require_POST
from .models import Producto, Factura, DetalleFactura, Cliente
from .forms import ProductoForm
import openpyxl
from openpyxl import Workbook
from openpyxl.chart import BarChart, PieChart, Reference
from openpyxl.drawing.image import Image as ExcelImage
import io
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.text import RichText
from openpyxl.drawing.text import Paragraph, ParagraphProperties, CharacterProperties
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.contrib import messages
from io import BytesIO
from xhtml2pdf import pisa
from django.contrib.auth.decorators import permission_required
from django.forms.models import inlineformset_factory
from .forms import FacturaForm, DetalleFacturaFormSet






@login_required
def estadisticas_view(request):
    end_date_str = request.GET.get('fecha_fin')
    start_date_str = request.GET.get('fecha_inicio')

    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    else:
        end_date = timezone.now().date()

    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    else:
        start_date = end_date - timedelta(days=29)

    if start_date > end_date:
        messages.warning(request, "La fecha de inicio no puede ser posterior a la fecha de fin.")
        start_date = end_date - timedelta(days=29)

    ventas_totales = Factura.objects.filter(
        fecha__date__range=[start_date, end_date],
        estado='PAGADA'
    ).aggregate(total=Sum('monto_total'))['total'] or 0

    num_facturas = Factura.objects.filter(
        fecha__date__range=[start_date, end_date]
    ).count()

    estado_facturas = Factura.objects.filter(
        fecha__date__range=[start_date, end_date]
    ).values('estado').annotate(count=Count('id')).order_by('estado')

    estado_dict = {item['estado']: item['count'] for item in estado_facturas}
    
    estados_data = {
        'PAGADA': estado_dict.get('PAGADA', 0),
        'PENDIENTE': estado_dict.get('PENDIENTE', 0),
        'VENCIDA': estado_dict.get('VENCIDA', 0),
    }

    # Para mostrar labels legibles en el frontend
    estados_labels = ['Pagadas', 'Pendientes', 'Vencidas']
    estados_valores = [estados_data['PAGADA'], estados_data['PENDIENTE'], estados_data['VENCIDA']]

    # Top productos vendidos (solo de facturas PAGADAS)
    top_productos_vendidos = DetalleFactura.objects.filter(
        factura__fecha__date__range=[start_date, end_date],
        factura__estado='PAGADA'  # ← SOLO FACTURAS PAGADAS
    ).values('producto__nombre').annotate(
        total_cantidad=Sum('cantidad')
    ).order_by('-total_cantidad')[:5]

    top_productos_labels = [item['producto__nombre'] for item in top_productos_vendidos]
    top_productos_data = [float(item['total_cantidad']) for item in top_productos_vendidos]

    producto_mas_vendido_nombre = top_productos_labels[0] if top_productos_labels else "N/A"

    # Ventas diarias (solo facturas PAGADAS)
    ventas_diarias = Factura.objects.filter(
        fecha__date__range=[start_date, end_date],
        estado='PAGADA'  # ← SOLO FACTURAS PAGADAS
    ).annotate(
        day=TruncDay('fecha')
    ).values('day').annotate(
        total_dia=Sum('monto_total')
    ).order_by('day')

    date_range = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
    ventas_diarias_dict = {item['day'].date(): float(item['total_dia']) for item in ventas_diarias}

    tendencia_ventas_labels = [d.strftime('%Y-%m-%d') for d in date_range]
    tendencia_ventas_data = [ventas_diarias_dict.get(d, 0) for d in date_range]

    total_clientes = Cliente.objects.count()
    total_productos = Producto.objects.count()
    ultima_factura = Factura.objects.order_by('-fecha').first()

    # NUEVOS DATOS: Estadísticas adicionales por estado
    facturas_pagadas_monto = estados_data['PAGADA'] * (ventas_totales / estados_data['PAGADA'] if estados_data['PAGADA'] > 0 else 0)
    facturas_pendientes_monto = Factura.objects.filter(
        fecha__date__range=[start_date, end_date],
        estado='PENDIENTE'
    ).aggregate(total=Sum('monto_total'))['total'] or 0
    
    facturas_vencidas_monto = Factura.objects.filter(
        fecha__date__range=[start_date, end_date],
        estado='VENCIDA'
    ).aggregate(total=Sum('monto_total'))['total'] or 0

    context = {
        'ventas_totales': ventas_totales,
        'num_facturas': num_facturas,
        
        # Estados de facturas (corregido)
        'estados_data': estados_data,
        'estados_labels': json.dumps(estados_labels),
        'estados_valores': json.dumps(estados_valores),
        
        # Productos
        'top_productos_labels': json.dumps(top_productos_labels),
        'top_productos_data': json.dumps(top_productos_data),
        'producto_mas_vendido_nombre': producto_mas_vendido_nombre,
        
        # Tendencias
        'tendencia_ventas_labels': json.dumps(tendencia_ventas_labels),
        'tendencia_ventas_data': json.dumps(tendencia_ventas_data),
        
        # Fechas
        'fecha_inicio_str': start_date.strftime('%Y-%m-%d'),
        'fecha_fin_str': end_date.strftime('%Y-%m-%d'),
        
        # Datos generales
        'total_clientes': total_clientes,
        'total_productos': total_productos,
        'ultima_factura': ultima_factura,
        
        # NUEVOS: Desglose por estado
        'facturas_pendientes_monto': facturas_pendientes_monto,
        'facturas_vencidas_monto': facturas_vencidas_monto,
    }

    return render(request, 'estadisticas/estadisticas.html', context)

def home(request):
    return render(request, 'todo/home.html')  

@login_required
@permission_required("todo.view_cliente", raise_exception=True)
def tabla(request):
    query = request.GET.get('buscar')

    if query:
        lista_clientes = Cliente.objects.filter(
            Q(nombre__icontains=query) |
            Q(apellido__icontains=query) |
            Q(correo__icontains=query) |
            Q(telefono__icontains=query)
        ).order_by('id')
    else:
        lista_clientes = Cliente.objects.all().order_by('id')

    paginator = Paginator(lista_clientes, 5)
    pagina = request.GET.get('page')
    page_obj = paginator.get_page(pagina)

    return render(request, 'todo/tabla.html', {
        'page_obj': page_obj,
        'query': query
    })

@login_required
@permission_required("todo.add_cliente", raise_exception=True)
def agregar(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente registrado correctamente.')
            return redirect('tabla')        
    else:
        form = ClienteForm()
    
    return render(request, 'todo/agregar.html', {'form': form})

@login_required
@permission_required("todo.change_cliente", raise_exception=True)
def editar(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            if form.has_changed():
                form.save()
                messages.success(request, 'Cliente actualizado correctamente.')
            else:
                messages.info(request, 'No se realizaron cambios en el cliente.')      
        return redirect('tabla')
    
    else:
        form = ClienteForm(instance=cliente)
    
    return render(request, 'todo/editar.html', {'form': form})



@login_required
@permission_required("todo.delete_cliente", raise_exception=True)
def eliminar(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    cliente.delete()
    return redirect('tabla')

@login_required
def index(request):
    context = {
        'total_clientes': Cliente.objects.count(),
        'total_productos': Producto.objects.filter(estado=True).count(),
        'ventas_mes': Factura.objects.filter(
            fecha__month=timezone.now().month,
            fecha__year=timezone.now().year
        ).count(),
        'stock_bajo': Producto.objects.filter(
            stock__lte=5, estado=True
        ).count(),
    }
    return render(request, 'todo/index.html', context)



def registro(request):  # Vista para registrar un nuevo usuario
    if request.method == 'GET':
        return render(request, 'todo/registro.html', {
            'form': UserCreationForm()
        })
    else:
        if request.POST['password1'] == request.POST['password2']:
            try:
                email = request.POST['email']
                user = User.objects.create_user(
                    username=email,
                    email=email,                    
                    password=request.POST['password1'])
                user.save()
                login(request, user)
                return redirect('signIn')
            except IntegrityError:
                return render(request, 'todo/registro.html', {
                    'form': UserCreationForm(),
                    'error': 'El usuario ya existe'
                })
        return render(request, 'todo/registro.html', {
                    'form': UserCreationForm(),
                    'error': 'Las contraseñas no coinciden'
        })

def signout(request): # Vista para cerrar sesión
    logout(request)
    return redirect('home')
    
    
def signIn(request): #Vista para iniciar sesión
    if request.method == 'GET':
        return render(request, 'todo/signIn.html', {
            'form': AuthenticationForm()
        })
    else:
        user = authenticate(
            request, username=request.POST['email'],
            password=request.POST['password'])
        
        if user is None:
            return render(request, 'todo/signIn.html', {
                'form': AuthenticationForm,
                'error': 'Usuario o contraseña incorrectos'
            })
        else:
            login(request, user)
            return redirect('index')
        
        
def enviar_codigo_reset(user):
    codigo = generar_codigo_corto()

    token = PasswordResetToken.objects.create(
        user=user,
        token=codigo,  # Aquí guardas el código corto
        expires_at=timezone.now() + timedelta(minutes=10)
    )
    
    asunto = 'Código de recuperación de contraseña'
    mensaje = f'Hola {user.username}, tu código para restablecer tu contraseña es:\n\n{codigo}'
    remitente = 'andynox27v@gmail.com'
    destinatario = [user.email]
    
    send_mail(asunto, mensaje, remitente, destinatario)

def recuperacion(request):
    if request.method == 'POST':
        correo = request.POST.get('correo')
        try:
            user = User.objects.get(email=correo)
            enviar_codigo_reset(user)
            messages.success(request, 'Se ha enviado un código de recuperación a tu correo.')
            return redirect('verificar_codigo')
        except User.DoesNotExist:
            messages.error(request, 'No se encontró una cuenta con ese correo.')
    return render(request, 'todo/recuperacion.html')

def recuperar_contrasena(request):
    return render(request, 'todo/recuperar_contrasena.html')

def correo_enviado(request):
    return render(request, 'todo/correo_enviado.html')

def confirmar_contrasena(request):
    return render(request, 'todo/confirmar_contrasena.html')

def contrasena_cambiada(request):
    return render(request, 'todo/contrasena_cambiada.html')

def verificar_codigo(request):
    if request.method == 'POST':
        token = request.POST.get('token')
        try:
            token_obj = PasswordResetToken.objects.get(token=token)
            if token_obj.is_valid():
                request.session['reset_user_id'] = token_obj.user.id
                return redirect('nueva_contrasena')
            else:
                messages.error(request, 'El código ha expirado.')
        except PasswordResetToken.DoesNotExist:
            messages.error(request, 'Código inválido.')
    return render(request, 'todo/verificar_codigo.html')

def nueva_contrasena(request):
    user_id = request.session.get('reset_user_id')
    if not user_id:
        return redirect('recuperacion')

    user = User.objects.get(id=user_id)
    if request.method == 'POST':
        nueva = request.POST.get('password')
        user.set_password(nueva)
        user.save()
        del request.session['reset_user_id']
        messages.success(request, 'Contraseña actualizada correctamente.')
        return redirect('signIn')
    
    return render(request, 'todo/nueva_contrasena.html')

def generar_codigo_corto():
    return str(random.randint(100000,999999))

def guardar_codigo_usuario(email):
    codigo = generar_codigo_corto()
    cache.set(f"codigo_recuperacion_{email}", codigo, timeout=300)
    return codigo


def bienvenida(request):
    return render(request, 'bienvenida.html')


#PRODUCTOS

@login_required
@permission_required("todo.view_producto", raise_exception=True)
def productos_index(request):
    query = request.GET.get("q", "").strip()  # ahora usa 'q' como en el input
    
    if query:
        productos_lista = Producto.objects.filter(
            Q(nombre__icontains=query) | Q(descripcion__istartswith=query),
            estado = True
        ).order_by('-id')
    else:
        productos_lista = Producto.objects.filter(estado=True).order_by('-id')

    paginator = Paginator(productos_lista, 5)
    pagina = request.GET.get('page')
    page_obj = paginator.get_page(pagina)

    return render(request, 'productos/index.html', {
        'page_obj': page_obj,
        'q': query  # para que el input mantenga el valor buscado
    })


# DETALLE DE PRODUCTO
@login_required
@permission_required("todo.view_producto", raise_exception=True)
def detalle_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    return render(request, 'productos/detalle.html', {'producto': producto})


# CREAR PRODUCTO
@login_required
@permission_required("todo.add_producto", raise_exception=True)
def crear_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto creado')
            return redirect('productos_index')
    else:
        form = ProductoForm()
    return render(request, 'productos/crear.html', {'form': form})


# LISTAR PRODUCTOS INACTIVOS
@login_required
@permission_required("todo.view_producto", raise_exception=True)
def productos_inactivos(request):
    query = request.GET.get("q", "").strip()
    
    if query:
        productos_inactivos = Producto.objects.filter(
            Q(nombre__icontains=query) | Q(descripcion__istartswith=query),
            estado=False
        ).order_by('-id')
    else:
        productos_inactivos = Producto.objects.filter(estado=False).order_by('-id')

    paginator = Paginator(productos_inactivos, 5)
    pagina = request.GET.get('page')
    page_obj = paginator.get_page(pagina)

    return render(request, 'productos/inactivos.html', {
        'page_obj': page_obj,
        'q': query
    })

# ACTIVAR PRODUCTO
@login_required
@permission_required('productos.change_producto', raise_exception=True)
def activar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == "POST":
        producto.estado = True
        producto.save()
        return redirect('productos_inactivos')
    return render(request, "productos/activar_producto.html", {"producto": producto})

# DESHABILITAR PRODUCTO
@login_required
@permission_required('productos.delete_producto', raise_exception=True)
def deshabilitar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == "POST":
        producto.estado = False
        producto.save()
        return redirect('productos_index')
    return render(request, "productos/deshabilitar.html", {"producto": producto})




# EDITAR PRODUCTO
@login_required
@permission_required("todo.change_producto", raise_exception=True)
def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado')
            return redirect('productos_index')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'productos/editar.html', {'form': form, 'producto': producto})


#FACTURAS

@login_required
@permission_required("todo.view_factura", raise_exception=True)
def lista_facturas(request):
    query = request.GET.get('buscar')

    if query:
        facturas_list = Factura.objects.filter(
            Q(cliente__nombre__icontains=query) |
            Q(cliente__apellido__icontains=query) |
            Q(fecha__icontains=query)
        ).order_by('-fecha')
    else:
        facturas_list = Factura.objects.all().order_by('-fecha')

    paginator = Paginator(facturas_list, 5)
    pagina = request.GET.get('page')
    page_obj = paginator.get_page(pagina)

    return render(request, 'facturas/lista.html', {
        'page_obj': page_obj,
        'query': query
    })

@login_required
@permission_required("todo.add_factura", raise_exception=True)
def crear_factura(request):
    DetalleFormSet = inlineformset_factory(
        Factura, DetalleFactura,
        form=DetalleFacturaForm,
        extra=1, can_delete=True
    )

    if request.method == "POST":
        factura_form = FacturaForm(request.POST, request.FILES)
        if factura_form.is_valid():
            factura = factura_form.save(commit=False)
            factura.creado_por = request.user
            factura.save()

            formset = DetalleFormSet(request.POST, instance=factura)
            if formset.is_valid():
                formset.save()
                return redirect("lista_facturas")
        else:
            formset = DetalleFormSet(request.POST)
    else:
        factura_form = FacturaForm()
        formset = DetalleFormSet()

    return render(request, "facturas/crear.html", {
        "form": factura_form,
        "formset": formset,
    })
    
    
@login_required
def obtener_precio_producto(request):
    producto_id = request.GET.get('producto_id')
    try:
        producto = Producto.objects.get(id=producto_id)
        precio = float(producto.precio)
        return JsonResponse({'precio': f"{precio:.2f}"})
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)

@login_required
@permission_required("todo.view_factura", raise_exception=True)
def detalle_factura(request, pk):
    factura = get_object_or_404(Factura, pk=pk)
    detalles = DetalleFactura.objects.filter(factura=factura)
    total = sum(d.cantidad * d.precio_unitario for d in detalles)

    return render(request, 'facturas/detalle.html', {
        'factura': factura,
        'detalles': detalles,
        'total_factura': total,
    })


@login_required
@permission_required("todo.change_factura", raise_exception=True)
def editar_factura(request, pk):
    factura = get_object_or_404(Factura, pk=pk)

    if request.method == 'POST':
        nuevo_estado = request.POST.get("estado")
        
        form = FacturaForm(request.POST, instance=factura)
        formset = DetalleFacturaFormSet(request.POST, instance=factura)

        if form.is_valid() and formset.is_valid():
            factura = form.save(commit=False)
            
            if nuevo_estado and nuevo_estado in ['PENDIENTE', 'PAGADA', 'VENCIDA']:
                factura.estado = nuevo_estado
            
            factura.save()
            
            formset.save()
            
            if nuevo_estado and nuevo_estado in ['PENDIENTE', 'PAGADA', 'VENCIDA']:
                Factura.objects.filter(pk=factura.pk).update(estado=nuevo_estado)
            
            messages.success(request, f'Factura actualizada correctamente. Estado: {nuevo_estado}')
            return redirect('lista_facturas')
        else:
            messages.error(request, 'Error al actualizar la factura')
    else:
        form = FacturaForm(instance=factura)
        formset = DetalleFacturaFormSet(instance=factura)

    return render(request, 'facturas/editar.html', {
        'form': form,
        'formset': formset,
        'factura': factura
    })


@login_required
@permission_required("todo.delete_factura", raise_exception=True)
def eliminar_factura(request, pk):
    factura = Factura.objects.get(pk=pk)
    if request.method == 'POST':
        factura.delete()
        return redirect('lista_facturas')
    return render(request, 'facturas/eliminar.html', {'factura': factura})


#ROLES 
@permission_required("auth.change_user", raise_exception=True)
def roles(request):
    grupos_validos = ["Invitado", "Empleado", "Admin"]
    grupos = {g.name: g for g in Group.objects.filter(name__in=grupos_validos)}

    if request.method == "POST":
        cambios = 0
        for user in User.objects.all().select_related():
            key = f"rol_{user.id}"
            nuevo = request.POST.get(key)
            if not nuevo or nuevo not in grupos_validos:
                continue

            if user.is_superuser and nuevo != "Admin":
                messages.warning(request, f"No puedes quitar Admin a un superusuario: {user.username}")
                continue

            current_names = set(user.groups.values_list("name", flat=True))
            if current_names == {nuevo}:
                continue

            user.groups.clear()
            user.groups.add(grupos[nuevo])
            cambios += 1

        if cambios:
            messages.success(request, f"Roles actualizados: {cambios} cambios")
        else:
            messages.info(request, "No hubo cambios")
        return redirect("roles")

    usuarios = User.objects.all().order_by("username")
    return render(request, "todo/roles.html", {"usuarios": usuarios, "grupos": grupos_validos})


#EXPORTAR A EXCEL
@login_required
def exportar_excel(request):
    
    #Leer parametros de fecha
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    facturas = Factura.objects.all()
    
    #Si hay filtros de fecha, aplicar
    if fecha_inicio and fecha_fin:
        facturas = facturas.filter(fecha__range=[fecha_inicio, fecha_fin])
    elif fecha_inicio:
        facturas = facturas.filter(fecha__gte=fecha_inicio)
    elif fecha_fin:
        facturas = facturas.filter(fecha__lte=fecha_fin)
    
    #Crear el libro y hoja de excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Estadísticas"
    
    #Estilos básicos
    bold_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
    align_center = Alignment(horizontal="center", vertical="center")
    border_style = Border(
        left=Side(border_style="thin", color="000000"),
        right=Side(border_style="thin", color="000000"),
        top=Side(border_style="thin", color="000000"),
        bottom=Side(border_style="thin", color="000000"),
    )
    #Encabezados
    ws.append(["Métrica", "Valor"])
    for cell in ws[1]:
        cell.font = bold_font
        cell.fill = header_fill
        cell.alignment = align_center
        cell.border = border_style
    
    #Datos
    ventas_totales = facturas.filter(estado='PAGADA').aggregate(total=Sum('monto_total'))['total'] or 0
    num_facturas = facturas.count()
    num_facturas_pagadas = facturas.filter(estado='PAGADA').count()
    num_facturas_pendientes = facturas.filter(estado='PENDIENTE').count() 
    num_facturas_vencidas = facturas.filter(estado='VENCIDA').count()
    
    total_clientes = Cliente.objects.count()
    total_productos = Producto.objects.count()
    ultima_factura = facturas.order_by('-fecha').first()
    ultima_fecha = ultima_factura.fecha.strftime('%Y-%m-%d') if ultima_factura else "N/A"

    
    #Agregar filas con los datos
    ws.append(["Ingresos Reales (Solo Pagadas)", float(ventas_totales)])
    ws.append(["Total de Facturas", num_facturas])
    ws.append(["Facturas Pagadas", num_facturas_pagadas])
    ws.append(["Facturas Pendientes", num_facturas_pendientes])
    ws.append(["Facturas Vencidas", num_facturas_vencidas])
    ws.append(["Total Clientes", total_clientes])
    ws.append(["Total Productos", total_productos])
    ws.append(["Última Venta", ultima_fecha])
    
    
    #AGREGAR GRÁFICOS
    
    #Productos más vendidos
    ws["Z1"] = "Producto"
    ws["AA1"] = "Cantidad Vendida"

    top_productos = (
    DetalleFactura.objects.filter(
        factura__in=facturas.filter(estado='PAGADA')
    )
    .values("producto__nombre")
    .annotate(total_vendido=Sum("cantidad"))
    .order_by("-total_vendido")[:5]
)

    for i, prod in enumerate(top_productos, start=2):
        ws[f"Z{i}"] = prod["producto__nombre"]
        ws[f"AA{i}"] = int(prod["total_vendido"])

    #Crear gráficos
    datos = Reference(ws, min_col=27, min_row=2, max_row=1 + len(top_productos))
    etiquetas = Reference(ws, min_col=26, min_row=2, max_row=1 + len(top_productos))

    # Gráfico de barras
    chart_barras = BarChart()
    chart_barras.add_data(datos, titles_from_data=False)
    chart_barras.set_categories(etiquetas)
    
    ws["F2"] = "Top 5 Productos Más Vendidos"
    ws["F2"].font = Font(size=14, bold=True)
    ws["F2"].alignment = Alignment(horizontal="center")
        
    ws.add_chart(chart_barras, "D4")

    ws["F20"] = "Distribución Ventas Productos"
    ws["F20"].font = Font(size=14, bold=True)
    ws["F20"].alignment = Alignment(horizontal="center")
    
    # Gráfico circular
    chart_pie = PieChart()
    chart_pie.add_data(datos, titles_from_data=False)
    chart_pie.set_categories(etiquetas)
    
        
    chart_pie.dataLabels = DataLabelList()
    chart_pie.dataLabels.showPercent = True
    chart_pie.dataLabels.showSerName = False
    chart_pie.dataLabels.showVal = False
    chart_pie.dataLabels.showCatName = False
    
    ws.add_chart(chart_pie, "D22")

    
    # Aplicar estilo a todas las celdas con borde y alineación
    for row in ws.iter_rows(min_row=2, max_row=6, min_col=1, max_col=2):
        for cell in row:
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border_style
    
    # Ajustar ancho de columnas
    ws.column_dimensions["A"].width = 25
    ws.column_dimensions["B"].width = 20
    
    
    #Respuesta HTTP
    filename = f"estadisticas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    wb.save(response)

    return response


def generar_pdf(template_src, context_dict={}):
    html = render_to_string(template_src, context_dict)
    result = BytesIO()
    pdf = pisa.CreatePDF(html, dest=result)
    if not pdf.err:
        return result.getvalue()
    return None

@require_POST
def enviar_factura_email(request, pk):
    factura = get_object_or_404(Factura, pk=pk)
    
    detalles = factura.detallefactura_set.all()  # los detalles de esa factura
    total_factura = sum(d.subtotal() for d in detalles)  # suma de todos los subtotales

    context = {
        "factura": factura,
        "detalles": detalles,
        "total_factura": total_factura,
    }

    pdf = generar_pdf("facturas/pdf.html", context)

    
    if pdf:
        # Crear correo
        asunto = f"Comprobante_{factura.id}_{factura.fecha.strftime('%Y%m%d')}"
        mensaje = "Adjunto encontrarás tu factura en PDF."
        email = EmailMessage(asunto, mensaje, to=[factura.cliente.correo])
        
        # Adjuntar PDF
        email.attach(f"comprobante_{factura.id}_{detalles[0].producto.nombre}_{factura.fecha.strftime('%Y%m%d')}.pdf", pdf, "application/pdf")
        email.send()

        messages.success(request, "Comprobante enviado correctamente al cliente.")
    else:
        messages.error(request, "Hubo un error generando el PDF.")
    
    return redirect("detalle_factura", pk=factura.id)