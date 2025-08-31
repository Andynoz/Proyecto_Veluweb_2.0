from django import forms
from .models import Cliente
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.contrib.auth.forms import AuthenticationForm
from .models import Producto
from .models import Factura, DetalleFactura
from django.forms import inlineformset_factory


class ClienteForm(forms.ModelForm): #Formulario para registrar clientes
    telefono = forms.CharField(
        max_length=10,
        min_length=10,
        validators=[
            RegexValidator(
                regex = r'^\d{10}$',
                message='El número de teléfono debe tener exactamente 10 dígitos.'
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
        self.fields['producto'].queryset = Producto.objects.filter(
            estado=True,  
        ).order_by('nombre')
        
        self.fields['producto'].widget.attrs.update({'class': 'form-control'})

# Formset actualizado
DetalleFacturaFormSet = inlineformset_factory(
    Factura,
    DetalleFactura,
    form=DetalleFacturaForm,
    extra=1,
    can_delete=True
)