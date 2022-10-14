from django.contrib.auth import authenticate
from djoser.serializers import (TokenCreateSerializer, UserCreateSerializer,
                                UserSerializer)
from rest_framework import serializers
from rest_framework.serializers import SerializerMethodField

from users.models import User

FORBIDDEN_NAME = 'me'


class CustomUserSerializer(UserSerializer):
    """Сериализатор пользователей."""
    is_subscribed = SerializerMethodField('is_subscribed_user')

    class Meta:
        model = User
        fields = (
                  'email', 'id', 'username',
                  'first_name', 'last_name',
                  'is_subscribed'
        )

    def is_subscribed_user(self, obj):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and obj.subscribing.filter(user=user).exists()
        )


class SignupSerializer(UserCreateSerializer):
    """Сериализатор регистрации пользователя."""
    class Meta:
        model = User
        fields = (
                  'id', 'username', 'email',
                  'first_name', 'last_name',
                  'password'
        )

    def validate_username(self, username):
        if FORBIDDEN_NAME == username.lower():
            raise serializers.ValidationError(
                f'Имя {FORBIDDEN_NAME} использовать запрещено!'
            )
        return username


class CustomTokenCreateSerializer(TokenCreateSerializer):
    """Сериализатор получения токена."""
    class Meta:
        model = User
        fields = (
            'email', 'password'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.fields['email'] = serializers.CharField(required=False)

    def validate(self, attrs):
        password = attrs.get('password')
        params = {'email': attrs.get('email')}
        self.user = authenticate(
            request=self.context.get('request'), **params, password=password
        )
        if not self.user:
            self.user = User.objects.filter(**params).first()
            if self.user and not self.user.check_password(password):
                self.fail('invalid_credentials')
        if self.user and self.user.is_active:
            return attrs
        self.fail('invalid_credentials')
