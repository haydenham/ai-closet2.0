"""
Service for tracking and analyzing recommendation improvements based on user feedback
"""
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict, Counter
import statistics

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from app.models.user import User
from app.models.outfit_recommendation import OutfitRecommendation, RecommendationFeedback
from app.models.clothing_item import ClothingItem

logger = logging.getLogger(__name__)


@dataclass
class ImprovementMetrics:
    """Data class for improvement tracking metrics"""
    user_id: str
    time_period: str
    total_recommendations: int
    average_rating: float
    rating_trend: float  # positive = improving, negative = declining
    feedback_categories: Dict[str, int]
    common_issues: List[str]
    improvement_suggestions: List[str]
    satisfaction_score: float


@dataclass
class RecommendationPattern:
    """Data class for recommendation patterns and insights"""
    pattern_type: str
    description: str
    frequency: int
    success_rate: float
    user_satisfaction: float
    recommendations: List[str]


class RecommendationImprovementService:
    """Service for analyzing recommendation performance and suggesting improvements"""
    
    def __init__(self):
        self.min_recommendations_for_analysis = 5
        self.analysis_periods = {
            'week': 7,
            'month': 30,
            'quarter': 90
        }
    
    def analyze_user_improvement_metrics(
        self,
        db: Session,
        user: User,
        period: str = 'month'
    ) -> ImprovementMetrics:
        """
        Analyze improvement metrics for a specific user
        
        Args:
            db: Database session
            user: User object
            period: Analysis period ('week', 'month', 'quarter')
            
        Returns:
            ImprovementMetrics with detailed analysis
        """
        logger.info(f"Analyzing improvement metrics for user {user.id} over {period}")
        
        # Calculate date range
        days = self.analysis_periods.get(period, 30)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get recommendations in period
        recommendations = db.query(OutfitRecommendation).filter(
            and_(
                OutfitRecommendation.user_id == user.id,
                OutfitRecommendation.created_at >= start_date,
                OutfitRecommendation.feedback_score.isnot(None)
            )
        ).order_by(OutfitRecommendation.created_at).all()
        
        if len(recommendations) < self.min_recommendations_for_analysis:
            logger.warning(f"Insufficient data for user {user.id}: {len(recommendations)} recommendations")
            return self._create_empty_metrics(user.id, period)
        
        # Calculate basic metrics
        ratings = [rec.feedback_score for rec in recommendations if rec.feedback_score]
        average_rating = statistics.mean(ratings) if ratings else 0.0
        
        # Calculate rating trend (comparing first half vs second half)
        rating_trend = self._calculate_rating_trend(ratings)
        
        # Analyze feedback categories
        feedback_categories = self._analyze_feedback_categories(db, user.id, start_date)
        
        # Identify common issues
        common_issues = self._identify_common_issues(db, user.id, start_date)
        
        # Generate improvement suggestions
        improvement_suggestions = self._generate_improvement_suggestions(
            recommendations, feedback_categories, common_issues
        )
        
        # Calculate satisfaction score
        satisfaction_score = self._calculate_satisfaction_score(
            average_rating, rating_trend, feedback_categories
        )
        
        return ImprovementMetrics(
            user_id=str(user.id),
            time_period=period,
            total_recommendations=len(recommendations),
            average_rating=round(average_rating, 2),
            rating_trend=round(rating_trend, 3),
            feedback_categories=feedback_categories,
            common_issues=common_issues,
            improvement_suggestions=improvement_suggestions,
            satisfaction_score=round(satisfaction_score, 2)
        )
    
    def analyze_recommendation_patterns(
        self,
        db: Session,
        user: User,
        limit: int = 10
    ) -> List[RecommendationPattern]:
        """
        Analyze patterns in user's recommendation history
        
        Args:
            db: Database session
            user: User object
            limit: Maximum number of patterns to return
            
        Returns:
            List of RecommendationPattern objects
        """
        logger.info(f"Analyzing recommendation patterns for user {user.id}")
        
        # Get user's recommendations with feedback
        recommendations = db.query(OutfitRecommendation).filter(
            and_(
                OutfitRecommendation.user_id == user.id,
                OutfitRecommendation.feedback_score.isnot(None)
            )
        ).all()
        
        if len(recommendations) < self.min_recommendations_for_analysis:
            return []
        
        patterns = []
        
        # Analyze occasion patterns
        occasion_patterns = self._analyze_occasion_patterns(recommendations)
        patterns.extend(occasion_patterns)
        
        # Analyze weather patterns
        weather_patterns = self._analyze_weather_patterns(recommendations)
        patterns.extend(weather_patterns)
        
        # Analyze style patterns
        style_patterns = self._analyze_style_patterns(recommendations)
        patterns.extend(style_patterns)
        
        # Sort by success rate and frequency
        patterns.sort(key=lambda x: (x.success_rate, x.frequency), reverse=True)
        
        return patterns[:limit]
    
    def get_improvement_recommendations(
        self,
        db: Session,
        user: User
    ) -> Dict[str, Any]:
        """
        Get comprehensive improvement recommendations for a user
        
        Args:
            db: Database session
            user: User object
            
        Returns:
            Dictionary with improvement recommendations
        """
        logger.info(f"Generating improvement recommendations for user {user.id}")
        
        # Get metrics for different periods
        week_metrics = self.analyze_user_improvement_metrics(db, user, 'week')
        month_metrics = self.analyze_user_improvement_metrics(db, user, 'month')
        
        # Get patterns
        patterns = self.analyze_recommendation_patterns(db, user)
        
        # Analyze closet gaps
        closet_gaps = self._analyze_closet_gaps(db, user)
        
        # Generate personalized recommendations
        personalized_tips = self._generate_personalized_tips(
            week_metrics, month_metrics, patterns, closet_gaps
        )
        
        return {
            "user_id": str(user.id),
            "analysis_date": datetime.utcnow().isoformat(),
            "metrics": {
                "week": week_metrics,
                "month": month_metrics
            },
            "patterns": [
                {
                    "type": pattern.pattern_type,
                    "description": pattern.description,
                    "frequency": pattern.frequency,
                    "success_rate": pattern.success_rate,
                    "satisfaction": pattern.user_satisfaction
                }
                for pattern in patterns
            ],
            "closet_gaps": closet_gaps,
            "personalized_tips": personalized_tips,
            "next_steps": self._generate_next_steps(week_metrics, month_metrics, closet_gaps)
        }
    
    def track_recommendation_performance(
        self,
        db: Session,
        recommendation_id: str,
        feedback_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Track performance of a specific recommendation
        
        Args:
            db: Database session
            recommendation_id: Recommendation ID
            feedback_data: Feedback data from user
            
        Returns:
            Performance tracking data
        """
        import uuid
        
        try:
            rec_uuid = uuid.UUID(recommendation_id)
        except ValueError:
            logger.error(f"Invalid recommendation ID format: {recommendation_id}")
            return {"error": "Invalid recommendation ID"}
        
        # Get recommendation
        recommendation = db.query(OutfitRecommendation).filter(
            OutfitRecommendation.id == rec_uuid
        ).first()
        
        if not recommendation:
            logger.error(f"Recommendation not found: {recommendation_id}")
            return {"error": "Recommendation not found"}
        
        # Calculate performance metrics
        performance_data = {
            "recommendation_id": recommendation_id,
            "user_id": str(recommendation.user_id),
            "rating": feedback_data.get("rating"),
            "feedback_type": feedback_data.get("feedback_type"),
            "processing_time": recommendation.processing_time_ms,
            "matching_scores": recommendation.similarity_scores or {},
            "improvement_areas": self._identify_improvement_areas(feedback_data),
            "success_indicators": self._identify_success_indicators(feedback_data),
            "tracked_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Tracked performance for recommendation {recommendation_id}")
        return performance_data
    
    def _create_empty_metrics(self, user_id: str, period: str) -> ImprovementMetrics:
        """Create empty metrics for insufficient data"""
        return ImprovementMetrics(
            user_id=user_id,
            time_period=period,
            total_recommendations=0,
            average_rating=0.0,
            rating_trend=0.0,
            feedback_categories={},
            common_issues=["Insufficient data for analysis"],
            improvement_suggestions=["Generate more recommendations to enable analysis"],
            satisfaction_score=0.0
        )
    
    def _calculate_rating_trend(self, ratings: List[float]) -> float:
        """Calculate trend in ratings over time"""
        if len(ratings) < 4:
            return 0.0
        
        # Split into first and second half
        mid_point = len(ratings) // 2
        first_half = ratings[:mid_point]
        second_half = ratings[mid_point:]
        
        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)
        
        return second_avg - first_avg
    
    def _analyze_feedback_categories(
        self,
        db: Session,
        user_id: str,
        start_date: datetime
    ) -> Dict[str, int]:
        """Analyze feedback categories for the user"""
        feedback_records = db.query(RecommendationFeedback).join(
            OutfitRecommendation
        ).filter(
            and_(
                OutfitRecommendation.user_id == user_id,
                RecommendationFeedback.created_at >= start_date
            )
        ).all()
        
        categories = Counter()
        for feedback in feedback_records:
            if feedback.feedback_type:
                categories[feedback.feedback_type] += 1
        
        return dict(categories)
    
    def _identify_common_issues(
        self,
        db: Session,
        user_id: str,
        start_date: datetime
    ) -> List[str]:
        """Identify common issues from feedback"""
        feedback_records = db.query(RecommendationFeedback).join(
            OutfitRecommendation
        ).filter(
            and_(
                OutfitRecommendation.user_id == user_id,
                RecommendationFeedback.created_at >= start_date,
                RecommendationFeedback.rating <= 3  # Low ratings
            )
        ).all()
        
        issues = []
        issue_patterns = {
            'style_mismatch': 'Style preferences not matching recommendations',
            'item_specific': 'Issues with specific clothing items',
            'occasion_mismatch': 'Recommendations not suitable for occasions',
            'color_preference': 'Color combinations not preferred'
        }
        
        feedback_types = [f.feedback_type for f in feedback_records if f.feedback_type]
        common_types = Counter(feedback_types).most_common(3)
        
        for feedback_type, count in common_types:
            if feedback_type in issue_patterns:
                issues.append(issue_patterns[feedback_type])
        
        return issues
    
    def _generate_improvement_suggestions(
        self,
        recommendations: List[OutfitRecommendation],
        feedback_categories: Dict[str, int],
        common_issues: List[str]
    ) -> List[str]:
        """Generate improvement suggestions based on analysis"""
        suggestions = []
        
        # Analyze rating distribution
        ratings = [r.feedback_score for r in recommendations if r.feedback_score]
        if ratings:
            avg_rating = statistics.mean(ratings)
            
            if avg_rating < 3.5:
                suggestions.append("Consider updating style preferences in your profile")
                suggestions.append("Upload more diverse clothing items to improve matching")
            
            if 'style_mismatch' in feedback_categories:
                suggestions.append("Review and refine your style quiz responses")
            
            if 'occasion_mismatch' in feedback_categories:
                suggestions.append("Be more specific about occasions in your requests")
            
            if 'color_preference' in feedback_categories:
                suggestions.append("Specify color preferences in your outfit requests")
        
        # Add general suggestions if no specific issues found
        if not suggestions:
            suggestions.extend([
                "Continue providing feedback to improve recommendations",
                "Try requesting outfits for different occasions",
                "Upload more clothing items to expand matching options"
            ])
        
        return suggestions[:5]  # Limit to top 5 suggestions
    
    def _calculate_satisfaction_score(
        self,
        average_rating: float,
        rating_trend: float,
        feedback_categories: Dict[str, int]
    ) -> float:
        """Calculate overall satisfaction score"""
        # Base score from average rating (0-5 scale converted to 0-100)
        base_score = (average_rating / 5.0) * 100
        
        # Adjust for trend (positive trend adds points, negative subtracts)
        trend_adjustment = rating_trend * 10
        
        # Adjust for feedback diversity (more feedback types = more engagement)
        diversity_bonus = min(len(feedback_categories) * 2, 10)
        
        satisfaction_score = base_score + trend_adjustment + diversity_bonus
        
        # Ensure score is between 0 and 100
        return max(0, min(100, satisfaction_score))
    
    def _analyze_occasion_patterns(
        self,
        recommendations: List[OutfitRecommendation]
    ) -> List[RecommendationPattern]:
        """Analyze patterns by occasion"""
        occasion_data = defaultdict(list)
        
        for rec in recommendations:
            if rec.occasion and rec.feedback_score:
                occasion_data[rec.occasion].append(rec)
        
        patterns = []
        for occasion, recs in occasion_data.items():
            if len(recs) >= 2:  # Need at least 2 recommendations
                ratings = [r.feedback_score for r in recs]
                avg_rating = statistics.mean(ratings)
                success_rate = len([r for r in ratings if r >= 4]) / len(ratings)
                
                patterns.append(RecommendationPattern(
                    pattern_type="occasion",
                    description=f"Recommendations for {occasion} occasions",
                    frequency=len(recs),
                    success_rate=success_rate,
                    user_satisfaction=avg_rating,
                    recommendations=[str(r.id) for r in recs]
                ))
        
        return patterns
    
    def _analyze_weather_patterns(
        self,
        recommendations: List[OutfitRecommendation]
    ) -> List[RecommendationPattern]:
        """Analyze patterns by weather"""
        weather_data = defaultdict(list)
        
        for rec in recommendations:
            if rec.weather and rec.feedback_score:
                weather_data[rec.weather].append(rec)
        
        patterns = []
        for weather, recs in weather_data.items():
            if len(recs) >= 2:
                ratings = [r.feedback_score for r in recs]
                avg_rating = statistics.mean(ratings)
                success_rate = len([r for r in ratings if r >= 4]) / len(ratings)
                
                patterns.append(RecommendationPattern(
                    pattern_type="weather",
                    description=f"Recommendations for {weather} weather",
                    frequency=len(recs),
                    success_rate=success_rate,
                    user_satisfaction=avg_rating,
                    recommendations=[str(r.id) for r in recs]
                ))
        
        return patterns
    
    def _analyze_style_patterns(
        self,
        recommendations: List[OutfitRecommendation]
    ) -> List[RecommendationPattern]:
        """Analyze patterns by AI model used (style-based)"""
        model_data = defaultdict(list)
        
        for rec in recommendations:
            if rec.ai_model_used and rec.feedback_score:
                model_data[rec.ai_model_used].append(rec)
        
        patterns = []
        for model, recs in model_data.items():
            if len(recs) >= 2:
                ratings = [r.feedback_score for r in recs]
                avg_rating = statistics.mean(ratings)
                success_rate = len([r for r in ratings if r >= 4]) / len(ratings)
                
                patterns.append(RecommendationPattern(
                    pattern_type="style",
                    description=f"Recommendations using {model} model",
                    frequency=len(recs),
                    success_rate=success_rate,
                    user_satisfaction=avg_rating,
                    recommendations=[str(r.id) for r in recs]
                ))
        
        return patterns
    
    def _analyze_closet_gaps(self, db: Session, user: User) -> List[Dict[str, Any]]:
        """Analyze gaps in user's closet based on recommendation patterns"""
        # Get user's clothing items
        closet_items = db.query(ClothingItem).filter(
            ClothingItem.user_id == user.id
        ).all()
        
        # Count items by category
        category_counts = Counter(item.category.lower() for item in closet_items)
        
        # Define ideal minimums for a well-rounded closet
        ideal_minimums = {
            'top': 8,
            'bottom': 6,
            'shoes': 4,
            'outerwear': 3,
            'accessory': 5
        }
        
        gaps = []
        for category, ideal_min in ideal_minimums.items():
            current_count = category_counts.get(category, 0)
            if current_count < ideal_min:
                gap_size = ideal_min - current_count
                gaps.append({
                    "category": category,
                    "current_count": current_count,
                    "recommended_minimum": ideal_min,
                    "gap_size": gap_size,
                    "priority": "high" if gap_size >= 3 else "medium" if gap_size >= 2 else "low"
                })
        
        return gaps
    
    def _generate_personalized_tips(
        self,
        week_metrics: ImprovementMetrics,
        month_metrics: ImprovementMetrics,
        patterns: List[RecommendationPattern],
        closet_gaps: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate personalized tips based on analysis"""
        tips = []
        
        # Tips based on rating trends
        if month_metrics.rating_trend > 0.5:
            tips.append("Great progress! Your satisfaction with recommendations is improving.")
        elif month_metrics.rating_trend < -0.5:
            tips.append("Consider updating your style preferences - your satisfaction seems to be declining.")
        
        # Tips based on patterns
        successful_patterns = [p for p in patterns if p.success_rate > 0.7]
        if successful_patterns:
            best_pattern = max(successful_patterns, key=lambda x: x.success_rate)
            tips.append(f"You seem to love {best_pattern.description.lower()} - request more of these!")
        
        # Tips based on closet gaps
        high_priority_gaps = [g for g in closet_gaps if g["priority"] == "high"]
        if high_priority_gaps:
            gap_categories = [g["category"] for g in high_priority_gaps]
            tips.append(f"Consider adding more {', '.join(gap_categories)} items to improve recommendations.")
        
        # General tips
        if month_metrics.total_recommendations < 10:
            tips.append("Try requesting more outfit recommendations to help us learn your preferences better.")
        
        if not tips:
            tips.append("Keep providing feedback to help us improve your recommendations!")
        
        return tips[:5]  # Limit to top 5 tips
    
    def _generate_next_steps(
        self,
        week_metrics: ImprovementMetrics,
        month_metrics: ImprovementMetrics,
        closet_gaps: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate actionable next steps"""
        next_steps = []
        
        if month_metrics.average_rating < 3.5:
            next_steps.append("Retake the style quiz to better align recommendations with your preferences")
        
        if closet_gaps:
            priority_gap = max(closet_gaps, key=lambda x: x["gap_size"])
            next_steps.append(f"Upload {priority_gap['gap_size']} more {priority_gap['category']} items")
        
        if week_metrics.total_recommendations < 3:
            next_steps.append("Request 2-3 more outfit recommendations this week")
        
        next_steps.append("Continue providing detailed feedback on recommendations")
        
        return next_steps[:4]  # Limit to top 4 steps
    
    def _identify_improvement_areas(self, feedback_data: Dict[str, Any]) -> List[str]:
        """Identify areas for improvement based on feedback"""
        areas = []
        
        rating = feedback_data.get("rating", 5)
        if rating <= 3:
            if feedback_data.get("style_accuracy", 5) <= 3:
                areas.append("style_matching")
            if feedback_data.get("item_matching", 5) <= 3:
                areas.append("closet_matching")
            if feedback_data.get("occasion_appropriateness", 5) <= 3:
                areas.append("occasion_matching")
        
        return areas
    
    def _identify_success_indicators(self, feedback_data: Dict[str, Any]) -> List[str]:
        """Identify success indicators from feedback"""
        indicators = []
        
        rating = feedback_data.get("rating", 0)
        if rating >= 4:
            indicators.append("high_satisfaction")
        
        if feedback_data.get("style_accuracy", 0) >= 4:
            indicators.append("good_style_match")
        
        if feedback_data.get("item_matching", 0) >= 4:
            indicators.append("good_closet_match")
        
        if "stylish" in feedback_data.get("feedback_tags", []):
            indicators.append("stylish_recommendation")
        
        return indicators


# Global service instance
improvement_service = None

def get_improvement_service():
    """Get or create the global improvement service instance"""
    global improvement_service
    if improvement_service is None:
        improvement_service = RecommendationImprovementService()
    return improvement_service