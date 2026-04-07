from rest_framework import serializers
from .models import User, SnackItem, Order, OrderItem

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['id', 'name', 'email', 'role', 'is_active']

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model  = User
        fields = ['name', 'email', 'password', 'role']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class SnackItemSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model  = SnackItem
        fields = '__all__'

    def get_image_url(self, obj):
        if obj.image:
            url = obj.image.url
            # Cloudinary URLs are already absolute, return directly
            if url.startswith('http'):
                return url
            # Local fallback: build absolute URI
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(url)
            return url
        return None

class OrderItemSerializer(serializers.ModelSerializer):
    snack_name  = serializers.CharField(source='snack.name', read_only=True)
    snack_price = serializers.DecimalField(source='snack.price', max_digits=8, decimal_places=2, read_only=True)

    class Meta:
        model  = OrderItem
        fields = ['id', 'snack', 'snack_name', 'snack_price', 'quantity']

class OrderSerializer(serializers.ModelSerializer):
    items     = OrderItemSerializer(many=True)
    user_name = serializers.CharField(source='user.name', read_only=True)
    total     = serializers.SerializerMethodField()

    class Meta:
        model  = Order
        fields = ['id', 'user', 'user_name', 'date', 'is_locked', 'items', 'total']
        read_only_fields = ['user', 'is_locked']

    def get_total(self, obj):
        return sum(float(i.snack.price * i.quantity) for i in obj.items.all())

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            if item_data.get('quantity', 0) > 0:
                OrderItem.objects.create(order=order, **item_data)
        return order