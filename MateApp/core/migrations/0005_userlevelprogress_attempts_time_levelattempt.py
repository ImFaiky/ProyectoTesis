import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_achievement_userachievement'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='userlevelprogress',
            name='attempts',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='userlevelprogress',
            name='best_time_seconds',
            field=models.IntegerField(blank=True, help_text='Best completion time in seconds', null=True),
        ),
        migrations.CreateModel(
            name='LevelAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.IntegerField(default=0)),
                ('stars', models.IntegerField(default=0)),
                ('time_seconds', models.IntegerField(default=0, help_text='Time spent on this attempt in seconds')),
                ('answers', models.JSONField(blank=True, default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('level', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attempts', to='core.level')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='level_attempts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
