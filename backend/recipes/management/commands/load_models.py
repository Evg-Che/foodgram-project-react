import json

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    _FILE_PATH = 'recipes/data/ingredients.json'

    def handle(self, *args, **options):
        with open(self._FILE_PATH, 'r', encoding='UTF-8') as file:
            data = json.load(file)
            Ingredient.objects.bulk_create(
                [Ingredient(name=ingredient['name'],
                            measurement_unit=ingredient['measurement_unit'])
                 for ingredient in data]
            )
