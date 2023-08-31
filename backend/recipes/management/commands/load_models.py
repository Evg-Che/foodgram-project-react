import json
import os

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    _FILE_PATH = os.path.join('recipes/data', 'ingredients.json')

    def handle(self, *args, **options):
        if Ingredient.objects.exists():
            print('Данные уже загружены в базу данных Foodgram.')
            return

        try:
            self.load_models()
        except FileNotFoundError:
            print(f'Файл {self.FILE_PATH} не найден')
        except Exception as err:
            print(f'Не удалось загрузить данные: {err}')
        else:
            print('Данные успешно добавлены в базу данных Foodgram.')

    def load_models(self):
        with open(self._FILE_PATH, 'r', encoding='UTF-8') as file:
            data = json.load(file)
            Ingredient.objects.bulk_create(
                [Ingredient(name=ingredient['name'],
                            measurement_unit=ingredient['measurement_unit'])
                 for ingredient in data]
            )
