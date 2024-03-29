from django.shortcuts import get_object_or_404
from djoser import utils
from djoser.serializers import SetPasswordSerializer, TokenSerializer
from djoser.views import TokenCreateView
from recipes.serializers import SubscriptionsSerializer
from recipes.views import ALREADY_IN_FAVORITE, SELF_FAVORITE
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (HTTP_200_OK, HTTP_201_CREATED,
                                   HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST)
from users.models import Subscribe, User
from users.serializers import CustomUserSerializer, SignupSerializer


class CustomTokenCreateView(TokenCreateView):
    """Вьюсет получения токена."""
    def _action(self, serializer):
        """Возвращает токен и статус HTTP_201_CREATED."""
        token = utils.login_user(self.request, serializer.user)
        token_serializer_class = TokenSerializer
        return Response(
            data=token_serializer_class(token).data,
            status=status.HTTP_201_CREATED
        )


class CustomUserViewSet(viewsets.ModelViewSet):
    """Вьюсет пользователей."""
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (AllowAny,)
    pagination_class = LimitOffsetPagination

    def get_serializer_class(self):
        """
        Возвращает сериализатор в зависимости от
        используемого метода.
        """
        if self.action == "create":
            return SignupSerializer
        elif self.action == "set_password":
            return SetPasswordSerializer
        elif self.action == "subscriptions":
            return SubscriptionsSerializer
        return self.serializer_class

    @action(['get'], detail=False, permission_classes=(IsAuthenticated,))
    def me(self, request, *args, **kwargs):
        """Возвращает данные текущего пользователя."""
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(['post'], detail=False, permission_classes=(IsAuthenticated,))
    def set_password(self, request, *args, **kwargs):
        """
        Принимает старый и новый пароль и после
        проверки задает новый пароль.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.request.user.set_password(serializer.data["new_password"])
            self.request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(['get'], detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request, *args, **kwargs):
        """Показывает все подписки пользователя."""
        user = request.user
        subscriptions = Subscribe.objects.filter(user=user)
        serializer = self.get_serializer(subscriptions, many=True)
        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(['post', 'delete'], detail=True,
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, pk=None):
        """
        Добавляет методом POST и удалает методом DELETE
        автора из полписок. Если полписка уже оформлена или
        не существует выдает соответствующие сообщения.
        """
        user = self.request.user
        author = get_object_or_404(User, pk=pk)
        if request.method == 'POST':
            if user == author:
                return Response({'detail': SELF_FAVORITE},
                                status=HTTP_200_OK)
            subscribe, created = Subscribe.objects.get_or_create(
                user=user, author=author
            )
            if created is True:
                serializer = SubscriptionsSerializer()
                return Response(
                    serializer.to_representation(instance=subscribe),
                    status=HTTP_201_CREATED
                )
            return Response({'detail': ALREADY_IN_FAVORITE},
                            status=HTTP_200_OK)
        if request.method == 'DELETE':
            Subscribe.objects.filter(
                user=user,
                author=author
            ).delete()
            return Response(status=HTTP_204_NO_CONTENT)
        return Response(status=HTTP_400_BAD_REQUEST)
