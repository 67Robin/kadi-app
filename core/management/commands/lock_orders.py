from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Order

class Command(BaseCommand):
    help = 'Lock all orders for today after cutoff time'

    def handle(self, *args, **options):
        today = timezone.localdate()
        updated = Order.objects.filter(
            date=today,
            is_locked=False
        ).update(is_locked=True)
        self.stdout.write(
            f'Locked {updated} orders for {today}'
        )