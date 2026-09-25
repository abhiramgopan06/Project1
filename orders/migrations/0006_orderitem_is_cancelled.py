from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0005_returnreplacerequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='is_cancelled',
            field=models.BooleanField(default=False),
        ),
    ]
