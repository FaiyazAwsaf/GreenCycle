import csv
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from main_app.models_waste import WasteGeneration

class Command(BaseCommand):
    help = 'Import waste generation data from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        
        if not os.path.exists(csv_file):
            self.stdout.write(self.style.ERROR(f'File not found: {csv_file}'))
            return
        
        # Clear existing data (optional)
        # WasteGeneration.objects.all().delete()
        
        # Read CSV and import data
        count = 0
        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    # Parse the timestamp
                    timestamp = datetime.strptime(row['timestamp'], '%Y-%m-%d')
                    
                    # Create or update the waste generation record
                    waste_gen, created = WasteGeneration.objects.update_or_create(
                        timestamp=timestamp,
                        location=row['location'],
                        defaults={
                            'waste_generated_tons': float(row['waste_generated_tons'])
                        }
                    )
                    
                    if created:
                        count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error importing row: {row}. Error: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'Successfully imported {count} waste generation records'))