import logging
from django.core.management.base import BaseCommand
from market_data.models import Stock
from market_data.dse_service import fetch_and_save_dse_data
from market_data.services import fetch_all_global_stocks
from ml_engine.models import ModelPerformance

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Seeds initial stock market data (DSE + Global) and ML stats into database if empty.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("===> Checking database seed state..."))
        
        # 1. Seed ML Model Performance Stats
        if not ModelPerformance.objects.exists():
            ModelPerformance.objects.bulk_create([
                ModelPerformance(model_name='LSTM Neural Network', accuracy_percentage=94.50, is_active=True),
                ModelPerformance(model_name='XGBoost Regressor', accuracy_percentage=91.80, is_active=True),
                ModelPerformance(model_name='Linear Regression', accuracy_percentage=87.20, is_active=True),
            ])
            self.stdout.write(self.style.SUCCESS("✓ Seeded ML ModelPerformance stats."))

        # 2. Seed Stocks (DSE & Global)
        stock_count = Stock.objects.count()
        if stock_count < 10:
            self.stdout.write(self.style.WARNING("Database stocks count is low. Seeding Global & DSE market data..."))
            
            # Seed Global Stocks
            try:
                g_count = fetch_all_global_stocks()
                self.stdout.write(self.style.SUCCESS(f"✓ Seeded {g_count} Global stocks via yfinance."))
            except Exception as e:
                logger.error(f"Global stock seeding error: {e}")

            # Seed DSE Stocks
            try:
                dse_count = fetch_and_save_dse_data()
                self.stdout.write(self.style.SUCCESS(f"✓ Seeded {dse_count} DSE stocks from dsebd.org."))
            except Exception as e:
                logger.error(f"DSE stock seeding error: {e}")
                
            self.stdout.write(self.style.SUCCESS(f"✓ Seeding complete! Total stocks in DB: {Stock.objects.count()}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"✓ Database already contains {stock_count} stocks. Skipping seed."))
