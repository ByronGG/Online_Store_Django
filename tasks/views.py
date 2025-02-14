from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth import login, logout, authenticate
from django.db import IntegrityError
from .models import Product, Order, OrderItem, Category, Wishlist, Profile  # Modelos BD
from django.core.paginator import Paginator  # Paginacion
import re
from django.db.models import Q
from django.contrib.auth.decorators import login_required
import os
from datetime import datetime


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


@login_required
def profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    # Verificar si el perfil está completo
    profile_complete = all([
        request.user.first_name,
        request.user.last_name,
        profile.birth_date,
        profile.address,
        profile.city,
        profile.phone
    ])
    
    # Verificar si tiene tarjeta registrada
    has_card = bool(profile.card_number)
    
    return render(request, 'profile.html', {
        'profile': profile,
        'profile_complete': profile_complete,
        'has_card': has_card,
        'editing': request.GET.get('edit', False)
    })


def orders(request):
    if not request.user.is_authenticated:
        messages.error(request, "Debes iniciar sesión para ver tus pedidos.")
        return redirect("signin")
    
    # Obtener todas las órdenes completadas del usuario
    orders = Order.objects.filter(
        user=request.user,
        is_completed=True
    ).order_by('-created_at')
    
    # Paginación
    paginator = Paginator(orders, 5)  # 5 órdenes por página
    page_number = request.GET.get('page')
    orders_page = paginator.get_page(page_number)
    
    return render(request, "inventory/orders.html", {
        'orders': orders_page
    })


@login_required
def wishlist(request):
    wishlist_items = Wishlist.objects.filter(
        user=request.user
    ).select_related('product').order_by('-added_date')
    
    return render(request, "inventory/wishlist.html", {
        'wishlist_items': wishlist_items
    })

@login_required
def add_to_wishlist(request, product_id):
    if request.method != 'POST':
        messages.error(request, "Método no permitido")
        return redirect('product_list')
        
    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )
    
    if created:
        messages.success(request, f"{product.name} agregado a tu lista de deseos.")
    else:
        messages.info(request, f"{product.name} ya está en tu lista de deseos.")
    
    # Redirigir a la página anterior
    return redirect(request.META.get('HTTP_REFERER', 'product_list'))

@login_required
def remove_from_wishlist(request, product_id):
    Wishlist.objects.filter(user=request.user, product_id=product_id).delete()
    messages.success(request, "Producto eliminado de tu lista de deseos.")
    return redirect('wishlist')

@login_required
def update_avatar(request):
    if request.method == 'POST' and request.FILES.get('avatar'):
        # Obtener o crear el perfil del usuario
        profile, created = Profile.objects.get_or_create(user=request.user)
        
        # Si ya existe una imagen anterior, la eliminamos
        if profile.avatar:
            if os.path.isfile(profile.avatar.path):
                os.remove(profile.avatar.path)
        
        # Guardar la nueva imagen
        profile.avatar = request.FILES['avatar']
        profile.save()
        
        messages.success(request, "Foto de perfil actualizada correctamente.")
    else:
        messages.error(request, "Por favor, selecciona una imagen.")
    
    return redirect('profile')

@login_required
def update_profile(request):
    if request.method == 'POST':
        # Obtener o crear el perfil del usuario
        profile, created = Profile.objects.get_or_create(user=request.user)
        
        # Validar campos
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        
        # Validaciones
        if len(first_name) < 2:
            messages.error(request, "El nombre debe tener al menos 2 caracteres.")
            return redirect('profile')
            
        if len(last_name) < 2:
            messages.error(request, "Los apellidos deben tener al menos 2 caracteres.")
            return redirect('profile')
            
        if phone and not phone.isdigit():
            messages.error(request, "El teléfono solo debe contener números.")
            return redirect('profile')
            
        # Actualizar datos del usuario
        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.save()
        
        # Actualizar datos del perfil
        try:
            birth_date = request.POST.get('birth_date')
            if birth_date:
                profile.birth_date = birth_date
        except ValueError:
            messages.error(request, "Formato de fecha inválido.")
            return redirect('profile')
            
        profile.address = request.POST.get('address', '').strip()
        profile.city = request.POST.get('city', '').strip()
        profile.phone = phone
        profile.save()
        
        messages.success(request, "¡Perfil actualizado correctamente!")
    
    return redirect('profile')

@login_required
def update_card(request):
    if request.method == 'POST':
        profile = Profile.objects.get(user=request.user)
        
        # Obtener y validar datos
        card_number = request.POST.get('card_number', '').strip()
        card_holder = request.POST.get('card_holder', '').strip()
        card_expiry = request.POST.get('card_expiry', '').strip()
        card_cvv = request.POST.get('card_cvv', '').strip()
        
        # Validar fecha de expiración
        try:
            if not re.match(r'^(0[1-9]|1[0-2])\/([0-9]{2})$', card_expiry):
                messages.error(request, "La fecha de expiración debe tener formato MM/YY.")
                return redirect('profile')
                
            # Obtener mes y año de la tarjeta
            month, year = map(int, card_expiry.split('/'))
            card_date = datetime(2000 + year, month, 1)
            
            # Obtener fecha actual
            current_date = datetime.now()
            current_date = datetime(current_date.year, current_date.month, 1)
            
            if card_date < current_date:
                messages.error(request, "La tarjeta ha expirado. Por favor, use una tarjeta válida.")
                return redirect('profile')
                
        except (ValueError, IndexError):
            messages.error(request, "Fecha de expiración inválida.")
            return redirect('profile')
            
        # Validaciones
        if not card_number.isdigit() or len(card_number) != 16:
            messages.error(request, "El número de tarjeta debe tener 16 dígitos.")
            return redirect('profile')
        
        if not card_holder or len(card_holder) < 3:
            messages.error(request, "El nombre del titular es requerido.")
            return redirect('profile')
        
        if not card_cvv.isdigit() or len(card_cvv) not in [3, 4]:
            messages.error(request, "El CVV debe tener 3 o 4 dígitos.")
            return redirect('profile')
        
        # Guardar datos
        profile.card_number = card_number
        profile.card_holder = card_holder.upper()
        profile.card_expiry = card_expiry
        profile.card_cvv = card_cvv
        profile.save()
        
        messages.success(request, "Tarjeta guardada correctamente.")
    
    return redirect('profile')

