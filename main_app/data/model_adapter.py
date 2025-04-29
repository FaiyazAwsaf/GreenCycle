from .json_manager import (
    get_all_items, get_item_by_id, create_item, update_item, delete_item,
    get_related_items, get_many_to_many_related_items, sort_items
)
import os
from datetime import datetime

# Model adapter classes to mimic Django ORM behavior but use JSON files

class ModelAdapter:
    """Base adapter class for all models"""
    file_name = None  # Override in subclasses
    
    @classmethod
    def objects(cls):
        """Return a QuerySetAdapter for this model"""
        return QuerySetAdapter(cls)
    
    @classmethod
    def get(cls, **kwargs):
        """Get a single object that matches the criteria"""
        items = get_all_items(cls.file_name, kwargs)
        if not items:
            raise DoesNotExist(f"{cls.__name__} matching query does not exist.")
        return cls(**items[0])
    
    @classmethod
    def filter(cls, **kwargs):
        """Filter objects based on criteria"""
        return QuerySetAdapter(cls, filters=kwargs)
    
    @classmethod
    def all(cls):
        """Get all objects"""
        return QuerySetAdapter(cls)
    
    @classmethod
    def create(cls, **kwargs):
        """Create a new object"""
        item_data = create_item(cls.file_name, kwargs)
        return cls(**item_data)
    
    def save(self):
        """Save the object to the JSON file"""
        if hasattr(self, 'id') and self.id:
            # Update existing object
            data = self.__dict__.copy()
            updated_data = update_item(self.__class__.file_name, self.id, data)
            if updated_data:
                self.__dict__.update(updated_data)
        else:
            # Create new object
            data = self.__dict__.copy()
            created_data = create_item(self.__class__.file_name, data)
            self.__dict__.update(created_data)
        return self
    
    def delete(self):
        """Delete the object from the JSON file"""
        if hasattr(self, 'id') and self.id:
            return delete_item(self.__class__.file_name, self.id)
        return None


class QuerySetAdapter:
    """Adapter to mimic Django's QuerySet behavior"""
    def __init__(self, model_class, filters=None, order_by=None):
        self.model_class = model_class
        self.filters = filters or {}
        self.order_by_field = order_by
        self._result_cache = None
    
    def filter(self, **kwargs):
        """Filter the queryset"""
        new_filters = self.filters.copy()
        new_filters.update(kwargs)
        return QuerySetAdapter(self.model_class, filters=new_filters, order_by=self.order_by_field)
    
    def exclude(self, **kwargs):
        """Exclude items matching criteria (simplified implementation)"""
        # This is a simplified implementation that doesn't fully mimic Django's exclude
        results = self._fetch_results()
        filtered_results = []
        for item in results:
            exclude_item = False
            for key, value in kwargs.items():
                if key in item and item[key] == value:
                    exclude_item = True
                    break
            if not exclude_item:
                filtered_results.append(item)
        
        # Create a new queryset with the filtered results
        qs = QuerySetAdapter(self.model_class, filters=self.filters, order_by=self.order_by_field)
        qs._result_cache = filtered_results
        return qs
    
    def get(self, **kwargs):
        """Get a single object"""
        new_filters = self.filters.copy()
        new_filters.update(kwargs)
        items = get_all_items(self.model_class.file_name, new_filters)
        if not items:
            raise DoesNotExist(f"{self.model_class.__name__} matching query does not exist.")
        if len(items) > 1:
            raise MultipleObjectsReturned(f"get() returned more than one {self.model_class.__name__}")
        return self.model_class(**items[0])
    
    def order_by(self, field):
        """Order the queryset by a field"""
        return QuerySetAdapter(self.model_class, filters=self.filters, order_by=field)
    
    def first(self):
        """Get the first object"""
        results = self._fetch_results()
        if not results:
            return None
        return self.model_class(**results[0])
    
    def last(self):
        """Get the last object"""
        results = self._fetch_results()
        if not results:
            return None
        return self.model_class(**results[-1])
    
    def count(self):
        """Count the number of objects"""
        return len(self._fetch_results())
    
    def exists(self):
        """Check if any objects exist"""
        return bool(self._fetch_results())
    
    def _fetch_results(self):
        """Fetch results from JSON file"""
        if self._result_cache is None:
            results = get_all_items(self.model_class.file_name, self.filters)
            if self.order_by_field:
                reverse = False
                field = self.order_by_field
                if field.startswith('-'):
                    reverse = True
                    field = field[1:]
                results = sort_items(results, field, reverse)
            self._result_cache = results
        return self._result_cache
    
    def __iter__(self):
        """Iterate through the queryset"""
        results = self._fetch_results()
        for item in results:
            yield self.model_class(**item)
    
    def __getitem__(self, k):
        """Get an item or slice"""
        if isinstance(k, slice):
            results = self._fetch_results()[k]
            return [self.model_class(**item) for item in results]
        else:
            return self.model_class(**self._fetch_results()[k])
    
    def __len__(self):
        """Get the length of the queryset"""
        return len(self._fetch_results())


