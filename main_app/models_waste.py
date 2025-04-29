from django.db import models

class WasteGeneration(models.Model):
    timestamp = models.DateTimeField()
    location = models.CharField(max_length=100)
    waste_generated_tons = models.FloatField()
    
    def __str__(self):
        return f"{self.location} - {self.timestamp.strftime('%Y-%m-%d')}: {self.waste_generated_tons} tons"
    
    class Meta:
        ordering = ['timestamp']
        unique_together = ('timestamp', 'location')

class WastePrediction(models.Model):
    timestamp = models.DateTimeField()
    location = models.CharField(max_length=100)
    predicted_waste_tons = models.FloatField()
    lower_bound = models.FloatField()
    upper_bound = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.location} - {self.timestamp.strftime('%Y-%m-%d')}: {self.predicted_waste_tons} tons"
    
    class Meta:
        ordering = ['timestamp']
        unique_together = ('timestamp', 'location')