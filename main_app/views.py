from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from .models import RecyclingCenter, MarketplaceItem, Category, UserPreference, ItemRecommendation
from django.contrib.auth.models import User
import numpy as np
from django.contrib.auth.forms import UserCreationForm

# Create your views here.
def home(request):
    return render(request, 'main_app/home.html', {'title': 'Hackathon Project Home'})

# User Registration View
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'main_app/register.html', {'form': form, 'title': 'Register'})

def map_view(request):
    centers = RecyclingCenter.objects.filter(is_active=True)
    return render(request, 'main_app/map.html', {'centers': centers})

# Marketplace Views
def marketplace(request):
    categories = Category.objects.all()
    featured_items = MarketplaceItem.objects.filter(is_featured=True, status='available')[:4]
    recent_items = MarketplaceItem.objects.filter(status='available').order_by('-created_at')[:8]
    
    # Get recommendations if user is authenticated
    recommended_items = []
    if request.user.is_authenticated:
        recommendations = ItemRecommendation.objects.filter(
            user=request.user, 
            item__status='available'
        ).order_by('-score')[:4]
        recommended_items = [rec.item for rec in recommendations]
    
    context = {
        'categories': categories,
        'featured_items': featured_items,
        'recent_items': recent_items,
        'recommended_items': recommended_items,
        'title': 'Marketplace - Exchange Reusable Items'
    }
    return render(request, 'main_app/marketplace.html', context)

def item_detail(request, item_id):
    item = get_object_or_404(MarketplaceItem, id=item_id)
    
    # Increment view count
    item.views_count += 1
    item.save()
    
    # Get similar items based on category
    similar_items = MarketplaceItem.objects.filter(
        category=item.category, 
        status='available'
    ).exclude(id=item.id)[:4]
    
    context = {
        'item': item,
        'similar_items': similar_items,
        'title': f'{item.title} - Marketplace'
    }
    
    # Update recommendations if user is authenticated
    if request.user.is_authenticated and request.user != item.owner:
        update_recommendations(request.user, item)
    
    return render(request, 'main_app/item_detail.html', context)

@login_required
def add_item(request):
    categories = Category.objects.all()
    
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
        
        # Create new item
        category = get_object_or_404(Category, id=category_id)
        item = MarketplaceItem(
            title=title,
            description=description,
            category=category,
            condition=condition,
            owner=request.user,
            location=location,
            image=image
        )
        item.save()
        
        messages.success(request, 'Item added successfully!')
        return redirect('item_detail', item_id=item.id)
    
    return render(request, 'main_app/add_item.html', {
        'categories': categories,
        'title': 'Add New Item'
    })

@login_required
def my_items(request):
    items = MarketplaceItem.objects.filter(owner=request.user).order_by('-created_at')
    return render(request, 'main_app/my_items.html', {
        'items': items,
        'title': 'My Items'
    })

@login_required
def update_item(request, item_id):
    item = get_object_or_404(MarketplaceItem, id=item_id, owner=request.user)
    categories = Category.objects.all()
    
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
        
        # Update item
        category = get_object_or_404(Category, id=category_id)
        item.title = title
        item.description = description
        item.category = category
        item.condition = condition
        item.location = location
        item.status = status
        if image:
            item.image = image
        
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
    item = get_object_or_404(MarketplaceItem, id=item_id, owner=request.user)
    
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
    
    items = MarketplaceItem.objects.filter(status='available')
    
    if query:
        items = items.filter(Q(title__icontains=query) | Q(description__icontains=query))
    
    if category_id:
        items = items.filter(category_id=category_id)
    
    if condition:
        items = items.filter(condition=condition)
    
    if location:
        items = items.filter(location__icontains=location)
    
    categories = Category.objects.all()
    
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
    preferences, created = UserPreference.objects.get_or_create(user=request.user)
    categories = Category.objects.all()
    
    if request.method == 'POST':
        preferred_categories = request.POST.getlist('preferred_categories')
        preferred_conditions = request.POST.get('preferred_conditions')
        preferred_locations = request.POST.get('preferred_locations')
        
        # Update preferences
        preferences.preferred_categories.clear()
        for category_id in preferred_categories:
            category = get_object_or_404(Category, id=category_id)
            preferences.preferred_categories.add(category)
        
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
        preferences = UserPreference.objects.get(user=user)
    except UserPreference.DoesNotExist:
        # Create default preferences if they don't exist
        preferences = UserPreference.objects.create(user=user)
        preferences.preferred_categories.add(viewed_item.category)
    
    # Get all available items not owned by the user
    available_items = MarketplaceItem.objects.filter(
        status='available'
    ).exclude(owner=user)
    
    for item in available_items:
        # Calculate recommendation score
        score = calculate_recommendation_score(user, item, preferences, viewed_item)
        
        # Update or create recommendation
        recommendation, created = ItemRecommendation.objects.get_or_create(
            user=user,
            item=item,
            defaults={'score': score}
        )
        
        if not created:
            # Update existing recommendation score
            recommendation.score = (recommendation.score + score) / 2  # Average with previous score
            recommendation.save()

def calculate_recommendation_score(user, item, preferences, viewed_item=None):
    """Calculate recommendation score based on user preferences and behavior"""
    score = 0.0
    
    # Category preference (highest weight)
    if item.category in preferences.preferred_categories.all():
        score += 0.4
    
    # Condition preference
    if preferences.preferred_conditions:
        preferred_conditions_list = [c.strip() for c in preferences.preferred_conditions.split(',')]
        if item.condition in preferred_conditions_list:
            score += 0.2
    
    # Location preference
    if preferences.preferred_locations:
        preferred_locations_list = [l.strip() for l in preferences.preferred_locations.split(',')]
        if item.location in preferred_locations_list:
            score += 0.2
    
    # Similarity to viewed item
    if viewed_item:
        # Same category as viewed item
        if item.category == viewed_item.category:
            score += 0.1
        
        # Similar condition
        if item.condition == viewed_item.condition:
            score += 0.05
        
        # Similar location
        if item.location == viewed_item.location:
            score += 0.05
    
    # Add some randomness to avoid recommendation bubbles
    score += np.random.uniform(0, 0.1)
    
    return min(score, 1.0)  # Cap at 1.0
