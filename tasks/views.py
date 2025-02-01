from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.db import IntegrityError
from .models import Product, Order, OrderItem # Modelos BD
from django.core.paginator import Paginator  # Paginacion
import re


# Create your views here.
def home(request):
    return render(request, "home.html")


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
    product_list = Product.objects.all()
    paginator = Paginator(product_list, 10)  # Muestra 10 productos por página
    page_number = request.GET.get("page")
    products = paginator.get_page(page_number)
    return render(request, "inventory/products.html", {"products": products})


def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        messages.error(request, "Debes iniciar sesión para agregar productos al carrito.")
        return redirect("signin")
    product = get_object_or_404(Product, id=product_id)
    order, created = Order.objects.get_or_create(user=request.user, is_completed=False)
    # Obtener o crear el OrderItem, asegurándote de establecer el precio
    order_item, item_created = OrderItem.objects.get_or_create(
        order=order,
        product=product,
        defaults={'price': product.price}  # Establece el precio al crear el OrderItem
    )
    if not item_created:
        order_item.quantity += 1
    order_item.save()  # Guarda el OrderItem actualizado
    # Recalcula el total del pedido
    order.total = sum(item.get_total() for item in order.items.all())
    order.save()
    messages.success(request, f"{product.name} agregado al carrito.")
    return redirect("view_cart")  # Redirige al carrito después de agregar el producto


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
        return render(request, "signin.html", {"form": AuthenticationForm()})
    else:
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("home")
            else:
                return render(
                    request,
                    "signin.html",
                    {"form": form, "error": "Username or password is incorrect"},
                )
        else:
            return render(
                request,
                "signin.html",
                {"form": form, "error": "Invalid form data"},
            )


def profile(request):
    if not request.user.is_authenticated:
        messages.error(request, "Debes iniciar sesión para ver tu perfil.")
        return redirect("signin")
    orders = Order.objects.filter(user=request.user, is_completed=True)
    return render(request, "profile.html", {"orders": orders})
