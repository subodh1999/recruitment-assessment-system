from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_testresult'),
    ]

    operations = [
        migrations.AlterField(
            model_name='selectedcandidate',
            name='status',
            field=models.CharField(choices=[('selected', 'Selected'), ('final_selected', 'Final Selected')], default='selected', max_length=20),
        ),
    ]
