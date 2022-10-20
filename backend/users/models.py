from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class User(AbstractUser):
    """Переопределение модели пользователя."""

    id = models.AutoField(primary_key=True)

    username = models.CharField('Имя пользователя',
                                db_index=True,
                                max_length=150,
                                unique=True)

    email = models.EmailField(
        'Почта',
        unique=True,
        max_length=254,
    )

    first_name = models.CharField(
        'Имя',
        max_length=150,
    )

    last_name = models.CharField(
        'Фамилия',
        max_length=150,
    )

    password = models.CharField(
        'Пароль',
        max_length=100,
    )

    REQUIRED_FIELDS = ('email', 'first_name', 'last_name',)

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscribe(models.Model):
    """Модель подписки."""

    id = models.AutoField(primary_key=True)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribing',
        verbose_name='Автор'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'author'],
                                    name='unique_user_author'),
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def clean(self):
        if self.author == self.user:
            raise ValidationError('Нельзя подписаться на себя.')
