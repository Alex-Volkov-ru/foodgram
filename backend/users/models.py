from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError

from foodgram.constants import EMAIL_MAX_LENGTH, USER_FIELDS_MAX_LENGTH


class User(AbstractUser):
    """Модель пользователя с email в качестве USERNAME_FIELD."""
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
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        default='',
        verbose_name='Аватар'
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
        User,
        on_delete=models.CASCADE,
        related_name='followed'
    )
    following = models.ForeignKey(
        User,
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

    def clean(self):
        if self.user == self.following:
            raise ValidationError(
                "Пользователь не может подписаться на самого себя")
        return super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user} подписан на {self.following}'
