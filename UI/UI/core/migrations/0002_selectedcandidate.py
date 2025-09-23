from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SelectedCandidate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('candidate_email', models.CharField(max_length=255, unique=True)),
                ('status', models.CharField(choices=[('selected', 'Selected'), ('final', 'Final')], default='selected', max_length=10)),
            ],
        ),
    ]
