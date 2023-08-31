from django.contrib import admin

from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingList,
    Tag
)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'color',
        'slug'
    )
    list_filter = (
        'name',
    )
    search_fields = (
        'name',
        'slug'
    )


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit'
    )
    list_filter = (
        'name',
    )
    search_fields = (
        'name',
    )


@admin.register(IngredientInRecipe)
class IngredientInRecipeInlineAdmin(admin.TabularInline):
    model = IngredientInRecipe


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'author',
        'count_of_favorites'
    )
    list_filter = (
        'name',
        'author__username',
        'tags__name'
    )
    search_fields = (
        'name',
        'author__username',
        'tags__name'
    )
    readonly_fields = (
        'count_of_favorites',
    )
    inlines = [IngredientInRecipeInlineAdmin]

    def count_of_favorites(self, obj):
        return obj.favorites.count()

    count_of_favorites.short_description = 'Добавлено в избранное'


@admin.register(ShoppingList)
class ShoppingListAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe'
    )
    list_filter = (
        'recipe__tags',
    )
    search_fields = (
        'recipe__name',
        'user__username'
    )


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe'
    )
    list_filter = (
        'recipe__tags',
    )
    search_fields = (
        'recipe__name',
        'user__username'
    )
