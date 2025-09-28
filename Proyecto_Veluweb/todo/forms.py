from django import forms
from .models import Cliente
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.contrib.auth.forms import AuthenticationForm
from .models import Producto
from .models import Factura, DetalleFactura
from django.forms import inlineformset_factory
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class ClienteForm(forms.ModelForm): #Formulario para registrar clientes
    telefono = forms.CharField(
        max_length=10,
        min_length=10,
        validators=[
            RegexValidator(
                regex = r'^\d{10}$',
            )
        ],
        error_messages={
            'required': 'Este campo es obligatorio.',
            'min_length': 'Debe tener al menos 10 dígitos.',
            'max_length': 'Debe tener como máximo 10 dígitos.',
        },
        widget=forms.TextInput(attrs={
            'class': 'form-control'
            })
    )
    
    ciudad = forms.CharField(
        max_length=100,
        error_messages={
            'required': 'Este campo es obligatorio.',
            'max_length': 'La ciudad no puede tener más de 100 caracteres'
        },
        widget=forms.TextInput(attrs={
            'class': 'form-control'        
        })
    )
    
    direccion = forms.CharField(
        max_length=255,
        error_messages={
            'required': 'Este campo es obligatorio.',
            'max_length': 'La dirección no puede tener más de 255 caracteres.'
        },
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2
        })
    )
    
    

    class Meta:     #validación de datos del formulario registro
        model = Cliente
        fields = ['nombre', 'apellido', 'correo', 'telefono', 'ciudad', 'direccion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
        }
        error_messages = {
            'nombre': {'required': 'Este campo es obligatorio.'},
            'apellido': {'required': 'Este campo es obligatorio.'},
            'correo': {
                'required': 'Este campo es obligatorio.',
                'invalid': 'Ingrese un correo válido.',
            },
        }
        
    def clean(self): #validación de nombre y apellido
        cleaned_data = super().clean()
        nombre = cleaned_data.get('nombre')
        apellido = cleaned_data.get('apellido')
        
        if nombre and apellido:
            # Buscar clientes con el mismo nombre y apellido
            queryset = Cliente.objects.filter(
                nombre__iexact=nombre,
                apellido__iexact=apellido
            )
            
            # CLAVE: Excluir el cliente actual si estamos editando
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise ValidationError("Este cliente ya está registrado.")
        
        return cleaned_data


    def clean_correo(self): #validación de correo
        correo = self.cleaned_data.get('correo')
        queryset = Cliente.objects.filter(correo=correo)            #Excluir el mismo cliente en edición
        
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)         
        if queryset.exists():
                raise ValidationError('Este correo ya está registrado.')
        return correo

#Formulario de login
class LoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Correo electrónico',
            'required': True,
        }),
        label='Correo electrónico'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña',
            'required': True,
        }),
        label='Contraseña'
    ) 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_messages['invalid_login'] = 'Correo o contraseña incorrectos.'
        self.error_messages['inactive'] = 'Esta cuenta está inactiva.' 

# PRODUCTOS

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'codigo', 'precio', 'descripcion', 'stock', 'imagen']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control rounded-pill border-0 shadow-sm',
                'placeholder': 'Nombre del producto',
                'autocomplete': 'off',
                'required': 'true'
            }),
            'codigo': forms.TextInput(attrs={
                'class': 'form-control rounded-pill border-0 shadow-sm',
                'placeholder': 'Código del producto',
                'autocomplete': 'off',
                'required': 'true'
            }),
            'precio': forms.NumberInput(attrs={
                'class': 'form-control rounded-pill border-0 shadow-sm',
                'placeholder': 'Precio',
                'step': '0.01',
                'min': '0',
                'autocomplete': 'off',
                'required': 'true'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control border-0 shadow-sm',
                'placeholder': 'Escribe una breve descripción',
                'rows': 3,
                'autocomplete': 'off'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-select border-0 shadow-sm',
                'required': 'true'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-control rounded-pill border-0 shadow-sm',
                'placeholder': 'Cantidad en stock',
                'min': '0',
                'autocomplete': 'off',
                'required': 'true'
            }),
            'imagen': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'onchange': 'previewImage(event)'
            }),
        }

    #VALIDACIÓN DE NOMBRE
    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            queryset = Producto.objects.filter(nombre__iexact=nombre)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError('Ya existe un producto con este nombre.')
        return nombre
        
        
