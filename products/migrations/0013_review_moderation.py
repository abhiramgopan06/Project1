from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("products", "0012_productvariant_options_and_price"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.AddField(model_name="productreview", name="is_approved", field=models.BooleanField(db_index=True, default=False)),
        migrations.AddField(model_name="productreview", name="verified_purchase", field=models.BooleanField(db_index=True, default=False)),
        migrations.AddField(model_name="productreview", name="moderated_by", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="moderated_product_reviews", to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name="productreview", name="moderated_at", field=models.DateTimeField(blank=True, null=True)),
    ]
