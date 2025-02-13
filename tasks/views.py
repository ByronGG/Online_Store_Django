from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth import login, logout, authenticate
from django.db import IntegrityError
from .models import Product, Order, OrderItem, Category  # Modelos BD
from django.core.paginator import Paginator  # Paginacion
import re
from django.db.models import Q


# Create your views here.
def home(request):
    return render(request, "home.html")

def about(request):
    return render(request, "about.html")

def contact(request):
    return render(request, "contact.html")

def privacy(request):
    return render(request, "privacy.html")

def signUp(request):
    if request.method == "GET":
        return render(request, "signup.html", {"form": UserCreationForm()})
    else:
        username = request.POST["username"]
        password1 = request.POST["password1"]
        password2 = request.POST["password2"]
        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return render(request, "signup.html", {"form": UserCreationForm()})
        if username == password1:
            messages.error(request, "Password cannot be the same as the username")
            return render(request, "signup.html", {"form": UserCreationForm()})
        if len(password1) < 8:
            messages.error(request, "Password must be at least 8 characters long")
            return render(request, "signup.html", {"form": UserCreationForm()})
        if not re.search(r"[A-Za-z]", password1):
            messages.error(request, "Password must contain at least one letter")
            return render(request, "signup.html", {"form": UserCreationForm()})
        if re.search(r"^\d+$", password1):
            messages.error(request, "Password cannot be entirely numeric")
            return render(request, "signup.html", {"form": UserCreationForm()})
        try:
            # register user
            user = User.objects.create_user(
                username=username,
                password=password1,
            )
            user.save()
            login(request, user)
            return redirect("home")
        except IntegrityError:
            messages.error(request, "Username already exists")
            return render(request, "signup.html", {"form": UserCreationForm()})


def product_list(request):
    # Obtener parámetros de búsqueda y filtrado
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    order = request.GET.get('order', '')

    # Iniciar con todos los productos
    products = Product.objects.all()

    # Aplicar filtros de búsqueda
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        )

    # Aplicar filtro de categoría
    if category_id:
        products = products.filter(category_id=category_id)

    # Aplicar ordenamiento
    if order:
        if order == 'price_asc':
            products = products.order_by('price')
        elif order == 'price_desc':
            products = products.order_by('-price')
        elif order == 'name':
            products = products.order_by('name')

    # Paginación
    paginator = Paginator(products, 9)  # 9 productos por página
    page_number = request.GET.get('page')
    products_page = paginator.get_page(page_number)

    # Obtener nombre de categoría seleccionada
    selected_category_name = ''
    if category_id:
        category = Category.objects.filter(id=category_id).first()
        if category:
            selected_category_name = category.name

    context = {
        'products': products_page,
        'categories': Category.objects.all(),
        'selected_category_name': selected_category_name,
        'query': query,
    }
    
    return render(request, "inventory/products.html", context)


def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        messages.error(
            request, "Debes iniciar sesión para agregar productos al carrito."
        )
        return redirect("signin")
    product = get_object_or_404(Product, id=product_id)
    order, created = Order.objects.get_or_create(user=request.user, is_completed=False)
    # Obtener la cantidad del formulario (por defecto 1 si no se proporciona)
    quantity = int(request.POST.get("quantity", 1))
    # Obtener o crear el OrderItem, asegurándote de establecer el precio
    order_item, item_created = OrderItem.objects.get_or_create(
        order=order,
        product=product,
        defaults={
            "price": product.price,
            "quantity": quantity,
        },  # Establece el precio y la cantidad al crear el OrderItem
    )
    if not item_created:
        order_item.quantity += quantity  # Incrementa la cantidad si el ítem ya existe
    order_item.save()  # Guarda el OrderItem actualizado
    # Recalcula el total del pedido
    order.total = sum(item.get_total() for item in order.items.all())
    order.save()
    messages.success(request, f"{quantity} x {product.name} agregado(s) al carrito.")
    return redirect("product_list")  # Redirige a la lista de productos


def remove_from_cart(request, item_id):
    if not request.user.is_authenticated:
        messages.error(request, "Debes iniciar sesión para modificar el carrito.")
        return redirect("signin")
    order_item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)
    order = order_item.order
    # Elimina el ítem y recalcula el total del pedido
    order_item.delete()
    order.total = sum(item.get_total() for item in order.items.all())
    order.save()
    messages.success(request, f"{order_item.product.name} eliminado del carrito.")
    return redirect("view_cart")


def view_cart(request):
    if not request.user.is_authenticated:
        messages.error(request, "Debes iniciar sesión para ver el carrito.")
        return redirect("signin")
    order = Order.objects.filter(user=request.user, is_completed=False).first()
    return render(request, "inventory/cart.html", {"order": order})

def cart_item_count(request):
    if request.user.is_authenticated:
        order = Order.objects.filter(user=request.user, is_completed=False).first()
        if order:
            return {'cart_item_count': order.items.count()}
    return {'cart_item_count': 0}

def get_cart_count(request):
    if request.user.is_authenticated:
        order = Order.objects.filter(user=request.user, is_completed=False).first()
        if order:
            return JsonResponse({'cart_item_count': order.items.count()})
    return JsonResponse({'cart_item_count': 0})

def checkout(request):
    if not request.user.is_authenticated:
        messages.error(request, "Debes iniciar sesión para finalizar la compra.")
        return redirect("signin")
    order = Order.objects.filter(user=request.user, is_completed=False).first()
    if order and order.items.exists():
        order.is_completed = True
        order.save()
        messages.success(request, "¡Compra realizada con éxito!")
    else:
        messages.error(request, "No hay productos en el carrito.")
    return redirect("home")


def signOut(request):
    logout(request)
    return redirect("signin")


def signIn(request):
    if request.method == "GET":
        # Si el usuario ya está autenticado, redirigir al home
        if request.user.is_authenticated:
            return redirect("home")
        return render(request, "signin.html")
    else:
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        if not username or not password:
            return render(
                request,
                "signin.html",
                {"error": "Por favor complete todos los campos"}
            )
            
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Obtener la URL de redirección si existe
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect("home")
        else:
            return render(
                request,
                "signin.html",
                {"error": "Usuario o contraseña incorrectos"}
            )


def profile(request):
    if not request.user.is_authenticated:
        messages.error(request, "Debes iniciar sesión para ver tu perfil.")
        return redirect("signin")
    
    # Obtener órdenes ordenadas por fecha descendente
    orders = Order.objects.filter(
        user=request.user, 
        is_completed=True
    ).order_by('-created_at')  # Asumiendo que tienes un campo created_at
    
    # Implementar paginación
    paginator = Paginator(orders, 10)  # 10 órdenes por página
    page_number = request.GET.get('page')
    orders_page = paginator.get_page(page_number)
    
    context = {
        'orders': orders_page,
        'user_info': {
            'username': request.user.username,
            'email': request.user.email,
            'date_joined': request.user.date_joined,
        }
    }
    
    return render(request, "profile.html", context)
