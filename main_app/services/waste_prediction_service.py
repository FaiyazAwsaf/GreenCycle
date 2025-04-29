import pandas as pd
from datetime import datetime, timedelta
from prophet import Prophet
from main_app.models_waste import WasteGeneration, WastePrediction


class WastePredictionService:
    @staticmethod
    def load_historic_data():
        # Load data from WasteGeneration model
        waste_data = WasteGeneration.objects.all().order_by('timestamp')
        
        # Convert to DataFrame format required by Prophet
        # Ensure timestamps are timezone-naive
        data = {
            'ds': [record.timestamp.astimezone().replace(tzinfo=None) for record in waste_data],
            'y': [record.waste_generated_tons for record in waste_data],
            'location': [record.location for record in waste_data]
        }
        return pd.DataFrame(data)
    
    @staticmethod
    def train_model(df, location):
        # Filter data for specific location
        location_df = df[df['location'] == location][['ds', 'y']]
        
        # Create and train Prophet model
        model = Prophet()
        model.fit(location_df)
        return model
    
    @staticmethod
    def make_predictions(model, days=7):
        # Create future dates DataFrame - only include exactly the number of days requested
        future = pd.DataFrame()
        start_date = datetime.now() + timedelta(days=1)  # Start from tomorrow
        dates = [start_date + timedelta(days=i) for i in range(days)]
        future['ds'] = dates
        
        # Make predictions
        forecast = model.predict(future)
        return forecast
    
    @staticmethod
    def save_predictions(forecast, location):
        # Save each prediction to the database
        for _, row in forecast.iterrows():
            WastePrediction.objects.create(
                timestamp=row['ds'],
                location=location,
                predicted_waste_tons=row['yhat'],
                lower_bound=row['yhat_lower'],
                upper_bound=row['yhat_upper']
            )
    
    @classmethod
    def generate_predictions(cls, days=7, location=None):
        # Load historic data
        df = cls.load_historic_data()
        
        # Get unique locations
        if location:
            locations = [location]
        else:
            locations = df['location'].unique()
        
        # Generate predictions for each location
        for loc in locations:
            # Delete existing predictions for this location
            WastePrediction.objects.filter(location=loc).delete()
            
            # Train model for location
            model = cls.train_model(df, loc)
            
            # Make predictions
            forecast = cls.make_predictions(model, days)
            
            # Save predictions
            cls.save_predictions(forecast, loc)
            
        return True
    
    @staticmethod
    def get_available_locations():
        """Return a list of all locations with historical data"""
        return WasteGeneration.objects.values_list('location', flat=True).distinct()
    
    @staticmethod
    def get_predictions(location, days=7):
        """Get existing predictions for a location"""
        # Get current date
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        # Add one more day to ensure we get the full requested number of future days
        end_date = start_date + timedelta(days=days+1)
        
        # Get predictions - using lte instead of lt to include the end date
        predictions = WastePrediction.objects.filter(
            location=location,
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).order_by('timestamp')
        
        return predictions