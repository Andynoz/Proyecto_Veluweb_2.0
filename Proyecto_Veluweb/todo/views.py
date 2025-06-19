from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse
from .models import Cliente
from .forms import ClienteForm
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages
from .models import PasswordResetToken
from django.utils import timezone
from django.core.mail import send_mail
from datetime import timedelta
from django.db import IntegrityError
from django.contrib.auth.backends import ModelBackend
from .models import Producto
from .forms import ProductoForm
from .models import Factura, DetalleFactura
from .forms import FacturaForm, DetalleFacturaFormSet, DetalleFacturaForm
from django.forms import modelformset_factory
from django.contrib.auth.decorators import login_required



def home(request):
    return render(request, 'todo/home.html')  

@login_required
def tabla(request):
    clientes = Cliente.objects.all()
    return render(request, 'todo/tabla.html', {'clientes': clientes})

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
    productos = Producto.objects.all()
    return render(request, 'productos/index.html', {'productos': productos})

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
    return render(request, 'productos/editar.html', {'form': form})  # ← plantilla real

@login_required
def eliminar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        producto.delete()
        return redirect('productos_index')
    return render(request, 'productos/eliminar.html', {'producto': producto})


#FACTURAS

@login_required
def lista_facturas(request):
    facturas = Factura.objects.all()
    return render(request, 'facturas/lista.html', {'facturas': facturas})

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
