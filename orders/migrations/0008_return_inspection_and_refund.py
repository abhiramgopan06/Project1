from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('orders', '0007_order_shipping_method'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='returnreplacerequest',
            name='reason',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='returnreplacerequest',
            name='status',
            field=models.CharField(choices=[('Requested', 'Requested'), ('Approved', 'Approved'), ('Rejected', 'Rejected'), ('Product Received', 'Product Received'), ('Refunded', 'Refunded'), ('Completed', 'Completed')], default='Requested', max_length=20),
        ),
        migrations.AddField(model_name='returnreplacerequest', name='product_condition', field=models.CharField(choices=[('Pending Inspection', 'Pending Inspection'), ('Good', 'Good'), ('Damaged', 'Damaged')], default='Pending Inspection', max_length=30)),
        migrations.AddField(model_name='returnreplacerequest', name='inspection_note', field=models.TextField(blank=True)),
        migrations.AddField(model_name='returnreplacerequest', name='refund_status', field=models.CharField(choices=[('Not Eligible', 'Not Eligible'), ('Pending', 'Pending'), ('Processed', 'Processed')], default='Not Eligible', max_length=20)),
        migrations.AddField(model_name='returnreplacerequest', name='refund_amount', field=models.DecimalField(decimal_places=2, default=0, max_digits=10)),
        migrations.AddField(model_name='returnreplacerequest', name='received_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='returnreplacerequest', name='inspected_by', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inspected_returns', to=settings.AUTH_USER_MODEL)),
    ]
