# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-25 15:31
from __future__ import unicode_literals

from django.db import migrations, models
import share.models.fields
import share.models.jobs


class Migration(migrations.Migration):

    dependencies = [
        ('share', '0034_auto_20170512_2052'),
    ]

    operations = [
        migrations.CreateModel(
            name='CeleryTaskResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('correlation_id', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('FAILURE', 'FAILURE'), ('PENDING', 'PENDING'), ('RECEIVED', 'RECEIVED'), ('RETRY', 'RETRY'), ('REVOKED', 'REVOKED'), ('STARTED', 'STARTED'), ('SUCCESS', 'SUCCESS')], db_index=True, default='PENDING', max_length=50)),
                ('task_id', models.UUIDField(db_index=True, unique=True)),
                ('meta', share.models.fields.DateTimeAwareJSONField(editable=False, null=True)),
                ('result', share.models.fields.DateTimeAwareJSONField(editable=False, null=True)),
                ('task_name', models.TextField(blank=True, db_index=True, editable=False, null=True)),
                ('traceback', models.TextField(blank=True, editable=False, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('share_version', models.TextField(default=share.models.jobs.get_share_version, editable=False)),
            ],
            options={
                'verbose_name': 'Celery Task Result',
                'verbose_name_plural': 'Celery Task Results',
            },
        ),
        migrations.DeleteModel(
            name='CeleryProviderTask',
        ),
        migrations.AddField(
            model_name='sourceconfig',
            name='full_harvest',
            field=models.BooleanField(default=False, help_text='Whether or not this SourceConfig should be fully harvested. Requires earliest_date to be set. The schedule harvests task will create all logs necessary if this flag is set. This should never be set to True by default. '),
        ),
        migrations.AddField(
            model_name='sourceconfig',
            name='harvest_after',
            field=models.TimeField(default='02:00'),
        ),
        migrations.AddField(
            model_name='sourceconfig',
            name='harvest_interval',
            field=models.DurationField(default='1 day'),
        ),
        migrations.AlterField(
            model_name='harvestlog',
            name='status',
            field=models.IntegerField(choices=[(0, 'Enqueued'), (1, 'In Progress'), (2, 'Failed'), (3, 'Succeeded'), (4, 'Rescheduled'), (6, 'Forced'), (7, 'Skipped'), (8, 'Retrying'), (9, 'Cancelled')], db_index=True, default=0),
        ),
        migrations.RemoveField(
            model_name='normalizeddata',
            name='tasks',
        ),
        migrations.AddField(
            model_name='normalizeddata',
            name='tasks',
            field=models.ManyToManyField(to='share.CeleryTaskResult'),
        ),
        migrations.AddIndex(
            model_name='celerytaskresult',
            index=models.Index(fields=['-date_modified', '-id'], name='share_celer_date_mo_686d4d_idx'),
        ),
        migrations.RenameModel(
            old_name='CeleryTask',
            new_name='UnusedCeleryTask',
        ),
        migrations.CreateModel(
            name='UnusedCeleryProviderTask',
            fields=[
            ],
            options={
                'indexes': [],
                'proxy': True,
            },
            bases=('share.unusedcelerytask',),
        ),
        migrations.AlterField(
            model_name='unusedcelerytask',
            name='type',
            field=models.CharField(choices=[('share.unusedceleryprovidertask', 'unused celery provider task')], db_index=True, max_length=255),
        ),
    ]
