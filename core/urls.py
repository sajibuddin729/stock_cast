from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from portfolio.views import RegisterView, CustomTokenObtainPairView
from core.views import HealthCheckView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 24/7 Keep-Alive & Server Health Check APIs
    path('api/health/', HealthCheckView.as_view(), name='health-check'),
    path('api/ping/', HealthCheckView.as_view(), name='ping'),
    
    # Auth APIs (Register, Login & Refresh Token)
    path('api/auth/register/', RegisterView.as_view(), name='auth_register'),
    path('api/auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Apps APIs
    path('api/market/', include('market_data.urls')),
    path('api/portfolio/', include('portfolio.urls')),
    path('api/ml/', include('ml_engine.urls')),
]
