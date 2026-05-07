from django.db.models import Count, Q, F
from datetime import datetime, timedelta
from .models import UserLevelProgress, Level, LevelAttempt

def save_level_progress(user, level, new_score, new_stars, answers=None, time_seconds=0):
    defaults = {
        'score': new_score,
        'stars': new_stars,
        'attempts': 1,
        'best_time_seconds': time_seconds if time_seconds > 0 else None,
    }
    if answers is not None:
        defaults['answers'] = answers

    progress, created = UserLevelProgress.objects.get_or_create(
        user=user, 
        level=level,
        defaults=defaults
    )

    if not created:
        progress.attempts += 1

        # Update only if new score is higher
        if new_score > progress.score:
            progress.score = new_score
        
        if new_stars > progress.stars:
            progress.stars = new_stars

        # Track best time (lower is better)
        if time_seconds > 0:
            if progress.best_time_seconds is None or time_seconds < progress.best_time_seconds:
                progress.best_time_seconds = time_seconds
            
        if answers is not None:
            progress.answers = answers

        progress.save()

    # Always record individual attempt for analytics
    LevelAttempt.objects.create(
        user=user,
        level=level,
        score=new_score,
        stars=new_stars,
        time_seconds=time_seconds,
        answers=answers or [],
    )
    
    return progress


