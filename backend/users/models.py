from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

from foodgram.constants import ACCOUNT_USERNAME_LIMIT, USER_EMAIL_LIMIT


class User(AbstractUser):
    """Модель пользователя с email в качестве USERNAME_FIELD."""
    email = models.EmailField(
        verbose_name='Электронная почта',
        max_length=USER_EMAIL_LIMIT,
        unique=True
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=ACCOUNT_USERNAME_LIMIT
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=ACCOUNT_USERNAME_LIMIT
    )
    avatar = models.ImageField(
        verbose_name='Аватар',
        upload_to='avatars/',
        default='',
        blank=True,
        null=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'password']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.last_name} {self.first_name}'


class Follow(models.Model):
    """Модель подписки пользователей."""
    following = models.ForeignKey(
        User,
        verbose_name='Автор контента',
        related_name='followers',
        on_delete=models.CASCADE
    )
    follower = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        related_name='following_authors',
        on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['follower', 'following'],
                name='unique_subscription'
            )
        ]

    def clean(self):
        if self.follower == self.following:
            raise ValidationError("Подписка на себя невозможна")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Подписка: {self.follower} → {self.following}'
