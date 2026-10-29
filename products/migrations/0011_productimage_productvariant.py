from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('products', '0010_categoryofferhistory')]
    operations = [
        migrations.CreateModel(name='ProductImage', fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('image', models.ImageField(upload_to='products/gallery/')), ('alt_text', models.CharField(blank=True, max_length=180)), ('sort_order', models.PositiveSmallIntegerField(default=0)), ('created_at', models.DateTimeField(auto_now_add=True)), ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gallery_images', to='products.product'))], options={'ordering': ['sort_order', 'id']}),
        migrations.CreateModel(name='ProductVariant', fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('sku', models.CharField(max_length=80, unique=True)), ('size', models.CharField(blank=True, max_length=40)), ('color', models.CharField(blank=True, max_length=40)), ('price_adjustment', models.DecimalField(decimal_places=2, default=0, max_digits=9)), ('stock', models.PositiveIntegerField(default=0)), ('is_active', models.BooleanField(default=True)), ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variants', to='products.product'))], options={'ordering': ['size', 'color']}),
    ]
