# Generated by Django 5.1.6 on 2025-06-01 14:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ETA", "0012_merge_0011_alter_profile_bio_0011_inviterequest"),
    ]

    operations = [
        migrations.CreateModel(
            name="Tag",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=30, unique=True)),
            ],
            options={
                "ordering": ["category__name", "name"],
            },
        ),
        migrations.CreateModel(
            name="TagCategory",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=30, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name="event",
            name="tags",
            field=models.ManyToManyField(blank=True, to="ETA.tag"),
        ),
        migrations.AddField(
            model_name="tag",
            name="category",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="tags",
                to="ETA.tagcategory",
            ),
        ),
    ]
