                                             

from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0002_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Payment',
        ),
    ]
