from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('queueing', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='queuetoken',
            name='status',
            field=models.CharField(choices=[('SERVING', 'Serving'), ('COMPLETED', 'Completed'), ('UNEXAMINED', 'Unexamined')], max_length=10),
        ),
    ]