# FACTURAS

class FacturaForm(forms.ModelForm):
    class Meta:
        model = Factura
        fields = ['cliente', 'fecha', 'estado'] 
        widgets = {
            'fecha': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'},
                format='%Y-%m-%dT%H:%M'
            ),
            'estado': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-lg text-base focus:outline-none focus:border-blue-700'
            }),
            'cliente': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-lg text-base focus:outline-none focus:border-blue-700'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha'].input_formats = ['%Y-%m-%dT%H:%M']
        
        self.fields['estado'].choices = Factura.ESTADO_CHOICES



class DetalleFacturaForm(forms.ModelForm):
    class Meta:
        model = DetalleFactura
        fields = ['producto', 'cantidad', 'precio_unitario']
        widgets = {
            'cantidad': forms.NumberInput(attrs={'min': 1, 'class': 'form-control'}),
            'precio_unitario': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo productos activos y con stock > 0 para seleccionar (UX)
        self.fields['producto'].queryset = Producto.objects.filter(
            estado=True, stock__gt=0
        ).order_by('nombre')
        self.fields['producto'].widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned = super().clean()
        producto = cleaned.get("producto")
        cantidad = cleaned.get("cantidad")

        if producto is None or cantidad is None:
            return cleaned

        if cantidad <= 0:
            raise forms.ValidationError("La cantidad debe ser mayor a 0.")

        if not producto.estado:
            raise forms.ValidationError(f"El producto {producto.nombre} está desactivado.")

        if cantidad > producto.stock:
            raise forms.ValidationError(
                f"Stock insuficiente para {producto.nombre}. Disponible: {producto.stock}"
            )
        return cleaned



# Formset actualizado
DetalleFacturaFormSet = inlineformset_factory(
    Factura,
    DetalleFactura,
    form=DetalleFacturaForm,
    extra=1,
    can_delete=True
)

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-lg text-base focus:outline-none focus:border-blue-700',
            'placeholder': 'Correo electrónico'
        }),
        help_text='Requerido. Ingresa una dirección de correo válida.'
    )
    
    password1 = forms.CharField(
        label='Contraseña',
        min_length=8,
        max_length=50,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 pr-12 border-2 border-gray-200 rounded-lg text-base focus:outline-none focus:border-blue-700',
            'placeholder': 'Mínimo 8 caracteres',
            'maxlength': '50'
        }),
        help_text='La contraseña debe tener entre 8 y 50 caracteres.'
    )
    
    password2 = forms.CharField(
        label='Confirmar contraseña',
        min_length=8,
        max_length=50,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 pr-12 border-2 border-gray-200 rounded-lg text-base focus:outline-none focus:border-blue-700',
            'placeholder': 'Confirmar contraseña',
            'maxlength': '50'
        }),
        help_text='Repite la contraseña anterior.'
    )
    class Meta:
        model = User
        fields = ("email", "password1", "password2")  # Removimos username
    
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1:
            if len(password1) < 8:
                raise ValidationError('La contraseña debe tener al menos 8 caracteres.')
            if len(password1) > 50:
                raise ValidationError('La contraseña no puede tener más de 50 caracteres.')
        return password1

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Ya existe un usuario con este correo electrónico.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data["email"]
        user.email = email
        user.username = email
        if commit:
            user.save()
        return user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizamos los widgets de las contraseñas
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-lg text-base focus:outline-none focus:border-blue-700',
            'placeholder': 'Contraseña'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-lg text-base focus:outline-none focus:border-blue-700',
            'placeholder': 'Confirmar contraseña'
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Ya existe un usuario con este correo electrónico.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data["email"]
        user.email = email
        user.username = email  # Usamos el email como username
        if commit:
            user.save()
        return user