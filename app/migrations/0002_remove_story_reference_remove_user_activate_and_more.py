# Generated by Django 4.2.4 on 2023-09-02 16:10

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='story',
            name='reference',
        ),
        migrations.RemoveField(
            model_name='user',
            name='activate',
        ),
        migrations.AddField(
            model_name='story',
            name='prompt',
            field=models.CharField(default=django.utils.timezone.now, max_length=500),
            preserve_default=False,
        ),
    ]
