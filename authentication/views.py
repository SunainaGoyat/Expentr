from base64 import urlsafe_b64decode, urlsafe_b64encode
from email.message import EmailMessage
from telnetlib import LOGOUT
from . tokens import generate_tokens
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate , login, logout
from expentr import settings
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
      

# from expentr.authentication.apps import LoginConfig

# Create your views here.
def home(request):
    return render(request,"authentication/index.html")

def signup(request):
    if request.method == "POST":
        username = request.POST.get('username')
        fname = request.POST.get('fname')
        lname = request.POST.get('lname')
        email = request.POST.get('email')
        pass1 =  request.POST.get('pass1')
        pass2 = request.POST.get('pass2')

        if User.objects.filter(username=username):
            messages.error(request,"Username already exist! Please try other username")
            return redirect('home')

        if User.objects.filter(email=email):
            messages.error(request, "Email already registered")
            return redirect ('home')

        if len(username)>10:
            messages.error(request, "Username must be under 10 character ")        

        if pass1 != pass2:
            messages.error(request, "Password didn't match!")

        if not username.isalnum():
            messages.error(request, "Username mut be alpha-numeric")
            return redirect('home')

        myuser = User.objects.create_user(username,email,pass1)
        myuser.first_name = fname
        myuser.last_name = lname
        myuser.is_active = False
        myuser.save()

        messages.success(request, "Your account has been successfully created . We have sent you a confirmation email, Please confirm your email in order to activate your account")

        # if User.objects.filter(username = username).first():
        #   messages.error(request, "This username is already taken")
        #   return redirect('home')

        messages.success(request,"Your Account has been successfully created.")

        # Welcome EMAIL

        subject="Welcome to Expentr =  Django login!!"
        message = "Hello" + myuser.first_name + "|| \n" + "Welcome to Expentr!! \n Thank you for visiting our website \n We have also sent  you a confirmation Email, Please coonfirm your email address  in ordr to activate your account . \n\n Thanking you \n Vishu Goyat"
        from_email = settings.EMAIL_HOST_USER
        to_list = [myuser.email]
        send_mail(subject, message, from_email, to_list, fail_silently=True)

        # Email Address confirmation Email

        current_site = get_current_site(request)
        email_subject = "Confirm your  Email @ Expentr - Django Login"
        message2 = render_to_string('email_confirmation.html',{
            'name':myuser.first_name,
            'domain': current_site.domain,
            'uid' : urlsafe_base64_encode(force_bytes(myuser.pk)),
            'token': generate_tokens.make_token(myuser)
        })
        email = EmailMessage(
            email_subject,
            message2,
            settings.EMAIL_HOST_USER,
            [myuser.email],
        )
        email.fail_silently = True
        email.send()

        return redirect('signin')
        
    return render(request, "authentication/signup.html")

def signin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        pass1= request.POST.get('pass1')

        user = authenticate(username=username, password=pass1)

        if user is not None:
            login(request,user)
            fname = user.first_name
            return render(request,"authentication/index.html",{'fname':fname})

        else:
            messages.error(request,"Bad Credentials")
            return redirect('home')
    return render(request, "authentication/signin.html")

def signout(request):
        logout(request)
        messages.success(request,"Logged out Successfully")
        return redirect('home')

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        myuser = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        myuser = None
    if myuser is not None and generate_tokens.check_token(myuser, token):
        myuser.is_active = True
        myuser.save()
        login(request,myuser)
        return redirect('home')
    else:
        return render(request,'activation_failed.html')