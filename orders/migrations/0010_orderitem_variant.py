from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('orders', '0009_return_reason_category'), ('products', '0011_productimage_productvariant')]
    operations = [migrations.AddField(model_name='orderitem', name='variant', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='order_items', to='products.productvariant'))]
