import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_selectedcandidate'),
    ]

    operations = [
        migrations.CreateModel(
            name='TestResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('q1_code', models.TextField(blank=True)),
                ('q1_output', models.TextField(blank=True)),
                ('q1_status', models.CharField(blank=True, max_length=20)),
                ('q2_code', models.TextField(blank=True)),
                ('q2_output', models.TextField(blank=True)),
                ('q2_status', models.CharField(blank=True, max_length=20)),
                ('q3_code', models.TextField(blank=True)),
                ('q3_output', models.TextField(blank=True)),
                ('q3_status', models.CharField(blank=True, max_length=20)),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('candidate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.candidate')),
            ],
        ),
    ]
