from django.db import models

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    description = models.TextField(blank=True, null=True, verbose_name="Descripción")

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nombre")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Categoria")
    description = models.TextField(blank=True, null=True, verbose_name="Descripción")
    stock = models.PositiveBigIntegerField(default=0, verbose_name="Stock")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('IN', 'Entrada'),
        ('OUT', 'Salida'),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Producto")
    quantity = models.IntegerField(verbose_name="Cantidad")
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_TYPES, verbose_name="Tipo de movimiento")
    movement_date = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de movimiento")

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.product} - {self.quantity}"
    
    class Meta:
        verbose_name = "Movimiento de stock"
        verbose_name_plural = "Movimientos de stock"