# Exception classes to mimic Django's exceptions
class DoesNotExist(Exception):
    pass

class MultipleObjectsReturned(Exception):
    pass


# Model adapter implementations for each model
class RecyclingCenterAdapter(ModelAdapter):
    file_name = 'recycling_centers'
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def __str__(self):
        return self.name


class CategoryAdapter(ModelAdapter):
    file_name = 'categories'
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def __str__(self):
        return self.name
    
    @property
    def items(self):
        """Get related marketplace items"""
        return MarketplaceItemAdapter.filter(category_id=self.id)


class MarketplaceItemAdapter(ModelAdapter):
    file_name = 'marketplace_items'
    
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('pending', 'Pending Exchange'),
        ('exchanged', 'Exchanged'),
    )
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def __str__(self):
        return self.title
    
    @property
    def category(self):
        """Get the related category"""
        if hasattr(self, 'category_id'):
            try:
                return CategoryAdapter.get(id=self.category_id)
            except DoesNotExist:
                return None
        return None
    
    @property
    def owner(self):
        """Get the related user"""
        if hasattr(self, 'owner_id'):
            try:
                return UserAdapter.get(id=self.owner_id)
            except DoesNotExist:
                return None
        return None


class UserPreferenceAdapter(ModelAdapter):
    file_name = 'user_preferences'
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
            
        # Initialize preferred_categories as empty list if not provided
        if not hasattr(self, 'preferred_category_ids'):
            self.preferred_category_ids = []
    
    def __str__(self):
        username = "Unknown"
        if hasattr(self, 'user_id'):
            try:
                user = UserAdapter.get(id=self.user_id)
                username = user.username
            except DoesNotExist:
                pass
        return f"{username}'s preferences"
    
    @property
    def user(self):
        """Get the related user"""
        if hasattr(self, 'user_id'):
            try:
                return UserAdapter.get(id=self.user_id)
            except DoesNotExist:
                return None
        return None
    
    @property
    def preferred_categories(self):
        """Get the preferred categories"""
        class CategoryManager:
            def __init__(self, adapter):
                self.adapter = adapter
            
            def all(self):
                if hasattr(self.adapter, 'preferred_category_ids'):
                    categories = []
                    for cat_id in self.adapter.preferred_category_ids:
                        try:
                            categories.append(CategoryAdapter.get(id=cat_id))
                        except DoesNotExist:
                            pass
                    return categories
                return []
            
            def add(self, category):
                if not hasattr(self.adapter, 'preferred_category_ids'):
                    self.adapter.preferred_category_ids = []
                
                if hasattr(category, 'id'):
                    if category.id not in self.adapter.preferred_category_ids:
                        self.adapter.preferred_category_ids.append(category.id)
                        self.adapter.save()
            
            def remove(self, category):
                if hasattr(self.adapter, 'preferred_category_ids') and hasattr(category, 'id'):
                    if category.id in self.adapter.preferred_category_ids:
                        self.adapter.preferred_category_ids.remove(category.id)
                        self.adapter.save()
            
            def clear(self):
                self.adapter.preferred_category_ids = []
                self.adapter.save()
        
        return CategoryManager(self)


class ItemRecommendationAdapter(ModelAdapter):
    file_name = 'item_recommendations'
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def __str__(self):
        user_str = "Unknown"
        item_str = "Unknown"
        
        if hasattr(self, 'user_id'):
            try:
                user = UserAdapter.get(id=self.user_id)
                user_str = user.username
            except DoesNotExist:
                pass
        
        if hasattr(self, 'item_id'):
            try:
                item = MarketplaceItemAdapter.get(id=self.item_id)
                item_str = item.title
            except DoesNotExist:
                pass
        
        return f"Recommendation for {user_str}: {item_str}"
    
    @property
    def user(self):
        """Get the related user"""
        if hasattr(self, 'user_id'):
            try:
                return UserAdapter.get(id=self.user_id)
            except DoesNotExist:
                return None
        return None
    
    @property
    def item(self):
        """Get the related item"""
        if hasattr(self, 'item_id'):
            try:
                return MarketplaceItemAdapter.get(id=self.item_id)
            except DoesNotExist:
                return None
        return None


# User adapter to handle Django's User model
class UserAdapter(ModelAdapter):
    file_name = 'users'
    DoesNotExist = DoesNotExist
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def __str__(self):
        return self.username
    
    @property
    def items(self):
        """Get user's marketplace items"""
        return MarketplaceItemAdapter.filter(owner_id=self.id)
    
    @property
    def preference(self):
        """Get user's preferences"""
        try:
            return UserPreferenceAdapter.get(user_id=self.id)
        except DoesNotExist:
            # Create default preferences
            return UserPreferenceAdapter.create(user_id=self.id, preferred_category_ids=[])
    
    @property
    def recommendations(self):
        """Get user's recommendations"""
        return ItemRecommendationAdapter.filter(user_id=self.id)

