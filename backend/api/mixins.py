from rest_framework import mixins, viewsets


class CustomViewSetMixin(mixins.ListModelMixin,
                         mixins.RetrieveModelMixin,
                         viewsets.GenericViewSet):
    """Класс миксин для TagViewSet и IngredientViewSet."""
    pass
