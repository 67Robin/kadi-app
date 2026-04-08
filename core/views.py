from datetime import time
from django.db.models import Sum
from django.utils import timezone
from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.conf import settings
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings as django_settings

from .models import User, SnackItem, Order, OrderItem
from .serializers import (
    UserSerializer, UserCreateSerializer,
    SnackItemSerializer, OrderSerializer
)

CUTOFF_TIME = time(23, 30)

def is_before_cutoff():
    return timezone.localtime().time() < CUTOFF_TIME

class IsAdminRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'admin'

from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

class SnackItemViewSet(viewsets.ModelViewSet):
    serializer_class = SnackItemSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:  # admin
            return SnackItem.objects.all()
        return SnackItem.objects.filter(is_active=True)

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsAdminRole()]
        return [permissions.IsAuthenticated()]

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            date = self.request.query_params.get('date')
            qs = Order.objects.prefetch_related('items__snack')
            if date:
                qs = qs.filter(date=date)
            return qs
        return Order.objects.filter(user=user).prefetch_related('items__snack')

    def perform_create(self, serializer):
        if not is_before_cutoff():
            raise PermissionDenied("Order window closed. Deadline is 10:30 AM.")
        today = timezone.localdate()
        if Order.objects.filter(user=self.request.user, date=today).exists():
            raise PermissionDenied("You already have an order for today.")
        serializer.save(user=self.request.user, date=today)

    def perform_update(self, serializer):
        order = self.get_object()
        if order.is_locked and self.request.user.role != 'admin':
            raise PermissionDenied("Orders are locked.")
        if not is_before_cutoff() and self.request.user.role != 'admin':
            raise PermissionDenied("Past cutoff time.")
        serializer.save()


@api_view(['GET'])
@permission_classes([IsAdminRole])
def aggregated_order(request):
    date_str = request.query_params.get('date')

    # ✅ FIX 1: Proper date parsing
    try:
        if date_str and date_str != "undefined":
            date = datetime.fromisoformat(date_str).date()
        else:
            date = timezone.localdate()
    except Exception as e:
        print("DATE ERROR:", date_str, e)
        date = timezone.localdate() 

    # ✅ FIX 2: Correct filtering
    people_count = Order.objects.filter(date=date).count()

    data = OrderItem.objects.filter(
        order__date=date,
        quantity__gt=0
    ).values(
        'snack__name', 'snack__price', 'snack__image'
    ).annotate(
        total_qty=Sum('quantity')
    ).order_by('-total_qty')

    items = []
    for item in data:
        image_url = None
        raw = item.get('snack__image')

        # ✅ FIX 3: Safe image handling
        if raw:
            raw = str(raw)
            if raw.startswith('http'):
                image_url = raw
            else:
                import cloudinary
                cloud_name = cloudinary.config().cloud_name
                image_url = f"https://res.cloudinary.com/{cloud_name}/image/upload/{raw}"

        items.append({
            'snack__name': item['snack__name'],
            'snack__price': str(item['snack__price']),
            'snack__image_url': image_url,
            'total_qty': item['total_qty'] or 0,  # ✅ FIX 4
        })

    return Response({
        'date': str(date),
        'items': items,
        'people_count': people_count
    })

@api_view(['GET'])
def monthly_summary(request, year, month):
    user = request.user
    user_id = request.query_params.get('user_id')
    if user_id and request.user.role == 'admin':
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

    items = OrderItem.objects.filter(
        order__user=user,
        order__date__year=year,
        order__date__month=month,
        quantity__gt=0
    ).values('snack__name', 'snack__price').annotate(total_qty=Sum('quantity'))

    total = sum(float(i['snack__price']) * i['total_qty'] for i in items)
    return Response({
        'user': user.name,
        'year': year,
        'month': month,
        'items': list(items),
        'total': round(total, 2)
    })

@api_view(['GET'])
@permission_classes([IsAdminRole])
def users_list(request):
    users = User.objects.filter(is_active=True)
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)

from django.shortcuts import render

def login_view(request):
    return render(request, 'core/login.html')

def dashboard_view(request):
    return render(request, 'core/dashboard.html')

@api_view(['GET'])
def me(request):
    return Response({
        'name': request.user.name,
        'email': request.user.email,
        'role': request.user.role,
    })

def admin_dashboard_view(request):
    return render(request, 'core/admin/dashboard.html')

def reports_view(request):
    return render(request, 'core/admin/reports.html')

@api_view(['POST'])
@permission_classes([IsAdminRole])
def create_user(request):
    serializer = UserCreateSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)

@api_view(['POST'])
@permission_classes([IsAdminRole])
def toggle_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        user.is_active = not user.is_active
        user.save()
        return Response({'status': 'updated'})
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=404)

def users_management_view(request):
    return render(request, 'core/admin/users.html')

def snacks_management_view(request):
    return render(request, 'core/admin/snacks.html')

def history_view(request):
    today = timezone.localdate()

    data = OrderItem.objects.filter(
        order__date=today,
        quantity__gt=0
    ).values(
        'snack__name',
        'snack__price',
        'snack__image',   
    ).annotate(
        total_qty=Sum('quantity')
    )

    items = []

    for item in data:
        image_url = None
        raw = item.get('snack__image')

        if raw:
            raw = str(raw)
            if raw.startswith('http'):
                image_url = raw
            else:
                import cloudinary
                cloud_name = cloudinary.config().cloud_name
                image_url = f"https://res.cloudinary.com/{cloud_name}/image/upload/{raw}"

        items.append({
            'name': item['snack__name'],
            'price': item['snack__price'],
            'image_url': image_url,   
            'qty': item['total_qty'],
        })

    return render(request, 'core/history.html', {
        'items': items
    })
def reconciliation_view(request):
    return render(request, 'core/admin/reconciliation.html')

@api_view(['DELETE'])
def cancel_order(request):
    if not is_before_cutoff():
        raise PermissionDenied("Cannot cancel after 10:30 AM.")
    today = timezone.localdate()
    try:
        order = Order.objects.get(user=request.user, date=today)
        order.delete()
        return Response({'message': 'Order cancelled successfully'})
    except Order.DoesNotExist:
        return Response({'error': 'No order found for today'}, status=404)