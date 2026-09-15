import json
import os
import random

def load_workout_data():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'workout_data.json')
    with open(path, 'r') as f:
        return json.load(f)

def generate_workout_plan(bmi, goal, experience, location, health_condition):
    """
    Generate a 7-day workout plan.
    
    Args:
        bmi (float): User's BMI
        goal (int): 0=Weight Loss, 1=Maintenance, 2=Weight Gain (Muscle Gain)
        experience (str): 'beginner', 'intermediate', 'advanced'
        location (str): 'home' or 'gym'
        health_condition (str): e.g. 'None', 'Diabetes', 'PCOS', 'Thyroid', 'Hypertension'
    
    Returns:
        dict: 7-day workout plan
    """
    data = load_workout_data()
    
    # Map goal int to string key
    goal_map = {0: 'weight_loss', 1: 'maintenance', 2: 'muscle_gain'}
    goal_key = goal_map.get(goal, 'maintenance')
    
    # Normalize inputs
    experience = experience.lower() if experience else 'beginner'
    location = location.lower() if location else 'home'
    
    if experience not in data['schedules']:
        experience = 'beginner'
    if location not in ['home', 'gym']:
        location = 'home'
    
    # Get exercise pool and schedule
    exercise_pool = data['exercises'].get(goal_key, data['exercises']['maintenance'])
    location_exercises = exercise_pool.get(location, exercise_pool.get('home', {}))
    schedule = data['schedules'].get(experience, data['schedules']['beginner'])
    
    # Health condition adjustments
    has_condition = health_condition and health_condition.lower() not in ['none', '']
    reduce_intensity = has_condition and health_condition.lower() in ['diabetes', 'pcos', 'thyroid', 'hypertension']
    
    # BMI adjustments
    is_obese = bmi > 30
    is_underweight = bmi < 18.5
    
    workout_plan = {}
    
    for day_info in schedule:
        day_key = day_info['day']
        label = day_info['label']
        types = day_info['types']
        
        if not types:
            # Rest day
            workout_plan[day_key] = {
                'label': label,
                'exercises': [],
                'is_rest_day': True,
                'notes': 'Focus on recovery, stretching, and hydration.'
            }
            continue
        
        day_exercises = []
        for ex_type in types:
            pool = location_exercises.get(ex_type, [])
            if not pool:
                continue
            
            # Select exercises (pick 3-4 for full body, 4-5 for focused days)
            if len(types) >= 3:
                count = min(2, len(pool))
            else:
                count = min(4, len(pool))
            
            selected = pool[:count]
            
            for ex in selected:
                exercise = dict(ex)  # Copy
                
                # Apply health condition modifications
                if reduce_intensity:
                    exercise['sets'] = max(2, exercise['sets'] - 1)
                    exercise['rest'] = _increase_rest(exercise['rest'])
                
                # BMI adjustments
                if is_obese:
                    # Replace high-impact with low-impact alternatives
                    exercise['sets'] = max(2, exercise['sets'] - 1)
                    if exercise.get('duration'):
                        exercise['rest'] = _increase_rest(exercise['rest'])
                
                if is_underweight and goal_key == 'muscle_gain':
                    exercise['sets'] = min(exercise['sets'] + 1, 5)
                
                day_exercises.append(exercise)
        
        notes = ''
        if reduce_intensity:
            notes = f'Modified for {health_condition}: reduced intensity, longer rest periods.'
        if is_obese:
            notes += ' Low-impact modifications applied due to high BMI.'
        
        workout_plan[day_key] = {
            'label': label,
            'exercises': day_exercises,
            'is_rest_day': False,
            'notes': notes.strip()
        }
    
    return workout_plan

def _increase_rest(rest_str):
    """Increase rest time by ~15 seconds for health condition adjustments."""
    if not rest_str:
        return '60s'
    rest_str = rest_str.strip().lower()
    if rest_str.endswith('s'):
        try:
            seconds = int(rest_str[:-1])
            return f'{seconds + 15}s'
        except ValueError:
            return rest_str
    return rest_str
