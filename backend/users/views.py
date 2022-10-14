from djoser import utils
from djoser.serializers import SetPasswordSerializer, TokenSerializer
from django.shortcuts import get_object_or_404
from djoser.views import TokenCreateView
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.status import (HTTP_200_OK, HTTP_201_CREATED,
                                   HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from recipes.views import ALREADY_IN_FAVORITE, SELF_FAVORITE

from users.models import User, Subscribe
from users.serializers import (CustomUserSerializer, SignupSerializer)
from recipes.serializers import SubscriptionsSerializer


class CustomTokenCreateView(TokenCreateView):
    """Вьюсет получения токена."""
    def _action(self, serializer):
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
        if self.action == "create":
            return SignupSerializer
        elif self.action == "set_password":
            return SetPasswordSerializer
        elif self.action == "subscriptions":
            return SubscriptionsSerializer
        return self.serializer_class

    @action(['get'], detail=False, permission_classes=(IsAuthenticated,))
    def me(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(['post'], detail=False, permission_classes=(IsAuthenticated,))
    def set_password(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        self.request.user.set_password(serializer.data["new_password"])
        self.request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(['get'], detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request, *args, **kwargs):
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
