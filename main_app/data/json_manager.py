import os
import json
from datetime import datetime
import uuid

# Base directory for all JSON data files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ensure all data files exist
def ensure_data_files():
    """Ensure all required JSON data files exist"""
    data_files = {
        'recycling_centers': [],
        'categories': [],
        'marketplace_items': [],
        'user_preferences': [],
        'item_recommendations': []
    }
    
    for file_name, default_data in data_files.items():
        file_path = os.path.join(BASE_DIR, f"{file_name}.json")
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump(default_data, f, indent=4)

# Initialize data files
ensure_data_files()

# Generic CRUD operations for JSON files
def load_data(file_name):
    """Load data from a JSON file"""
    file_path = os.path.join(BASE_DIR, f"{file_name}.json")
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # If file doesn't exist or is invalid, create a new one
        with open(file_path, 'w') as f:
            json.dump([], f, indent=4)
        return []

def save_data(file_name, data):
    """Save data to a JSON file"""
    file_path = os.path.join(BASE_DIR, f"{file_name}.json")
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def create_item(file_name, item_data):
    """Create a new item in a JSON file"""
    data = load_data(file_name)
    
    # Generate a unique ID if not provided
    if 'id' not in item_data:
        item_data['id'] = str(uuid.uuid4())
    
    # Add timestamps
    now = datetime.now().isoformat()
    item_data['created_at'] = now
    item_data['updated_at'] = now
    
    data.append(item_data)
    save_data(file_name, data)
    return item_data

def get_all_items(file_name, filters=None):
    """Get all items from a JSON file with optional filtering"""
    data = load_data(file_name)
    
    if not filters:
        return data
    
    # Apply filters
    filtered_data = data
    for key, value in filters.items():
        if '__' in key:  # Handle special filters like field__contains
            field, operator = key.split('__')
            if operator == 'contains':
                filtered_data = [item for item in filtered_data if field in item and value.lower() in str(item[field]).lower()]
            elif operator == 'exact':
                filtered_data = [item for item in filtered_data if field in item and item[field] == value]
            elif operator == 'in':
                filtered_data = [item for item in filtered_data if field in item and item[field] in value]
        else:  # Simple equality filter
            filtered_data = [item for item in filtered_data if key in item and item[key] == value]
    
    return filtered_data

def get_item_by_id(file_name, item_id):
    """Get a single item by ID"""
    data = load_data(file_name)
    for item in data:
        if item.get('id') == item_id:
            return item
    return None

def update_item(file_name, item_id, updated_data):
    """Update an existing item"""
    data = load_data(file_name)
    for i, item in enumerate(data):
        if item.get('id') == item_id:
            # Update the item but preserve id and created_at
            updated_data['id'] = item_id
            if 'created_at' in item:
                updated_data['created_at'] = item['created_at']
            updated_data['updated_at'] = datetime.now().isoformat()
            
            data[i] = updated_data
            save_data(file_name, data)
            return updated_data
    return None

def delete_item(file_name, item_id):
    """Delete an item by ID"""
    data = load_data(file_name)
    for i, item in enumerate(data):
        if item.get('id') == item_id:
            deleted_item = data.pop(i)
            save_data(file_name, data)
            return deleted_item
    return None

# Specialized functions for relationships
def get_related_items(file_name, related_field, related_id):
    """Get items related to another item"""
    data = load_data(file_name)
    return [item for item in data if related_field in item and item[related_field] == related_id]

def get_many_to_many_related_items(file_name, relation_field, item_ids):
    """Get items with many-to-many relationships"""
    data = load_data(file_name)
    return [item for item in data if relation_field in item and any(rel_id in item[relation_field] for rel_id in item_ids)]

# Sorting and pagination
def sort_items(items, sort_by, reverse=False):
    """Sort items by a field"""
    if sort_by.startswith('-'):
        sort_by = sort_by[1:]
        reverse = True
    
    return sorted(items, key=lambda x: x.get(sort_by, ''), reverse=reverse)

def paginate_items(items, page=1, per_page=10):
    """Paginate items"""
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end]