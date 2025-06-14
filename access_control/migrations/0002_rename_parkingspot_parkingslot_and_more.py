# Generated by Django 5.1.5 on 2025-05-12 01:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('access_control', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ParkingSpot',
            new_name='ParkingSlot',
        ),
        migrations.RenameModel(
            old_name='VisitorLog',
            new_name='Visitor',
        ),
        migrations.RenameField(
            model_name='parkingslot',
            old_name='spot_number',
            new_name='slot_number',
        ),
        migrations.RenameField(
            model_name='resident',
            old_name='apartment_number',
            new_name='unit_number',
        ),
        migrations.RenameField(
            model_name='visitor',
            old_name='dl_number',
            new_name='drivers_license',
        ),
    ]
