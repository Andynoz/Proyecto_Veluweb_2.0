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
                regex='^\d{10}$',
                message='El número de teléfono debe tener exactamente 10 dígitos.'
            )
        ],
        error_messages={
            'required': 'Este campo es obligatorio.',
            'min_length': 'Debe tener al menos 10 dígitos.',
            'max_length': 'Debe tener como máximo 10 dígitos.',
        },
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:     #validación de datos del formulario registro
        model = Cliente
        fields = ['nombre', 'apellido', 'correo', 'telefono']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
        }
        error_messages = {
            'nombre': {'required': 'Este campo es obligatorio.'},
            # 'apellido': {'required': 'Este campo es obligatorio.'}
            'correo': {
                'required': 'Este campo es obligatorio.',
                'invalid': 'Ingrese un correo válido.',
            },
        }

    def clean_correo(self): #validación de correo
        correo = self.cleaned_data.get('correo')
        if Cliente.objects.filter(correo=correo).exists():
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
        # Personalizar mensajes de error
        self.error_messages['invalid_login'] = 'Correo o contraseña incorrectos.'
        self.error_messages['inactive'] = 'Esta cuenta está inactiva.' 

# PRODUCTOS

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'codigo', 'precio', 'descripcion', 'imagen']


class FacturaForm(forms.ModelForm):
    class Meta:
        model = Factura
        fields = ['cliente']

class DetalleFacturaForm(forms.ModelForm):
    class Meta:
        model = DetalleFactura
        fields = ['producto', 'cantidad', 'precio_unitario']

DetalleFacturaFormSet = inlineformset_factory(
    Factura,
    DetalleFactura,
    form=DetalleFacturaForm,
    extra=1,  # Puedes ajustar la cantidad de líneas iniciales
)