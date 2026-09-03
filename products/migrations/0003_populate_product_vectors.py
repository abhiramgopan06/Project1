from django.db import migrations


def populate_vectors(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    for product in Product.objects.select_related('category').all():
        text = f"{product.name} {product.description} {product.category.name if product.category_id else ''}".lower()
        import re
        from collections import Counter
        words = [w for w in re.findall(r'[a-zA-Z0-9]+', text) if len(w) > 1]
        product.vector_data = dict(Counter(words).most_common(80))
        product.save(update_fields=['vector_data'])


def reverse_vectors(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    Product.objects.all().update(vector_data={})


class Migration(migrations.Migration):
    dependencies = [('products', '0002_recommendations_reviews')]
    operations = [migrations.RunPython(populate_vectors, reverse_vectors)]
