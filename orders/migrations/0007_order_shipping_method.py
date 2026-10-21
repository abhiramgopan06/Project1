from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0006_orderitem_is_cancelled'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='shipping_method',
            field=models.CharField(
                choices=[('free', 'Free Shipping'), ('express', 'Express Shipping')],
                default='free',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='shipping_cost',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=8),
        ),
    ]
