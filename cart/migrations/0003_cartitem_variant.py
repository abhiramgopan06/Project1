from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('cart', '0002_unique_cart_product'), ('products', '0011_productimage_productvariant')]
    operations = [
        migrations.RemoveConstraint(model_name='cartitem', name='unique_product_per_cart'),
        migrations.AddField(model_name='cartitem', name='variant', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cart_items', to='products.productvariant')),
        migrations.AddConstraint(model_name='cartitem', constraint=models.UniqueConstraint(fields=('cart', 'product', 'variant'), name='unique_cart_product_variant')),
    ]
