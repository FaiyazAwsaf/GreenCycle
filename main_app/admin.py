from django.contrib import admin
from .models import RecyclingCenter, Category, MarketplaceItem, UserPreference, ItemRecommendation

# Register your models here.
admin.site.register(RecyclingCenter)
admin.site.register(Category)
admin.site.register(MarketplaceItem)
admin.site.register(UserPreference)
admin.site.register(ItemRecommendation)
