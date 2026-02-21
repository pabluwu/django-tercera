from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('bomberos', '0006_userprofile_campos_registro_lite'),
    ]

    operations = [
        migrations.CreateModel(
            name='ApiLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('path', models.CharField(max_length=300)),
                ('method', models.CharField(max_length=10)),
                ('status_code', models.IntegerField()),
                ('ip', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.CharField(blank=True, max_length=400)),
                ('body', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'indexes': [
                    models.Index(fields=['created_at'], name='apilog_created_at_idx'),
                    models.Index(fields=['path'], name='apilog_path_idx'),
                    models.Index(fields=['status_code'], name='apilog_status_code_idx'),
                ],
            },
        ),
    ]
