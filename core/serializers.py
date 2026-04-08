from rest_framework import serializers
from .models import User, SnackItem, Order, OrderItem
import cloudinary

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
    image = serializers.ImageField(required=False)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = SnackItem
        fields = '__all__'

    def get_image_url(self, obj):
        try:
          request = self.context.get('request')
          if obj.image:
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url   
        except Exception:
            return None

    def update(self, instance, validated_data):
        image = validated_data.get('image', None)

        if image is not None:
            instance.image = image

        instance.name = validated_data.get('name', instance.name)
        instance.price = validated_data.get('price', instance.price)
        instance.is_active = validated_data.get('is_active', instance.is_active)

        instance.save()
        return instance

class OrderItemSerializer(serializers.ModelSerializer):
    snack_name  = serializers.CharField(source='snack.name', read_only=True)
    snack_price = serializers.DecimalField(source='snack.price', max_digits=8, decimal_places=2, read_only=True)
    snack_image_url = serializers.SerializerMethodField()

    class Meta:
        model  = OrderItem
        fields = ['id', 'snack', 'snack_name', 'snack_price', 'quantity', 'snack_image_url']

    def get_snack_image_url(self, obj):
        try:
            request = self.context.get('request')
            if obj.snack.image:
                if request:
                    return request.build_absolute_uri(obj.snack.image.url)
                return obj.snack.image.url
        except Exception:
            return None

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
