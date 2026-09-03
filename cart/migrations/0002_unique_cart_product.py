from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('cart', '0001_initial'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='cartitem',
            constraint=models.UniqueConstraint(
                fields=('cart', 'product'),
                name='unique_product_per_cart',
            ),
        ),
    ]
