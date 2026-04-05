from django.contrib import admin
from .models import User, SnackItem, Order, OrderItem

admin.site.register(User)
admin.site.register(SnackItem)
admin.site.register(Order)
admin.site.register(OrderItem)
