# Generated by Django 5.0.6 on 2024-10-27 02:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0019_remove_mosque_nonprofitform_remove_mosque_password_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='mosque',
            name='password',
            field=models.CharField(default='', max_length=255),
        ),
    ]