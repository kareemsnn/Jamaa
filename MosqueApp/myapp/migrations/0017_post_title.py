# Generated by Django 5.0.6 on 2024-09-15 02:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0016_rename_events_post_event_details_post_event_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='title',
            field=models.CharField(blank=True, max_length=32),
        ),
    ]