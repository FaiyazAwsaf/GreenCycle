from django.shortcuts import render, redirect
from django.contrib import messages
from .models_waste import WasteGeneration, WastePrediction
from .services.waste_prediction_service import WastePredictionService

def predictions(request):
    # Get available locations
    locations = WastePredictionService.get_available_locations()
    
    # Default values
    selected_location = None
    days = 7
    predictions = None
    
    if request.method == 'POST':
        # Get form data
        selected_location = request.POST.get('location')
        days = int(request.POST.get('days', 7))
        
        # Validate input
        if not selected_location:
            messages.error(request, 'Please select a location')
        elif days < 1 or days > 7:
            messages.error(request, 'Days must be between 1 and 7')
        else:
            # Generate predictions
            try:
                WastePredictionService.generate_predictions(days=days, location=selected_location)
                predictions = WastePredictionService.get_predictions(selected_location, days)
                messages.success(request, f'Successfully generated predictions for {selected_location}')
            except Exception as e:
                messages.error(request, f'Error generating predictions: {str(e)}')
    
    context = {
        'locations': locations,
        'selected_location': selected_location,
        'days': days,
        'predictions': predictions,
        'title': 'Waste Generation Predictions'
    }
    
    return render(request, 'main_app/predictions.html', context)