from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('products', '0011_productimage_productvariant'),
    ]

    operations = [
        migrations.AddField(
            model_name='productvariant',
            name='option_type',
            field=models.CharField(choices=[('size', 'Size'), ('color', 'Color'), ('storage', 'Storage capacity'), ('other', 'Other option')], default='size', max_length=20),
        ),
        migrations.AddField(
            model_name='productvariant',
            name='option_value',
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name='productvariant',
            name='price_override',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AlterModelOptions(
            name='productvariant',
            options={'ordering': ['option_type', 'option_value', 'size', 'color']},
        ),
    ]
