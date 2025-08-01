from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from .models import Cliente, Producto, Factura, DetalleFactura
from .forms import ClienteForm
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
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
from django.db.models import Q, Sum, Count, F
from django.db.models.functions import TruncDay
import json


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
        fecha__date__range=[start_date, end_date]
    ).aggregate(total=Sum('monto_total'))['total'] or 0

    num_facturas = Factura.objects.filter(
        fecha__date__range=[start_date, end_date]
    ).count()

    estado_facturas = Factura.objects.filter(
        fecha__date__range=[start_date, end_date]
    ).values('estado').annotate(count=Count('id')).order_by('estado')

    estado_dict = {item['estado']: item['count'] for item in estado_facturas}
    estados_data = {
        'Pagada': estado_dict.get('Pagada', 0),
        'Pendiente': estado_dict.get('Pendiente', 0),
        'Vencida': estado_dict.get('Vencida', 0),
    }

    top_productos_vendidos = DetalleFactura.objects.filter(
        factura__fecha__date__range=[start_date, end_date]
    ).values('producto__nombre').annotate(
        total_cantidad=Sum('cantidad')
    ).order_by('-total_cantidad')[:5]

    top_productos_labels = [item['producto__nombre'] for item in top_productos_vendidos]
    top_productos_data = [float(item['total_cantidad']) for item in top_productos_vendidos]

    producto_mas_vendido_nombre = top_productos_labels[0] if top_productos_labels else "N/A"


    ventas_diarias = Factura.objects.filter(
        fecha__date__range=[start_date, end_date]
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

    context = {
        'ventas_totales': ventas_totales,
        'num_facturas': num_facturas,
        'estados_data': estados_data,
        'top_productos_labels': json.dumps(top_productos_labels),
        'top_productos_data': json.dumps(top_productos_data),
        'producto_mas_vendido_nombre': producto_mas_vendido_nombre,
        'tendencia_ventas_labels': json.dumps(tendencia_ventas_labels),
        'tendencia_ventas_data': json.dumps(tendencia_ventas_data),
        'fecha_inicio_str': start_date.strftime('%Y-%m-%d'),
        'fecha_fin_str': end_date.strftime('%Y-%m-%d'),
        'total_clientes': total_clientes,
        'total_productos': total_productos,
        'ultima_factura': ultima_factura,
    }

    return render(request, 'estadisticas/estadisticas.html', context)

def home(request):
    return render(request, 'todo/home.html')  

@login_required
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
    page_number = request.GET.get('page')
    clientes = paginator.get_page(page_number)

    return render(request, 'todo/tabla.html', {
        'clientes': clientes,
        'query': query
    })

@login_required
def agregar(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('tabla')
    else:
        form = ClienteForm()
    
    return render(request, 'todo/agregar.html', {'form': form})

@login_required
def editar(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect('tabla')
    else:
        form = ClienteForm(instance=cliente)
    
    return render(request, 'todo/editar.html', {'form': form})

@login_required
def eliminar(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    cliente.delete()
    return redirect('tabla')

@login_required
def index(request):
    return render(request, 'todo/index.html')



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
    token = PasswordResetToken.objects.create(
        user=user,
        expires_at=timezone.now() + timedelta(minutes=10)
    )
    
    asunto = 'Código de recuperación de contraseña'
    mensaje = f'Hola {user.username}, tu código para restablecer tu contraseña es:\n\n{token.token}'
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


def bienvenida(request):
    return render(request, 'bienvenida.html')


# PRODUCTOS

@login_required
def productos_index(request):
    query = request.GET.get("buscar") 
    
    if query:
        productos_lista = Producto.objects.filter(
            Q(nombre__icontains=query) | Q(descripcion__icontains=query)
        ).order_by('-id')
    else:
        productos_lista = Producto.objects.all().order_by('-id')

    paginator = Paginator(productos_lista, 5)
    pagina = request.GET.get('page')
    productos = paginator.get_page(pagina)

    return render(request, 'productos/index.html', {
        'productos': productos,
        'buscar': query
    })
    

@login_required
def crear_producto(request):
    form = ProductoForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        return redirect('productos_index')
    return render(request, 'productos/crear.html', {'form': form})  # ← plantilla real

@login_required
def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    form = ProductoForm(request.POST or None, request.FILES or None, instance=producto)

    if form.is_valid():
        form.save()
        return redirect('productos_index')
    else:
        print(form.errors)  # 👈 Esto mostrará los errores en la consola

    return render(request, 'productos/editar.html', {'form': form})

@login_required
def eliminar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        producto.delete()
        return redirect('productos_index')
    return render(request, 'productos/eliminar.html', {'producto': producto})

@login_required
def detalle_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)

    producto_anterior = Producto.objects.filter(pk__lt=producto.pk).order_by('-pk').first()
    producto_siguiente = Producto.objects.filter(pk__gt=producto.pk).order_by('pk').first()

    contexto = {
        'producto': producto,
        'producto_anterior': producto_anterior,
        'producto_siguiente': producto_siguiente
    }

    return render(request, 'productos/detalle.html', contexto)

#FACTURAS

@login_required
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
    page_number = request.GET.get('page')
    facturas = paginator.get_page(page_number)

    return render(request, 'facturas/lista.html', {
        'facturas': facturas,
        'query': query
    })

@login_required
def crear_factura(request):
    if request.method == 'POST':
        form = FacturaForm(request.POST)
        formset = DetalleFacturaFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            factura = form.save()
            detalles = formset.save(commit=False)
            for detalle in detalles:
                detalle.factura = factura
                detalle.save()
            return redirect('lista_facturas')
    else:
        form = FacturaForm()
        formset = DetalleFacturaFormSet()

    return render(request, 'facturas/crear.html', {
        'form': form,
        'formset': formset
    })
    
    
@login_required
def obtener_precio_producto(request):
    producto_id = request.GET.get('producto_id')
    try:
        producto = Producto.objects.get(id=producto_id)
        return JsonResponse({'precio': str(producto.precio)})
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)

@login_required
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

def editar_factura(request, pk):
    factura = get_object_or_404(Factura, pk=pk)
    DetalleFormSet = modelformset_factory(DetalleFactura, form=DetalleFacturaForm, extra=1, can_delete=True)

    if request.method == 'POST':
        form = FacturaForm(request.POST, instance=factura)
        formset = DetalleFormSet(request.POST, queryset=DetalleFactura.objects.filter(factura=factura))

        if form.is_valid() and formset.is_valid():
            form.save()
            detalles = formset.save(commit=False)

            for detalle in detalles:
                detalle.factura = factura
                detalle.save()

            
            for obj in formset.deleted_objects:
                obj.delete()

            return redirect('lista_facturas')
    else:
        form = FacturaForm(instance=factura)
        formset = DetalleFormSet(queryset=DetalleFactura.objects.filter(factura=factura))

    return render(request, 'facturas/editar.html', {
        'form': form,
        'formset': formset,
        'factura': factura,
    })


@login_required
def eliminar_factura(request, pk):
    factura = Factura.objects.get(pk=pk)
    if request.method == 'POST':
        factura.delete()
        return redirect('lista_facturas')
    return render(request, 'facturas/eliminar.html', {'factura': factura})


#ROLES 
def roles(request):
    return render(request, 'todo/roles.html')