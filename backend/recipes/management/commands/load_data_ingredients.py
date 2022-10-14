import csv

from django.core.management import BaseCommand
from recipes.models import Ingredient

ALREDY_LOADED_ERROR_MESSAGE = """
If you need to reload the child data from the CSV file,
first delete the db.sqlite3 file to destroy the database.
Then, run `python manage.py migrate` for a new empty
database with tables"""


class Command(BaseCommand):
    """Добавляет данные из ingredients.csv в базу данных."""
    help = "python manage.py load_data_ingredients"

    def handle(self, *args, **options):
        if Ingredient.objects.exists():
            print('ingredients data already loaded...exiting.')
            print(ALREDY_LOADED_ERROR_MESSAGE)
            return
        print("Loading ingredients data")

        with open('ingredients.csv', encoding='utf-8') as file:
            csvfilereader = csv.reader(file, delimiter=",")
            for row in csvfilereader:
                ingredient = Ingredient(name=row[0], measurement_unit=row[1])
                ingredient.save()
