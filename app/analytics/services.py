from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, date, timedelta
from typing import List, Optional

from app.models import TimeSlot
from app.analytics.schemas import TimeSlotAnalytics, DailyAnalytics, TimeRangeAnalytics

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_analytics(self, user_id: int) -> TimeSlotAnalytics:
        """Get overall analytics for a user's time slots."""
        # Get all time slots for the user
        query = self.db.query(TimeSlot).filter(TimeSlot.owner_id == user_id)
        
        total_slots = query.count()
        completed_slots = query.filter(TimeSlot.status == "completed").count()
        in_progress_slots = query.filter(TimeSlot.status == "in_progress").count()
        not_started_slots = query.filter(TimeSlot.status == "not_started").count()
        
        # Calculate total minutes reported
        total_minutes = self.db.query(func.sum(TimeSlot.report_minutes))\
            .filter(TimeSlot.owner_id == user_id)\
            .scalar() or 0
            
        # Calculate averages and rates
        avg_minutes = total_minutes / total_slots if total_slots > 0 else 0
        completion_rate = (completed_slots / total_slots * 100) if total_slots > 0 else 0
        
        return TimeSlotAnalytics(
            total_slots=total_slots,
            completed_slots=completed_slots,
            in_progress_slots=in_progress_slots,
            not_started_slots=not_started_slots,
            total_minutes_reported=total_minutes,
            average_minutes_per_slot=round(avg_minutes, 2),
            completion_rate=round(completion_rate, 2)
        )

    def get_daily_analytics(self, user_id: int, target_date: date) -> DailyAnalytics:
        """Get analytics for a specific day."""
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date + timedelta(days=1), datetime.min.time())
        
        query = self.db.query(TimeSlot).filter(
            TimeSlot.owner_id == user_id,
            TimeSlot.start_time >= start_datetime,
            TimeSlot.start_time < end_datetime
        )
        
        total_slots = query.count()
        completed_slots = query.filter(TimeSlot.status == "completed").count()
        total_minutes = self.db.query(func.sum(TimeSlot.report_minutes))\
            .filter(
                TimeSlot.owner_id == user_id,
                TimeSlot.start_time >= start_datetime,
                TimeSlot.start_time < end_datetime
            ).scalar() or 0
            
        completion_rate = (completed_slots / total_slots * 100) if total_slots > 0 else 0
        
        return DailyAnalytics(
            date=target_date,
            total_slots=total_slots,
            completed_slots=completed_slots,
            total_minutes=total_minutes,
            completion_rate=round(completion_rate, 2)
        )

    def get_time_range_analytics(
        self, 
        user_id: int, 
        start_date: date, 
        end_date: date
    ) -> TimeRangeAnalytics:
        """Get analytics for a specific time range."""
        daily_analytics = []
        current_date = start_date
        
        total_slots = 0
        total_completed = 0
        total_minutes = 0
        
        while current_date <= end_date:
            daily_stats = self.get_daily_analytics(user_id, current_date)
            daily_analytics.append(daily_stats)
            
            total_slots += daily_stats.total_slots
            total_completed += daily_stats.completed_slots
            total_minutes += daily_stats.total_minutes
            
            current_date += timedelta(days=1)
            
        avg_completion_rate = (total_completed / total_slots * 100) if total_slots > 0 else 0
        
        return TimeRangeAnalytics(
            start_date=start_date,
            end_date=end_date,
            daily_analytics=daily_analytics,
            total_slots=total_slots,
            total_completed=total_completed,
            total_minutes=total_minutes,
            average_completion_rate=round(avg_completion_rate, 2)
        )