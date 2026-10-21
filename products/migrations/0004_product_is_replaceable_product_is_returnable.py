                                                

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_populate_product_vectors'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='is_replaceable',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='product',
            name='is_returnable',
            field=models.BooleanField(default=False),
        ),
    ]
