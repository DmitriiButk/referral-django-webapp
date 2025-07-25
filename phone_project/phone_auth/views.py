import random
import time

from rest_framework import status, permissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from .models import VerificationCode
from .serializers import (
    PhoneNumberSerializer,
    VerificationSerializer,
    UserSerializer,
    ActivateInviteCodeSerializer
)

User = get_user_model()


class SendVerificationCodeView(APIView):
    """API для отправки кода верификации на телефон пользователя."""

    def post(self, request: Request) -> Response:
        """
        Создает и отправляет код верификации на указанный номер телефона.

        Args:
            request: Запрос с номером телефона

        Returns:
            Ответ с сообщением об отправке и кодом верификации
        """
        serializer = PhoneNumberSerializer(data=request.data)

        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']

            verification_code = ''.join(random.choice('0123456789') for _ in range(4))

            VerificationCode.objects.filter(phone_number=phone_number).delete()
            VerificationCode.objects.create(phone_number=phone_number, code=verification_code)

            time.sleep(random.uniform(1, 2))

            return Response({
                'message': f'Код подтверждения отправлен на номер {phone_number}',
                'code': verification_code
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyCodeView(APIView):
    """API для верификации пользователя по коду подтверждения."""

    def post(self, request: Request) -> Response:
        """
        Проверяет код верификации и авторизует пользователя.

        Args:
            request: Запрос с номером телефона и кодом верификации

        Returns:
            Ответ с токенами доступа и флагом нового пользователя
        """
        serializer = VerificationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        phone_number = serializer.validated_data['phone_number']
        code = serializer.validated_data['code']

        try:
            verification = VerificationCode.objects.get(phone_number=phone_number, code=code)
        except VerificationCode.DoesNotExist:
            return Response({'error': 'Неверный код подтверждения'}, status=status.HTTP_400_BAD_REQUEST)

        verification.delete()

        try:
            user = User.objects.get(phone_number=phone_number)
            created = False
        except User.DoesNotExist:
            user = User.objects.create_user(phone_number=phone_number)
            created = True

        refresh = RefreshToken.for_user(user)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'is_new_user': created
        })


class ProfileView(APIView):
    """API для получения профиля текущего пользователя."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        """
        Возвращает информацию о профиле авторизованного пользователя.

        Args:
            request: Запрос авторизованного пользователя

        Returns:
            Ответ с данными профиля пользователя
        """
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class ActivateInviteCodeView(APIView):
    """API для активации инвайт-кода другого пользователя."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        """
        Активирует указанный инвайт-код для текущего пользователя.

        Args:
            request: Запрос с инвайт-кодом

        Returns:
            Ответ с сообщением об успешной активации или ошибкой
        """
        if request.user.activated_invite_code:
            return Response(
                {'error': 'Вы уже активировали инвайт-код'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ActivateInviteCodeSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        invite_code = serializer.validated_data['invite_code']

        try:
            inviter = User.objects.get(invite_code=invite_code)
        except User.DoesNotExist:
            return Response(
                {'error': 'Недействительный инвайт-код'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if inviter == request.user:
            return Response(
                {'error': 'Нельзя использовать собственный инвайт-код'},
                status=status.HTTP_400_BAD_REQUEST
            )

        request.user.activated_invite_code = invite_code
        request.user.save()

        return Response({'message': 'Инвайт-код успешно активирован'})
