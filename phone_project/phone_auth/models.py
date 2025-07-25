from typing import Optional, Any, Union
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import random
import string


class UserManager(BaseUserManager):
    """Менеджер для кастомной модели пользователя с авторизацией по номеру телефона."""

    def create_user(self, phone_number: str, password: Optional[str] = None, **extra_fields) -> 'User':
        """
        Создает и сохраняет пользователя с указанным телефоном и паролем.

        Args:
            phone_number: Номер телефона пользователя
            password: Опциональный пароль
            extra_fields: Дополнительные поля

        Returns:
            Объект пользователя

        Raises:
            ValueError: Если не указан номер телефона
        """
        if not phone_number:
            raise ValueError('Требуется номер телефона')

        user = self.model(phone_number=phone_number, **extra_fields)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number: str, password: Optional[str] = None, **extra_fields) -> 'User':
        """
        Создает и сохраняет суперпользователя.

        Args:
            phone_number: Номер телефона суперпользователя
            password: Опциональный пароль
            extra_fields: Дополнительные поля

        Returns:
            Объект суперпользователя
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(phone_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Кастомная модель пользователя с авторизацией по номеру телефона
    и функционалом реферальной системы.
    """
    phone_number = models.CharField(max_length=15, unique=True)
    invite_code = models.CharField(max_length=6, unique=False, null=True, blank=True)
    activated_invite_code = models.CharField(max_length=6, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Переопределенный метод сохранения для автоматической генерации инвайт-кода.
        """
        if not self.invite_code:
            self.invite_code = self.generate_invite_code()
        super().save(*args, **kwargs)

    def generate_invite_code(self) -> str:
        """
        Генерирует уникальный инвайт-код для пользователя.

        Returns:
            Уникальный инвайт-код
        """
        chars = string.ascii_uppercase + string.digits
        attempts = 0
        max_attempts = 10  # Предотвращение бесконечного цикла

        while attempts < max_attempts:
            code = ''.join(random.choice(chars) for _ in range(6))
            if not type(self).objects.filter(invite_code=code).exists():
                return code
            attempts += 1

        # Запасной вариант, если не удалось создать уникальный код
        return f"CODE{''.join(random.choice(string.digits) for _ in range(6))}"

    def __str__(self) -> str:
        """Строковое представление пользователя."""
        return self.phone_number


class VerificationCode(models.Model):
    """Модель для хранения кодов верификации, отправляемых на телефон."""

    phone_number = models.CharField(max_length=15)
    code = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        """Строковое представление кода верификации."""
        return f"{self.phone_number} - {self.code}"
