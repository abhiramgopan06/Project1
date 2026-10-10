from django.db import migrations


class Migration(migrations.Migration):
    """Removes the old, unused PendingRegistration table.

    The project now keeps the not-yet-verified user as an inactive User
    plus an EmailOTP row, so this table is no longer needed."""

    dependencies = [
        ('accounts', '0005_merge_0004_emailotp_0004_pendingregistration'),
    ]

    operations = [
        migrations.DeleteModel(
            name='PendingRegistration',
        ),
    ]
