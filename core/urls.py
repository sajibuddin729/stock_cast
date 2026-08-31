from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView  # JWT এর জন্য
from portfolio.views import RegisterView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Auth APIs (Register, Login & Refresh Token)
    path('api/auth/register/', RegisterView.as_view(), name='auth_register'),
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Apps APIs
    path('api/market/', include('market_data.urls')),
    path('api/portfolio/', include('portfolio.urls')),
    path('api/ml/', include('ml_engine.urls')),
]
