from django.contrib import admin
from .models import User, SnackItem, Order, OrderItem

admin.site.register(User)
admin.site.register(Order)
admin.site.register(OrderItem)
@admin.register(SnackItem)
class SnackAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'is_active']
    list_editable = ['is_active']