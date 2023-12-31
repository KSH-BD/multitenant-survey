# Generated by Django 4.2.6 on 2023-12-16 16:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0012_question_basicquestion'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='actual_zone',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.CreateModel(
            name='CompanyJson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.JSONField(verbose_name='Company')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='survey.tenant')),
            ],
        ),
    ]
