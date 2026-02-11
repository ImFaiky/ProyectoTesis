from .models import UserLevelProgress, Level

def save_level_progress(user, level, new_score, new_stars):
    progress, created = UserLevelProgress.objects.get_or_create(
        user=user, 
        level=level,
        defaults={'score': new_score, 'stars': new_stars}
    )

    if not created:
        # Update only if new score is higher
        if new_score > progress.score:
            progress.score = new_score
        
        # Update only if new stars are higher (or maybe if score is higher? usually independent or tied)
        # Flutter app logic: independent max
        if new_stars > progress.stars:
            progress.stars = new_stars
            
        progress.save()
    
    return progress
