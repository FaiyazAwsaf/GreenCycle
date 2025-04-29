from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from .models_json import RecyclingCenter, MarketplaceItem, Category, UserPreference, ItemRecommendation, User
import numpy as np
from django.contrib.auth.forms import UserCreationForm

# Helper function to mimic Django's get_object_or_404
def get_json_object_or_404(model_class, **kwargs):
    try:
        return model_class.get(**kwargs)
    except model_class.DoesNotExist:
        raise Http404(f"{model_class.__name__} not found.")

# Create your views here.
def home(request):
    return render(request, 'main_app/home.html', {'title': 'Hackathon Project Home'})

# User Registration View
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create a corresponding user in our JSON storage
            User.create(
                id=user.id,
                username=user.username,
                email=getattr(user, 'email', ''),
                first_name=getattr(user, 'first_name', ''),
                last_name=getattr(user, 'last_name', '')
            )
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'main_app/register.html', {'form': form, 'title': 'Register'})

def map_view(request):
    centers = RecyclingCenter.filter(is_active=True)
    return render(request, 'main_app/map.html', {'centers': centers})

# Marketplace Views
def marketplace(request):
    categories = Category.all()
    
    # Get featured and recent items
    all_items = MarketplaceItem.filter(status='available')
    featured_items = [item for item in all_items if item.is_featured][:4]
    
    # Sort recent items by created_at (descending)
    recent_items = sorted(
        all_items,
        key=lambda x: getattr(x, 'created_at', ''),
        reverse=True
    )[:8]
    
    # Get recommendations if user is authenticated
    recommended_items = []
    if request.user.is_authenticated:
        # Get user from our JSON storage
        try:
            json_user = User.get(id=request.user.id)
            recommendations = ItemRecommendation.filter(user_id=json_user.id)
            # Sort by score (descending)
            recommendations = sorted(
                recommendations,
                key=lambda x: getattr(x, 'score', 0),
                reverse=True
            )
            
            # Get available items only
            recommended_items = []
            for rec in recommendations[:4]:
                try:
                    item = MarketplaceItem.get(id=rec.item_id)
                    if item.status == 'available':
                        recommended_items.append(item)
                except MarketplaceItem.DoesNotExist:
                    continue
        except User.DoesNotExist:
            pass
    
    context = {
        'categories': categories,
        'featured_items': featured_items,
        'recent_items': recent_items,
        'recommended_items': recommended_items,
        'title': 'Marketplace - Exchange Reusable Items'
    }
    return render(request, 'main_app/marketplace.html', context)

def item_detail(request, item_id):
    item = get_json_object_or_404(MarketplaceItem, id=str(item_id))
    
    # Increment view count
    item.views_count = getattr(item, 'views_count', 0) + 1
    item.save()
    
    # Get similar items based on category
    similar_items = []
    if hasattr(item, 'category_id'):
        all_items = MarketplaceItem.filter(status='available')
        similar_items = [
            i for i in all_items 
            if hasattr(i, 'category_id') and i.category_id == item.category_id and i.id != item.id
        ][:4]
    
    context = {
        'item': item,
        'similar_items': similar_items,
        'title': f'{item.title} - Marketplace'
    }
    
    # Update recommendations if user is authenticated
    if request.user.is_authenticated:
        try:
            json_user = User.get(id=request.user.id)
            if json_user.id != getattr(item, 'owner_id', None):
                update_recommendations(json_user, item)
        except User.DoesNotExist:
            pass
    
    return render(request, 'main_app/item_detail.html', context)

