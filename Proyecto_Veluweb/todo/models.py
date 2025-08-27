from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import uuid
from django.urls import reverse
from django.utils.text import slugify

class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    correo = models.EmailField(unique=True)
    telefono = models.CharField(max_length=10)
    ciudad = models.CharField(max_length=100, verbose_name="Ciudad", default='Sin especificar')
    direccion = models.CharField(max_length=255, verbose_name="Dirección", default='Sin especificar')
    
    def __str__(self):
        return f"{self.nombre} {self.apellido}"
    
    class Meta:
        ordering = ['id']

class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=6, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return timezone.now() < self.expires_at

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre
        
    
class Producto(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)
    stock = models.PositiveIntegerField(default=0, verbose_name="Stock disponible")
    precio = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Precio Unitario")
    estado = models.BooleanField(default=True)

    def get_absolute_url(self):
        return reverse('detalle_producto', args=[self.pk])
    
    def __str__(self):
        return f"{self.nombre}"

class Factura(models.Model):
    ESTADO_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('Pagada', 'Pagada'),
        ('Vencida', 'Vencida'),
    ]
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    fecha = models.DateTimeField(default=timezone.now)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='Pendiente')
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Factura #{self.id} - {self.cliente}"

    def calculate_total(self):
        return sum(item.subtotal() for item in self.detallefactura_set.all())

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs) 
        if self.pk:
            self.monto_total = self.calculate_total()
            if self.estado == 'Pendiente' and self.fecha < timezone.now():
                self.estado = 'Vencida'
            super().save(update_fields=['monto_total', 'estado'])

class DetalleFactura(models.Model):
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"{self.producto} x {self.cantidad}"

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=DetalleFactura)
@receiver(post_delete, sender=DetalleFactura)
def update_factura_total(sender, instance, **kwargs):
    factura = instance.factura
    factura.monto_total = factura.calculate_total()
    if factura.estado == 'Pendiente' and factura.fecha < timezone.now():
        factura.estado = 'Vencida'
    factura.save(update_fields=['monto_total', 'estado'])