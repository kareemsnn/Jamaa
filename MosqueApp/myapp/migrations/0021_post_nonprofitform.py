# Generated by Django 5.0.6 on 2024-10-27 03:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0020_mosque_password'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='nonprofitform',
            field=models.FileField(blank=True, default='placeholder.pdf', null=True, upload_to='mosque_verification/'),
        ),
    ]
