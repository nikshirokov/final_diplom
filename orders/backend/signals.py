from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Order
from django.utils import timezone

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_basket(sender, instance, created, **kwargs):
    """
    Автоматически создает корзину (заказ со статусом 'basket')
    при регистрации нового пользователя
    """
    if created:
        Order.objects.get_or_create(
            user=instance,
            status='basket',
            defaults={'dt': timezone.now()}
        )