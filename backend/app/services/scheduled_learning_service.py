"""
Scheduled Learning Service for running daily algorithm improvement cycles
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import get_sync_session
from app.services.feature_learning_service import FeatureLearningService
from app.services.behavioral_analysis_service import BehavioralAnalysisService

logger = logging.getLogger(__name__)


class ScheduledLearningService:
    """Service for managing scheduled learning tasks"""
    
    def __init__(self):
        # Create separate database session for scheduled tasks
        self.engine = create_engine(settings.DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Task scheduling parameters
        self.daily_cycle_hour = 2  # Run at 2 AM
        self.last_daily_run = None
        self.is_running = False
    
    async def start_scheduler(self):
        """Start the learning scheduler"""
        logger.info("Starting learning scheduler")
        self.is_running = True
        
        while self.is_running:
            try:
                await self._check_and_run_daily_cycle()
                
                # Check every hour
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying
    
    def stop_scheduler(self):
        """Stop the learning scheduler"""
        logger.info("Stopping learning scheduler")
        self.is_running = False
    
    async def _check_and_run_daily_cycle(self):
        """Check if daily cycle should run and execute it"""
        now = datetime.utcnow()
        
        # Check if it's time for daily cycle
        if (self.last_daily_run is None or 
            (now - self.last_daily_run).days >= 1 and 
            now.hour >= self.daily_cycle_hour):
            
            logger.info("Starting scheduled daily improvement cycle")
            
            try:
                db = self.SessionLocal()
                
                # Run daily improvement cycle
                service = FeatureLearningService(db)
                results = await service.run_daily_improvement_cycle()
                
                # Log results
                if 'errors' in results and results['errors']:
                    logger.warning(f"Daily cycle completed with {len(results['errors'])} errors")
                    for error in results['errors']:
                        logger.error(f"Daily cycle error: {error}")
                else:
                    logger.info("Daily improvement cycle completed successfully")
                
                # Update last run time
                self.last_daily_run = now
                
                # Store cycle results for monitoring
                await self._store_cycle_results(results)
                
                db.close()
                
            except Exception as e:
                logger.error(f"Error in daily improvement cycle: {str(e)}")
                if 'db' in locals():
                    db.close()
    
    async def _store_cycle_results(self, results: Dict[str, Any]):
        """Store cycle results for monitoring and analysis"""
        try:
            # In a production system, you might want to store these results
            # in a dedicated monitoring table or send to a monitoring service
            
            cycle_summary = {
                'timestamp': results.get('timestamp', datetime.utcnow()),
                'feature_extraction_processed': results.get('feature_extraction', {}).get('processed', 0),
                'patterns_discovered': results.get('pattern_discovery', {}).get('patterns_found', 0),
                'correlations_found': results.get('correlation_mining', {}).get('correlations_found', 0),
                'responses_analyzed': results.get('behavioral_analysis', {}).get('responses_analyzed', 0),
                'error_count': len(results.get('errors', [])),
                'status': 'completed' if not results.get('errors') else 'completed_with_errors'
            }
            
            logger.info(f"Daily cycle summary: {cycle_summary}")
            
            # Here you could store to database, send to monitoring service, etc.
            
        except Exception as e:
            logger.error(f"Error storing cycle results: {str(e)}")
    
    async def run_manual_cycle(self) -> Dict[str, Any]:
        """Run improvement cycle manually (for API endpoint)"""
        try:
            db = self.SessionLocal()
            
            service = FeatureLearningService(db)
            results = await service.run_daily_improvement_cycle()
            
            db.close()
            
            return results
            
        except Exception as e:
            logger.error(f"Error in manual cycle: {str(e)}")
            if 'db' in locals():
                db.close()
            return {'error': str(e)}
    
    async def run_feature_extraction_batch(self, max_items: int = 50) -> Dict[str, Any]:
        """Run feature extraction for unprocessed items"""
        try:
            db = self.SessionLocal()
            
            # Get unprocessed items
            from app.models.quiz_system import QuizClothingItem
            from sqlalchemy import or_
            
            unprocessed_items = db.query(QuizClothingItem).filter(
                or_(
                    QuizClothingItem.auto_extracted_features.is_(None),
                    QuizClothingItem.auto_extracted_features == []
                )
            ).limit(max_items).all()
            
            if not unprocessed_items:
                db.close()
                return {'message': 'No unprocessed items found', 'processed': 0}
            
            # Extract features
            service = FeatureLearningService(db)
            item_ids = [str(item.id) for item in unprocessed_items]
            results = await service.batch_extract_features(item_ids)
            
            successful = len([r for r in results if r.get('success')])
            
            db.close()
            
            return {
                'processed': len(item_ids),
                'successful': successful,
                'failed': len(results) - successful,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error in feature extraction batch: {str(e)}")
            if 'db' in locals():
                db.close()
            return {'error': str(e)}
    
    async def run_behavioral_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Run behavioral analysis for specified time period"""
        try:
            db = self.SessionLocal()
            
            service = BehavioralAnalysisService(db)
            
            # Run multiple analyses
            results = {
                'style_accuracy': service.analyze_style_assignment_accuracy(days),
                'upload_patterns': service.analyze_user_upload_patterns(),
                'algorithm_drift': service.detect_algorithm_drift(days),
                'recommendations': service.generate_improvement_recommendations()
            }
            
            db.close()
            
            return results
            
        except Exception as e:
            logger.error(f"Error in behavioral analysis: {str(e)}")
            if 'db' in locals():
                db.close()
            return {'error': str(e)}
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        return {
            'is_running': self.is_running,
            'last_daily_run': self.last_daily_run.isoformat() if self.last_daily_run else None,
            'daily_cycle_hour': self.daily_cycle_hour,
            'next_scheduled_run': self._get_next_scheduled_run()
        }
    
    def _get_next_scheduled_run(self) -> str:
        """Calculate next scheduled run time"""
        now = datetime.utcnow()
        
        # If we haven't run today and it's past the scheduled hour, run today
        if (self.last_daily_run is None or 
            (now - self.last_daily_run).days >= 1):
            
            if now.hour >= self.daily_cycle_hour:
                # Run today
                next_run = now.replace(hour=self.daily_cycle_hour, minute=0, second=0, microsecond=0)
            else:
                # Run later today
                next_run = now.replace(hour=self.daily_cycle_hour, minute=0, second=0, microsecond=0)
        else:
            # Run tomorrow
            tomorrow = now + timedelta(days=1)
            next_run = tomorrow.replace(hour=self.daily_cycle_hour, minute=0, second=0, microsecond=0)
        
        return next_run.isoformat()


# Global scheduler instance
scheduler_instance = None


async def start_learning_scheduler():
    """Start the global learning scheduler"""
    global scheduler_instance
    
    if scheduler_instance is None:
        scheduler_instance = ScheduledLearningService()
    
    if not scheduler_instance.is_running:
        # Start scheduler in background task
        asyncio.create_task(scheduler_instance.start_scheduler())
        logger.info("Learning scheduler started")


def stop_learning_scheduler():
    """Stop the global learning scheduler"""
    global scheduler_instance
    
    if scheduler_instance:
        scheduler_instance.stop_scheduler()
        logger.info("Learning scheduler stopped")


def get_scheduler_instance() -> ScheduledLearningService:
    """Get the global scheduler instance"""
    global scheduler_instance
    
    if scheduler_instance is None:
        scheduler_instance = ScheduledLearningService()
    
    return scheduler_instance