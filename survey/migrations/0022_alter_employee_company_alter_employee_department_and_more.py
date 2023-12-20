# Generated by Django 4.2.6 on 2023-12-18 07:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0021_questionoption_survey_ques_value_a90cbb_idx'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='company',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='department',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='division',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='job_title',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='section',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
