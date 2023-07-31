from django.views.generic import DetailView, ListView

from .models import Food


class FoodDetailView(DetailView):
    model = Food


class FoodListView(ListView):
    model = Food

    def get_queryset(self):
        return super().get_queryset().prefetch_related("translations")
