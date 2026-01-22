from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from .models import ContactMessage
from statistical_analysis.q2_analysis import create_price_pie_chart,create_price_buckets,get_statistics
from statistical_analysis.q1_analysis import (
    create_genre_popularity_weighted, 
    create_genre_count_chart, 
    create_top_tags_chart, 
    get_q1_statistics
)
from statistical_analysis.q3_analysis import (
    create_language_engagement_chart,
    create_language_pie_chart,
    create_cumulative_engagement_chart,
    create_language_game_count_chart,
    get_q3_statistics
)


# Create your views here.
def home(request):
    return render(request, "index.html")

def login_required_page(request):
    return render(request, "login_required.html")


def login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        
          # Find user by email
        # try:
        user_obj = User.objects.get(email=email)
        user = authenticate(request, username=user_obj.email, password=password)
            
        if user is not None:
                auth_login(request, user)
                # Redirect to the page they were trying to access, or home
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
        else:
                messages.error(request, "Email ou mot de passe incorrect")
        # except User.DoesNotExist:
        #     messages.error(request, "Email ou mot de passe incorrect")
    
    return render(request, "connecter.html")

# Protected Analysis Page
@login_required(login_url="/login-required/")
def q1(request):
    """Q1 - Genres and Tags Analysis"""
    context = {
        'chart1': create_genre_popularity_weighted(),
        'chart2': create_genre_count_chart(),
        'chart3': create_top_tags_chart(),
        'stats': get_q1_statistics()
    }
    return render(request, 'q1.html', context)

@login_required(login_url="/login-required/")
def q2(request):
    """Q2 - Price Analysis"""
    context = {
        'chart1': create_price_pie_chart(),
        'chart2': create_price_buckets(),
        'stats': get_statistics()
    }
    return render(request, 'q2.html', context)

@login_required(login_url="/login-required/")
def q3(request):
    """Q3 - Language Engagement Analysis"""
    context = {
        'chart1': create_language_engagement_chart(),
        'chart2': create_language_pie_chart(),
        'chart3': create_cumulative_engagement_chart(),
        'chart4': create_language_game_count_chart(),
        'stats': get_q3_statistics()
    }
    return render(request, 'q3.html', context)

#Registration 
def register(request):
    if request.method == "POST":
        full_name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Les mots de passe ne correspondent pas")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "email a déjà utilisé")
            return redirect("register")

        user = User.objects.create_user(
            username = email,
            email=email,
            password=password
        )
        user.first_name = full_name
        user.save()

        auth_login(request, user)
       
        return redirect("home")

    return render(request, "inscription.html")


def contact(request):
    if request.method == "POST":
        nom = request.POST.get('name')   # le champ HTML s'appelle "name"
        email = request.POST.get('email')
        message_text = request.POST.get('message')

        ContactMessage.objects.create(
            nom=nom,          # ✅ correspond au modèle
            email=email,
            message=message_text
        )

        messages.success(request, "Merci pour votre message !")
        return redirect("home")

    return render(request, "contact.html")



