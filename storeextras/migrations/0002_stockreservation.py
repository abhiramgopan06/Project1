from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('storeextras', '0001_initial'), ('orders', '0010_orderitem_variant'), ('products', '0011_productimage_productvariant'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(name='StockReservation', fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('quantity', models.PositiveIntegerField()), ('reference', models.CharField(max_length=100, unique=True)), ('expires_at', models.DateTimeField()), ('released', models.BooleanField(default=False)), ('created_at', models.DateTimeField(auto_now_add=True)), ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='products.product')), ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stock_reservations', to=settings.AUTH_USER_MODEL)), ('variant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='products.productvariant'))], options={'ordering': ['expires_at']}), migrations.AddIndex(model_name='stockreservation', index=models.Index(fields=['released', 'expires_at'], name='stx_res_exp_idx'))]
