from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.utils import timezone

class HealthCheckView(APIView):
    """
    24/7 Keep-Alive & Server Health Check API.
    Used by UptimeRobot / CronJobs / App Keep-Alive to prevent Render Free Tier from spinning down.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({
            "status": "online",
            "server": "StockCast Production Backend",
            "message": "Render backend is 24/7 active and awake",
            "timestamp": timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
