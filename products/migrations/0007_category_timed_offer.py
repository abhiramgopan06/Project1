from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('products', '0006_product_discount_percent'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='offer_percent',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='category',
            name='offer_ends_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
