from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bomberos', '0005_mesanio_comprobantetransferencia_comprobantetesorero'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='apellido_materno',
            field=models.CharField(default='', max_length=150, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='apellido_paterno',
            field=models.CharField(default='', max_length=150, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='cargo',
            field=models.CharField(default='', max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='cia',
            field=models.CharField(default='', max_length=50, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='codigo_llamado',
            field=models.CharField(default='', max_length=50, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='direccion_calle',
            field=models.CharField(default='', max_length=255, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='direccion_complemento',
            field=models.CharField(default='', max_length=255, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='direccion_comuna',
            field=models.CharField(default='', max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='direccion_numero',
            field=models.CharField(default='', max_length=20, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='estado_civil',
            field=models.CharField(default='', max_length=50, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='nacionalidad',
            field=models.CharField(default='', max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='nombres',
            field=models.CharField(default='', max_length=150, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='profesion',
            field=models.CharField(default='', max_length=150, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='registro',
            field=models.CharField(default='', max_length=50, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='registro_cia',
            field=models.CharField(default='', max_length=50, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='sangre_grupo',
            field=models.CharField(default='', max_length=10, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='sexo',
            field=models.CharField(default='', max_length=30, blank=True),
            preserve_default=False,
        ),
    ]
