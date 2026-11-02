from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone

class Migration(migrations.Migration):
    dependencies = [("storeextras", "0003_backinstockalert"), ("orders", "0011_merge_20261029_1408"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name="OrderTrackingEvent", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("status", models.CharField(choices=[("placed", "Order placed"), ("confirmed", "Confirmed"), ("packed", "Packed"), ("shipped", "Shipped"), ("out_for_delivery", "Out for delivery"), ("delivered", "Delivered"), ("cancelled", "Cancelled")], max_length=30)), ("note", models.CharField(blank=True, max_length=255)), ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)), ("changed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)), ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tracking_events", to="orders.order"))], options={"ordering": ["created_at", "id"]}),
        migrations.CreateModel(name="AbandonedCartConsent", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("email_reminders_enabled", models.BooleanField(default=False)), ("consented_at", models.DateTimeField(blank=True, null=True)), ("last_reminder_at", models.DateTimeField(blank=True, null=True)), ("created_at", models.DateTimeField(auto_now_add=True)), ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="abandoned_cart_consent", to=settings.AUTH_USER_MODEL))]),
    ]
