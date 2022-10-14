from django.urls import include, path
from djoser.views import TokenDestroyView
from rest_framework.routers import DefaultRouter
from users.views import CustomTokenCreateView, CustomUserViewSet
from recipes.views import RecipeViewSet, IngredientViewSet, TagViewSet


v1_router = DefaultRouter()
v1_router.register('users', CustomUserViewSet, basename='user')
v1_router.register('recipes', RecipeViewSet, basename='recipes')
v1_router.register('ingredients', IngredientViewSet, basename='ingredients')
v1_router.register('tags', TagViewSet, basename='tags')

urlpatterns = [
    path('', include(v1_router.urls)),
    path('auth/token/login/', CustomTokenCreateView.as_view(), name='login'),
    path('auth/token/logout/', TokenDestroyView.as_view(), name='logout'),
]
