from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.db import IntegrityError
from .models import Product, Order, OrderItem
from django.core.paginator import Paginator  # Paginacion


# Create your views here.
def home(request):
    return render(request, "home.html")


def signUp(request):
    if request.method == "GET":
        return render(request, "signup.html", {"form": UserCreationForm})
    else:
        if request.POST["password1"] == request.POST["password2"]:
            try:
                # register user
                user = User.objects.create_user(
                    username=request.POST["username"],
                    password=request.POST["password1"],
                )
                user.save()
                login(request, user)
                return redirect("home")
            except IntegrityError:
                return render(
                    request,
                    "signup.html",
                    {"form": UserCreationForm, "error": "Username already exists"},
                )
        return render(
            request,
            "signup.html",
            {"form": UserCreationForm, "error": "Password do not match"},
        )


def product_list(request):
    product_list = Product.objects.all()
    paginator = Paginator(product_list, 10)  # Muestra 10 productos por página
    page_number = request.GET.get("page")
    products = paginator.get_page(page_number)
    return render(request, "inventory/products.html", {"products": products})


def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        messages.error(
            request, "Debes iniciar sesión para agregar productos al carrito."
        )
        return redirect("signin")
    product = get_object_or_404(Product, id=product_id)
    order, created = Order.objects.get_or_create(user=request.user, is_completed=False)
    order_item, item_created = OrderItem.objects.get_or_create(
        order=order, product=product
    )
    if not item_created:
        order_item.quantity += 1
    else:
        order_item.price = (
            product.price
        )  # Establece el precio del producto al crear el OrderItem
    order_item.save()  # Guarda el OrderItem actualizado
    order.total += product.price  # Actualiza el total del pedido
    order.save()
    messages.success(request, f"{product.name} agregado al carrito.")
    return redirect("product_list")


def remove_from_cart(request, item_id):
    if not request.user.is_authenticated:
        messages.error(request, "Debes iniciar sesión para modificar el carrito.")
        return redirect("signin")
    order_item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)
    order = order_item.order
    order.total -= (
        order_item.price * order_item.quantity
    )  # Resta el total del ítem eliminado
    order.save()
    order_item.delete()
    messages.success(request, f"{order_item.product.name} eliminado del carrito.")
    return redirect("view_cart")


def view_cart(request):
    order = Order.objects.filter(user=request.user, is_completed=False).first()
    return render(request, "invetory/cart.html", {"order": order})


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
