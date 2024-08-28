# Generated by Django 5.1 on 2024-08-28 14:53

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Text",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, unique=True)),
                ("text", models.TextField()),
                ("text_en", models.TextField(null=True)),
                ("text_uk", models.TextField(null=True)),
            ],
        ),
    ]
