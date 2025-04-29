from django.urls import path
from . import views_json as views  # Use JSON-based views instead of Django ORM
from . import views_waste
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('map/', views.map_view, name='map'),
    path('marketplace/', views.marketplace, name='marketplace'),
    path('marketplace/item/<int:item_id>/', views.item_detail, name='item_detail'),
    path('marketplace/add/', views.add_item, name='add_item'),
    path('marketplace/my-items/', views.my_items, name='my_items'),
    path('marketplace/update/<int:item_id>/', views.update_item, name='update_item'),
    path('marketplace/delete/<int:item_id>/', views.delete_item, name='delete_item'),
    path('marketplace/search/', views.search_items, name='search_items'),
    path('marketplace/preferences/', views.user_preferences, name='user_preferences'),
    
    # Waste prediction routes
    path('predictions/', views_waste.predictions, name='predictions'),
]

# Add media URL configuration if settings.DEBUG is True
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
