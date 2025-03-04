# momentum.py

from enum import Enum

class AchievementCategory(str, Enum):
    PRODUCTIVITY = "productivity"
    CONSISTENCY = "consistency"
    MILESTONE = "milestone"
    TIME_MANAGEMENT = "time_management"
    FOCUS = "focus"
    GROWTH = "growth"
    SOCIAL = "social"

class CriteriaType(str, Enum):
    COUNT = "count"
    STREAK = "streak"
    TIME = "time"
    COMPOUND = "compound"
    SPECIFIC_TIME = "specific_time"

POINT_EVENTS = {
    'task_completion': 3,
    'goal_completion': 15,
    'goal_step_completion': 5,
    'time_slot_completion': 7,
    'perfect_week': 30,
    'first_task_of_day': 2,
    'weekend_warrior': 10,
    'early_bird': 5,
    'night_owl': 5,
    'focused_session': lambda duration: max(1, duration // 3),
    'streak_milestone': lambda streak: streak * 3,
    'goal_streak': lambda streak: streak * 5,
    'perfect_month': 150,
    'task_complexity': lambda complexity: complexity * 7,
}

ACHIEVEMENTS = [
    # Productivity Achievements
    {
        'name': 'Task Master',
        'description': 'Complete 100 tasks',
        'points': 500,
        'category': AchievementCategory.PRODUCTIVITY,
        'criteria_type': CriteriaType.COUNT,
        'criteria_value': 100,
        'icon_name': 'trophy'
    },
    {
        'name': 'Goal Crusher',
        'description': 'Complete 10 goals',
        'points': 1000,
        'category': AchievementCategory.PRODUCTIVITY,
        'criteria_type': CriteriaType.COUNT,
        'criteria_value': 10,
        'icon_name': 'target'
    },
    
    # Consistency Achievements
    {
        'name': 'Streak Warrior',
        'description': 'Maintain a 30-day task completion streak',
        'points': 1000,
        'category': AchievementCategory.CONSISTENCY,
        'criteria_type': CriteriaType.STREAK,
        'criteria_value': 30,
        'icon_name': 'fire'
    },
    {
        'name': 'Weekly Wonder',
        'description': 'Complete all planned tasks for 4 consecutive weeks',
        'points': 2000,
        'category': AchievementCategory.CONSISTENCY,
        'criteria_type': CriteriaType.STREAK,
        'criteria_value': 28,
        'icon_name': 'calendar'
    },
    
    # Time Management
    {
        'name': 'Early Riser',
        'description': 'Complete 20 tasks before 9 AM',
        'points': 500,
        'category': AchievementCategory.TIME_MANAGEMENT,
        'criteria_type': CriteriaType.SPECIFIC_TIME,
        'criteria_value': 20,
        'icon_name': 'sun'
    },
    {
        'name': 'Time Wizard',
        'description': 'Successfully complete 50 scheduled time slots',
        'points': 750,
        'category': AchievementCategory.TIME_MANAGEMENT,
        'criteria_type': CriteriaType.COUNT,
        'criteria_value': 50,
        'icon_name': 'clock'
    },
    
    # Focus Achievements
    {
        'name': 'Deep Work Master',
        'description': 'Complete 10 focused sessions of 2+ hours',
        'points': 1500,
        'category': AchievementCategory.FOCUS,
        'criteria_type': CriteriaType.COUNT,
        'criteria_value': 10,
        'icon_name': 'zap'
    },
    {
        'name': 'Flow State Champion',
        'description': 'Accumulate 100 hours of focused work time',
        'points': 2000,
        'category': AchievementCategory.FOCUS,
        'criteria_type': CriteriaType.TIME,
        'criteria_value': 100,
        'icon_name': 'activity'
    },
    
    # Growth Achievements
    {
        'name': 'Goal Strategist',
        'description': 'Create and complete 5 goals with at least 5 steps each',
        'points': 1500,
        'category': AchievementCategory.GROWTH,
        'criteria_type': CriteriaType.COMPOUND,
        'criteria_value': 5,
        'icon_name': 'trending-up'
    },
    {
        'name': 'Productivity Pioneer',
        'description': 'Try all productivity features in a week',
        'points': 1000,
        'category': AchievementCategory.GROWTH,
        'criteria_type': CriteriaType.COMPOUND,
        'criteria_value': 1,
        'icon_name': 'compass'
    },
    
    # Social Achievements
    {
        'name': 'Leaderboard Legend',
        'description': 'Reach #1 on weekly leaderboard',
        'points': 2000,
        'category': AchievementCategory.SOCIAL,
        'criteria_type': CriteriaType.COMPOUND,
        'criteria_value': 1,
        'icon_name': 'award'
    }
]

# Exponential level progression
LEVELS = [
    {
        'level_number': 1,
        'points_required': 0,
        'title': 'Productivity Rookie',
        'perks': {'custom_backgrounds': False, 'analytics_access': False}
    },
    {
        'level_number': 2,
        'points_required': 100,
        'title': 'Efficiency Explorer',
        'perks': {'custom_backgrounds': True, 'analytics_access': False}
    },
    {
        'level_number': 3,
        'points_required': 300,
        'title': 'Momentum Builder',
        'perks': {'custom_backgrounds': True, 'analytics_access': True}
    },
    {
        'level_number': 4,
        'points_required': 700,
        'title': 'Progress Professional',
        'perks': {'custom_backgrounds': True, 'analytics_access': True, 'custom_themes': True}
    },
    {
        'level_number': 5,
        'points_required': 1500,
        'title': 'Productivity Warrior',
        'perks': {'custom_backgrounds': True, 'analytics_access': True, 'custom_themes': True, 'advanced_analytics': True}
    },
    {
        'level_number': 6,
        'points_required': 3000,
        'title': 'Time Lord',
        'perks': {'all_features': True, 'special_badge': True}
    },
    {
        'level_number': 7,
        'points_required': 6000,
        'title': 'Efficiency Emperor',
        'perks': {'all_features': True, 'special_badge': True, 'mentor_status': True}
    },
    {
        'level_number': 8,
        'points_required': 12000,
        'title': 'Productivity Legend',
        'perks': {'all_features': True, 'special_badge': True, 'mentor_status': True, 'custom_achievements': True}
    },
    {
        'level_number': 9,
        'points_required': 24000,
        'title': 'Momentum Master',
        'perks': {'all_features': True, 'special_badge': True, 'mentor_status': True, 'custom_achievements': True}
    },
    {
        'level_number': 10,
        'points_required': 50000,
        'title': 'Ultimate Achiever',
        'perks': {'all_features': True, 'special_badge': True, 'mentor_status': True, 'custom_achievements': True, 'legendary_status': True}
    }
]