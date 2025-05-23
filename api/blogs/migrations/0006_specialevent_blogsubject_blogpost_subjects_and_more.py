# Generated by Django 5.2rc1 on 2025-04-01 12:55

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blogs', '0005_blogpost_ai_score'),
    ]

    operations = [
        migrations.CreateModel(
            name='SpecialEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('date', models.DateField()),
                ('description', models.TextField()),
                ('importance_level', models.IntegerField(default=1, help_text='1-5, higher means more important')),
            ],
            options={
                'ordering': ['date'],
            },
        ),
        migrations.CreateModel(
            name='BlogSubject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('last_used', models.DateTimeField(auto_now=True)),
                ('usage_count', models.IntegerField(default=1)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subjects', to='blogs.client')),
            ],
            options={
                'unique_together': {('name', 'client')},
            },
        ),
        migrations.AddField(
            model_name='blogpost',
            name='subjects',
            field=models.ManyToManyField(related_name='blog_posts', to='blogs.blogsubject'),
        ),
        migrations.AddField(
            model_name='blogpost',
            name='related_event',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='blog_posts', to='blogs.specialevent'),
        ),
    ]
