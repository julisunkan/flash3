def sm2_algorithm(quality, easiness_factor=2.5, interval=0, repetitions=0):
    """
    SM-2 Spaced Repetition Algorithm
    
    Args:
        quality: User's response quality (0-5)
                 0: Complete blackout
                 1: Incorrect response; correct one remembered
                 2: Incorrect response; correct one seemed easy to recall
                 3: Correct response recalled with serious difficulty
                 4: Correct response after hesitation
                 5: Perfect response
        easiness_factor: Current easiness factor (default 2.5)
        interval: Current interval in days (default 0)
        repetitions: Number of consecutive correct responses (default 0)
    
    Returns:
        tuple: (new_easiness_factor, new_interval, new_repetitions)
    """
    
    if quality < 0 or quality > 5:
        quality = max(0, min(5, quality))
    
    new_ef = easiness_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    
    if new_ef < 1.3:
        new_ef = 1.3
    
    if quality < 3:
        new_repetitions = 0
        new_interval = 1
    else:
        if repetitions == 0:
            new_interval = 1
        elif repetitions == 1:
            new_interval = 6
        else:
            new_interval = round(interval * new_ef)
        
        new_repetitions = repetitions + 1
    
    return new_ef, new_interval, new_repetitions