@login_required
def add_item(request):
    categories = Category.all()
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        condition = request.POST.get('condition')
        location = request.POST.get('location')
        image = request.FILES.get('image')
        
        # Validate form data
        if not all([title, description, category_id, condition, location]):
            messages.error(request, 'Please fill all required fields')
            return render(request, 'main_app/add_item.html', {
                'categories': categories,
                'title': 'Add New Item'
            })
        
        # Get the category
        try:
            category = Category.get(id=category_id)
        except Category.DoesNotExist:
            messages.error(request, 'Invalid category')
            return render(request, 'main_app/add_item.html', {
                'categories': categories,
                'title': 'Add New Item'
            })
        
        # Create new item
        item_data = {
            'title': title,
            'description': description,
            'category_id': category.id,
            'condition': condition,
            'owner_id': request.user.id,
            'location': location,
            'status': 'available',
            'is_featured': False,
            'views_count': 0
        }
        
        # Handle image upload
        if image:
            # Save the image to media directory
            # Note: In a real implementation, you'd need to handle file storage
            # For now, we'll just store the image path
            item_data['image'] = f'marketplace_items/{image.name}'
        
        item = MarketplaceItem.create(**item_data)
        
        messages.success(request, 'Item added successfully!')
        return redirect('item_detail', item_id=item.id)
    
    return render(request, 'main_app/add_item.html', {
        'categories': categories,
        'title': 'Add New Item'
    })

@login_required
def my_items(request):
    # Get all items owned by the current user
    all_items = MarketplaceItem.filter(owner_id=str(request.user.id))
    
    # Sort by created_at (descending)
    items = sorted(
        all_items,
        key=lambda x: getattr(x, 'created_at', ''),
        reverse=True
    )
    
    return render(request, 'main_app/my_items.html', {
        'items': items,
        'title': 'My Items'
    })

@login_required
def update_item(request, item_id):
    # Get the item and verify ownership
    item = get_json_object_or_404(MarketplaceItem, id=str(item_id))
    if str(request.user.id) != getattr(item, 'owner_id', None):
        messages.error(request, 'You do not have permission to edit this item')
        return redirect('marketplace')
    
    categories = Category.all()
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        condition = request.POST.get('condition')
        location = request.POST.get('location')
        status = request.POST.get('status')
        image = request.FILES.get('image')
        
        # Validate form data
        if not all([title, description, category_id, condition, location, status]):
            messages.error(request, 'Please fill all required fields')
            return render(request, 'main_app/update_item.html', {
                'item': item,
                'categories': categories,
                'title': 'Update Item'
            })
        
        # Get the category
        try:
            category = Category.get(id=category_id)
        except Category.DoesNotExist:
            messages.error(request, 'Invalid category')
            return render(request, 'main_app/update_item.html', {
                'item': item,
                'categories': categories,
                'title': 'Update Item'
            })
        
        # Update item
        item.title = title
        item.description = description
        item.category_id = category.id
        item.condition = condition
        item.location = location
        item.status = status
        
        # Handle image upload
        if image:
            # Save the image to media directory
            # Note: In a real implementation, you'd need to handle file storage
            # For now, we'll just store the image path
            item.image = f'marketplace_items/{image.name}'
        
        item.save()
        
        messages.success(request, 'Item updated successfully!')
        return redirect('item_detail', item_id=item.id)
    
    return render(request, 'main_app/update_item.html', {
        'item': item,
        'categories': categories,
        'title': 'Update Item'
    })

@login_required
def delete_item(request, item_id):
    # Get the item and verify ownership
    item = get_json_object_or_404(MarketplaceItem, id=str(item_id))
    if str(request.user.id) != getattr(item, 'owner_id', None):
        messages.error(request, 'You do not have permission to delete this item')
        return redirect('marketplace')
    
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Item deleted successfully!')
        return redirect('my_items')
    
    return render(request, 'main_app/delete_item.html', {
        'item': item,
        'title': 'Delete Item'
    })

