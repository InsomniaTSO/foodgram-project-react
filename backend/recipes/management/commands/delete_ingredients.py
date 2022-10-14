from django.core.management import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Удаляет все ингредиенты из базы данных."""
    help = "python manage.py delete_ingredients"

    def handle(self, *args, **options):
        print("Delete ingredients data")
        Ingredient.objects.all().delete()
   
