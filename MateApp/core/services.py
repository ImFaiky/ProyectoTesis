from .models import UserLevelProgress, Level

def save_level_progress(user, level, new_score, new_stars, answers=None):
    defaults = {'score': new_score, 'stars': new_stars}
    if answers is not None:
        defaults['answers'] = answers

    progress, created = UserLevelProgress.objects.get_or_create(
        user=user, 
        level=level,
        defaults=defaults
    )

    if not created:
        # Update only if new score is higher
        if new_score > progress.score:
            progress.score = new_score
        
        if new_stars > progress.stars:
            progress.stars = new_stars
            
        # Always update answers to reflect the latest attempt? 
        # Or only if score is better? User asked for "overwrite if plays again", implying latest.
        if answers is not None:
            progress.answers = answers

        progress.save()
    
    return progress
