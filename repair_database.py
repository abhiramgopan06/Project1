import os
import django
from django.core.management import call_command
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from products.models import Category, Product, ProductOfferHistory

call_command('migrate', interactive=False, verbosity=1)

with connection.cursor() as cursor:
    tables = connection.introspection.table_names(cursor)

with connection.schema_editor() as schema_editor:
    if Category._meta.db_table in tables:
        with connection.cursor() as cursor:
            category_columns = {column.name for column in connection.introspection.get_table_description(cursor, Category._meta.db_table)}
        for field_name in ('offer_percent', 'offer_ends_at'):
            field = Category._meta.get_field(field_name)
            if field.column not in category_columns:
                schema_editor.add_field(Category, field)
                category_columns.add(field.column)
                print(f'Added missing database field: Category.{field_name}')

    if Product._meta.db_table in tables:
        with connection.cursor() as cursor:
            product_columns = {column.name for column in connection.introspection.get_table_description(cursor, Product._meta.db_table)}
        for field_name in ('discount_percent', 'discount_ends_at'):
            field = Product._meta.get_field(field_name)
            if field.column not in product_columns:
                schema_editor.add_field(Product, field)
                product_columns.add(field.column)
                print(f'Added missing database field: Product.{field_name}')

    if ProductOfferHistory._meta.db_table not in tables:
        schema_editor.create_model(ProductOfferHistory)
        print('Created missing product offer history table')

call_command('check', verbosity=1)
print('Database repair completed successfully.')
