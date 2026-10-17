from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('products', '0007_category_timed_offer'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='discount_ends_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
