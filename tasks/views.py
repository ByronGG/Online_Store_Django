from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.contrib.auth import login, logout, authenticate
from django.db import IntegrityError
from .models import Product
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
                return redirect("tasks")
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
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    return render(request, 'inventory/products.html', {'products': products})


def signOut(request):
    logout(request)
    return redirect("home")


"""
def signIn(request):
    if request.method == "GET":
        return render(request, "signin.html", {"form": AuthenticationForm()})
    else:
        user = authenticate(
            request,
            username=request.POST["username"],
            password=request.POST["password"],
        )
        if user is None:
            return render(
                request,
                "signin.html",
                {
                    "form": AuthenticationForm(),
                    "error": "Username or password is incorrect",
                },
            )
        else:
            login(request, user)
            return redirect("home")
"""


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
