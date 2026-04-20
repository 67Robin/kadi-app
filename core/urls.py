from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views
from .views import generate_whatsapp_message, mark_as_ordered,send_reset_link,reset_password_confirm

FRONTEND_URL = "https://kadi.up.railway.app"

router = DefaultRouter()
router.register(r'snacks', views.SnackItemViewSet, basename='snack')
router.register(r'orders', views.OrderViewSet, basename='order')

urlpatterns = [
    path('auth/login/', TokenObtainPairView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='refresh'),
    path('admin/aggregated/', views.aggregated_order, name='aggregated'),
    path('reports/monthly/<int:year>/<int:month>/', views.monthly_summary, name='monthly'),
    path('users/me/', views.me, name='me'),
    path('users/create/', views.create_user, name='create_user'),
    path('users/<int:user_id>/toggle/', views.toggle_user, name='toggle_user'),
    path('users/', views.users_list, name='users'),
    path('orders/cancel/', views.cancel_order, name='cancel_order'),
    path('', include(router.urls)),
    path('admin/whatsapp-message/', generate_whatsapp_message),
    path('admin/mark-ordered/', mark_as_ordered),
    path('history/', views.user_history),
    path('auth/reset-password/', send_reset_link),
    path('auth/reset-password-confirm/<uid>/<token>/', reset_password_confirm),
]