def search_items(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    condition = request.GET.get('condition', '')
    location = request.GET.get('location', '')
    
    # Get all available items
    items = MarketplaceItem.filter(status='available')
    
    # Apply filters
    if query:
        items = [item for item in items if 
                query.lower() in getattr(item, 'title', '').lower() or 
                query.lower() in getattr(item, 'description', '').lower()]
    
    if category_id:
        items = [item for item in items if 
                getattr(item, 'category_id', '') == category_id]
    
    if condition:
        items = [item for item in items if 
                getattr(item, 'condition', '') == condition]
    
    if location:
        items = [item for item in items if 
                location.lower() in getattr(item, 'location', '').lower()]
    
    categories = Category.all()
    
    return render(request, 'main_app/search_results.html', {
        'items': items,
        'categories': categories,
        'query': query,
        'category_id': category_id,
        'condition': condition,
        'location': location,
        'title': 'Search Results'
    })

@login_required
def user_preferences(request):
    # Get or create user preferences
    try:
        json_user = User.get(id=request.user.id)
        preferences = UserPreference.get(user_id=json_user.id)
    except (User.DoesNotExist, UserPreference.DoesNotExist):
        # Create default preferences
        preferences = UserPreference.create(
            user_id=str(request.user.id),
            preferred_category_ids=[],
            preferred_conditions='',
            preferred_locations=''
        )
    
    categories = Category.all()
    
    if request.method == 'POST':
        preferred_categories = request.POST.getlist('preferred_categories')
        preferred_conditions = request.POST.get('preferred_conditions')
        preferred_locations = request.POST.get('preferred_locations')
        
        # Update preferences
        preferences.preferred_category_ids = preferred_categories
        preferences.preferred_conditions = preferred_conditions
        preferences.preferred_locations = preferred_locations
        preferences.save()
        
        messages.success(request, 'Preferences updated successfully!')
        return redirect('marketplace')
    
    return render(request, 'main_app/user_preferences.html', {
        'preferences': preferences,
        'categories': categories,
        'title': 'My Preferences'
    })

# AI Recommendation Helper Functions
def update_recommendations(user, viewed_item):
    """Update recommendations based on user interaction with an item"""
    # Get user preferences
    try:
        preferences = UserPreference.get(user_id=user.id)
    except UserPreference.DoesNotExist:
        # Create default preferences if they don't exist
        preferences = UserPreference.create(
            user_id=user.id,
            preferred_category_ids=[viewed_item.category_id] if hasattr(viewed_item, 'category_id') else [],
            preferred_conditions='',
            preferred_locations=''
        )
    
    # Get all available items not owned by the user
    available_items = MarketplaceItem.filter(status='available')
    available_items = [item for item in available_items if getattr(item, 'owner_id', None) != user.id]
    
    for item in available_items:
        # Calculate recommendation score
        score = calculate_recommendation_score(user, item, preferences, viewed_item)
        
        # Update or create recommendation
        try:
            recommendation = ItemRecommendation.get(user_id=user.id, item_id=item.id)
            # Update existing recommendation score
            recommendation.score = (recommendation.score + score) / 2  # Average with previous score
            recommendation.save()
        except ItemRecommendation.DoesNotExist:
            # Create new recommendation
            ItemRecommendation.create(
                user_id=user.id,
                item_id=item.id,
                score=score,
                is_viewed=False
            )

def calculate_recommendation_score(user, item, preferences, viewed_item=None):
    """Calculate recommendation score based on user preferences and behavior"""
    score = 0.0
    
    # Category preference (highest weight)
    if hasattr(preferences, 'preferred_category_ids') and hasattr(item, 'category_id'):
        if item.category_id in preferences.preferred_category_ids:
            score += 0.4
    
    # Condition preference
    if hasattr(preferences, 'preferred_conditions') and preferences.preferred_conditions:
        preferred_conditions_list = [c.strip() for c in preferences.preferred_conditions.split(',')]
        if hasattr(item, 'condition') and item.condition in preferred_conditions_list:
            score += 0.2
    
    # Location preference
    if hasattr(preferences, 'preferred_locations') and preferences.preferred_locations:
        preferred_locations_list = [l.strip() for l in preferences.preferred_locations.split(',')]
        if hasattr(item, 'location'):
            for location in preferred_locations_list:
                if location.lower() in item.location.lower():
                    score += 0.2
                    break
    
    # Similarity to viewed item
    if viewed_item:
        # Same category as viewed item
        if hasattr(item, 'category_id') and hasattr(viewed_item, 'category_id'):
            if item.category_id == viewed_item.category_id:
                score += 0.1
        
        # Similar condition
        if hasattr(item, 'condition') and hasattr(viewed_item, 'condition'):
            if item.condition == viewed_item.condition:
                score += 0.05
        
        # Similar location
        if hasattr(item, 'location') and hasattr(viewed_item, 'location'):
            if item.location == viewed_item.location:
                score += 0.05
    
    # Add some randomness to avoid recommendation bubbles
    score += np.random.uniform(0, 0.1)
    
    return min(score, 1.0)  # Cap at 1.0