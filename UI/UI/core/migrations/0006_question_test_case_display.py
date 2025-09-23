from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_question'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='test_case_display',
            field=models.TextField(blank=True),
        ),
    ]
