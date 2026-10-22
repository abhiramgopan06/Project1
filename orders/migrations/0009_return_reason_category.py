from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('orders', '0008_return_inspection_and_refund'),
    ]

    operations = [
        migrations.AddField(
            model_name='returnreplacerequest',
            name='reason_category',
            field=models.CharField(
                choices=[
                    ('Color differs', 'Color differs from the picture'),
                    ('Damaged product', 'Product arrived damaged'),
                    ('Smaller than pictured', 'Product is smaller than pictured'),
                    ('Bigger than pictured', 'Product is bigger than pictured'),
                    ('Wrong product received', 'Wrong product received'),
                    ('Missing parts or accessories', 'Parts or accessories are missing'),
                    ('Quality not as expected', 'Quality is not as expected'),
                    ('Changed my mind', 'Changed my mind'),
                    ('Other', 'Other reason'),
                ],
                default='Other',
                max_length=40,
            ),
        ),
    ]
