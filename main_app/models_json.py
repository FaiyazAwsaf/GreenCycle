from .data.model_adapter import (
    RecyclingCenterAdapter, CategoryAdapter, MarketplaceItemAdapter,
    UserPreferenceAdapter, ItemRecommendationAdapter, UserAdapter
)

# JSON-based model replacements
RecyclingCenter = RecyclingCenterAdapter
Category = CategoryAdapter
MarketplaceItem = MarketplaceItemAdapter
UserPreference = UserPreferenceAdapter
ItemRecommendation = ItemRecommendationAdapter
User = UserAdapter

# This module serves as a drop-in replacement for Django's ORM models
# Import this instead of Django models when using JSON storage