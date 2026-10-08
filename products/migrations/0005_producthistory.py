from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('products', '0004_product_is_replaceable_product_is_returnable'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('viewed_count', models.PositiveIntegerField(default=0)),
                ('cart_count', models.PositiveIntegerField(default=0)),
                ('ordered_count', models.PositiveIntegerField(default=0)),
                ('search_count', models.PositiveIntegerField(default=0)),
                ('last_viewed', models.DateTimeField(blank=True, null=True)),
                ('last_interacted', models.DateTimeField(auto_now=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_history', to='products.product')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_history', to='auth.user')),
            ],
            options={
                'ordering': ['-last_interacted'],
            },
        ),
        migrations.AddConstraint(
            model_name='producthistory',
            constraint=models.UniqueConstraint(fields=('user', 'product'), name='unique_product_history_per_user'),
        ),
    ]
