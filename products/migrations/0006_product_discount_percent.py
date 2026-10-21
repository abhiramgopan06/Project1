from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("products", "0005_producthistory")]

    operations = [
        migrations.AddField(
            model_name="product",
            name="discount_percent",
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
