# Generated by Django 5.1.1 on 2024-09-30 12:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("blog_app", "0003_post_status"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="follow",
            unique_together={("reader", "author")},
        ),
    ]
