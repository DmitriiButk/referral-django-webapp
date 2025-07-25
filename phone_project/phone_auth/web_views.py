from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import HttpRequest, HttpResponse

from .models import User, VerificationCode
import random


def index_view(request: HttpRequest) -> HttpResponse:
    """Главная страница сайта."""
    return render(request, 'index.html')


@require_http_methods(["GET", "POST"])
def login_view(request: HttpRequest) -> HttpResponse:
    """Страница входа по номеру телефона."""
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')

        if phone_number:
            verification_code = ''.join(random.choice('0123456789') for _ in range(4))

            VerificationCode.objects.filter(phone_number=phone_number).delete()
            VerificationCode.objects.create(phone_number=phone_number, code=verification_code)

            request.session['phone_number'] = phone_number
            request.session['verification_code'] = verification_code

            return redirect('verify_code')

    return render(request, 'auth/login.html')


@require_http_methods(["GET", "POST"])
def verify_code_view(request: HttpRequest) -> HttpResponse:
    """Страница верификации кода."""
    phone_number = request.session.get('phone_number')

    if not phone_number:
        return redirect('login')

    if request.method == 'POST':
        code = request.POST.get('code')

        try:
            verification = VerificationCode.objects.get(phone_number=phone_number, code=code)

            verification.delete()

            user, created = User.objects.get_or_create(phone_number=phone_number)

            login(request, user)

            return redirect('dashboard')
        except VerificationCode.DoesNotExist:
            error = "Неверный код подтверждения"
            return render(request, 'auth/verify.html', {'error': error})

    debug_code = request.session.get('verification_code', '')
    return render(request, 'auth/verify.html', {'debug_code': debug_code})


@login_required
def dashboard_view(request: HttpRequest) -> HttpResponse:
    """Страница личного кабинета."""
    invited_users = User.objects.filter(activated_invite_code=request.user.invite_code)

    return render(request, 'profile/dashboard.html', {
        'user': request.user,
        'invited_users': invited_users
    })


@login_required
@require_http_methods(["POST"])
def activate_invite_view(request: HttpRequest) -> HttpResponse:
    """Активация инвайт-кода."""
    invited_users = User.objects.filter(activated_invite_code=request.user.invite_code)

    if request.user.activated_invite_code:
        return render(request, 'profile/dashboard.html', {
            'error': 'Вы уже активировали инвайт-код',
            'invited_users': invited_users
        })

    invite_code = request.POST.get('invite_code')

    try:
        inviter = User.objects.get(invite_code=invite_code)

        if inviter == request.user:
            return render(request, 'profile/dashboard.html', {
                'error': 'Нельзя использовать собственный инвайт-код',
                'invited_users': invited_users
            })

        request.user.activated_invite_code = invite_code
        request.user.save()

        return redirect('dashboard')
    except User.DoesNotExist:
        return render(request, 'profile/dashboard.html', {
            'error': 'Недействительный инвайт-код',
            'invited_users': invited_users
        })
