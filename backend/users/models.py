from django.contrib.auth.models import AbstractUser
from django.db import models
from foodgram.constants import EMAIL_MAX_LENGTH, USER_FIELDS_MAX_LENGTH


class CustomUser(AbstractUser):
    """Кастомная модель пользователя с email в качестве USERNAME_FIELD."""
    first_name = models.CharField(
        max_length=USER_FIELDS_MAX_LENGTH,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=USER_FIELDS_MAX_LENGTH,
        verbose_name='Фамилия'
    )
    email = models.EmailField(
        unique=True,
        max_length=EMAIL_MAX_LENGTH,
        verbose_name='Электронная почта'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['password', 'username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Follow(models.Model):
    """Модель подписки пользователей."""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='followed'
    )
    following = models. ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='follows',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_pair'
            )
        ]
