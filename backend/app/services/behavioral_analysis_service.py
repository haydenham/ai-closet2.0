"""
Behavioral Analysis Service for validating style assignments and improving algorithms
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, Counter
from decimal import Decimal
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

from app.models.quiz_system import (
    QuizResponse, QuizClothingItem, StyleCategory, StyleAssignmentFeedback,
    FeatureLearningData, FeatureCorrelation
)
from app.models.user import User
from app.models.clothing_item import ClothingItem

logger = logging.getLogger(__name__)


class BehavioralAnalysisService:
    """Service for analyzing user behavior to validate and improve style assignments"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Analysis parameters
        self.min_data_points = 5
        self.confidence_threshold = 0.7
        self.trend_significance_threshold = 0.1
    
    def analyze_style_assignment_accuracy(self, 
                                        time_period_days: int = 30) -> Dict[str, Any]:
        """
        Analyze accuracy of style assignments based on user behavior and feedback
        
        Args:
            time_period_days: Number of days to analyze
            
        Returns:
            Style assignment accuracy analysis
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=time_period_days)
            
            # Get quiz responses with feedback from the time period
            responses_with_feedback = self.db.query(QuizResponse).join(
                StyleAssignmentFeedback
            ).filter(
                QuizResponse.completed_at >= cutoff_date
            ).all()
            
            if not responses_with_feedback:
                return {'error': 'No feedback data available for analysis'}
            
            analysis = {
                'time_period_days': time_period_days,
                'total_responses_analyzed': len(responses_with_feedback),
                'style_accuracy': {},
                'overall_metrics': {},
                'improvement_recommendations': []
            }
            
            # Group by style category
            style_data = defaultdict(list)
            overall_ratings = []
            
            for response in responses_with_feedback:
                style = response.assigned_category
                
                # Get feedback for this response
                feedback = self.db.query(StyleAssignmentFeedback).filter(
                    StyleAssignmentFeedback.quiz_response_id == response.id
                ).first()
                
                if feedback:
                    style_data[style].append({
                        'accuracy_rating': feedback.accuracy_rating,
                        'user_satisfaction': response.user_satisfaction_rating,
                        'feedback_type': feedback.feedback_type,
                        'confidence_score': float(response.confidence_score or 0)
                    })
                    overall_ratings.append(feedback.accuracy_rating)
            
            # Calculate style-specific metrics
            for style, data_points in style_data.items():
                if len(data_points) >= self.min_data_points:
                    accuracy_ratings = [d['accuracy_rating'] for d in data_points]
                    satisfaction_ratings = [d['user_satisfaction'] for d in data_points if d['user_satisfaction']]
                    confidence_scores = [d['confidence_score'] for d in data_points]
                    
                    analysis['style_accuracy'][style] = {
                        'sample_size': len(data_points),
                        'average_accuracy': np.mean(accuracy_ratings),
                        'accuracy_std': np.std(accuracy_ratings),
                        'high_accuracy_rate': len([r for r in accuracy_ratings if r >= 4]) / len(accuracy_ratings),
                        'average_satisfaction': np.mean(satisfaction_ratings) if satisfaction_ratings else None,
                        'average_confidence': np.mean(confidence_scores),
                        'feedback_distribution': Counter([d['feedback_type'] for d in data_points])
                    }
                    
                    # Generate recommendations for low-performing styles
                    if analysis['style_accuracy'][style]['high_accuracy_rate'] < 0.6:
                        analysis['improvement_recommendations'].append({
                            'type': 'style_accuracy_improvement',
                            'style': style,
                            'issue': 'Low accuracy rate',
                            'current_rate': analysis['style_accuracy'][style]['high_accuracy_rate'],
                            'recommendation': f'Review feature mapping and quiz questions for {style} style'
                        })
            
            # Calculate overall metrics
            if overall_ratings:
                analysis['overall_metrics'] = {
                    'average_accuracy': np.mean(overall_ratings),
                    'accuracy_std': np.std(overall_ratings),
                    'high_accuracy_rate': len([r for r in overall_ratings if r >= 4]) / len(overall_ratings),
                    'styles_analyzed': len(style_data)
                }
            
            logger.info(f"Analyzed style assignment accuracy for {len(responses_with_feedback)} responses")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing style assignment accuracy: {str(e)}")
            return {'error': str(e)}
    
    def analyze_user_upload_patterns(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze user upload patterns to validate style assignments
        
        Args:
            user_id: Optional specific user ID to analyze
            
        Returns:
            Upload pattern analysis
        """
        try:
            # Get user clothing uploads
            query = self.db.query(ClothingItem)
            if user_id:
                query = query.filter(ClothingItem.user_id == user_id)
            
            uploads = query.all()
            
            if not uploads:
                return {'error': 'No upload data available'}
            
            # Get quiz responses for users with uploads
            user_ids = list(set([upload.user_id for upload in uploads]))
            quiz_responses = self.db.query(QuizResponse).filter(
                QuizResponse.user_id.in_(user_ids)
            ).all()
            
            analysis = {
                'total_users_analyzed': len(user_ids),
                'total_uploads': len(uploads),
                'style_consistency': {},
                'feature_alignment': {},
                'upload_behavior_insights': []
            }
            
            # Group data by user
            user_data = defaultdict(lambda: {'uploads': [], 'quiz_response': None})
            
            for upload in uploads:
                user_data[upload.user_id]['uploads'].append(upload)
            
            for response in quiz_responses:
                user_data[response.user_id]['quiz_response'] = response
            
            # Analyze each user's consistency
            style_consistency_scores = []
            feature_alignment_scores = []
            
            for user_id, data in user_data.items():
                if not data['quiz_response'] or len(data['uploads']) < 3:
                    continue  # Need minimum data for analysis
                
                assigned_style = data['quiz_response'].assigned_category
                user_uploads = data['uploads']
                
                # Analyze style consistency
                consistency_score = self._calculate_style_consistency(
                    assigned_style, user_uploads
                )
                style_consistency_scores.append(consistency_score)
                
                # Analyze feature alignment
                alignment_score = self._calculate_feature_alignment(
                    data['quiz_response'], user_uploads
                )
                feature_alignment_scores.append(alignment_score)
            
            # Calculate aggregate metrics
            if style_consistency_scores:
                analysis['style_consistency'] = {
                    'average_consistency': np.mean(style_consistency_scores),
                    'consistency_std': np.std(style_consistency_scores),
                    'high_consistency_rate': len([s for s in style_consistency_scores if s >= 0.7]) / len(style_consistency_scores)
                }
            
            if feature_alignment_scores:
                analysis['feature_alignment'] = {
                    'average_alignment': np.mean(feature_alignment_scores),
                    'alignment_std': np.std(feature_alignment_scores),
                    'high_alignment_rate': len([s for s in feature_alignment_scores if s >= 0.6]) / len(feature_alignment_scores)
                }
            
            # Generate insights
            if analysis['style_consistency'].get('high_consistency_rate', 0) < 0.5:
                analysis['upload_behavior_insights'].append({
                    'type': 'low_style_consistency',
                    'message': 'Users\' actual uploads don\'t align well with assigned styles',
                    'recommendation': 'Review style assignment algorithm and feature weights'
                })
            
            if analysis['feature_alignment'].get('high_alignment_rate', 0) < 0.5:
                analysis['upload_behavior_insights'].append({
                    'type': 'low_feature_alignment',
                    'message': 'User uploads don\'t match expected features from quiz responses',
                    'recommendation': 'Improve feature extraction and quiz question design'
                })
            
            logger.info(f"Analyzed upload patterns for {len(user_ids)} users")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing upload patterns: {str(e)}")
            return {'error': str(e)}
    
    def detect_algorithm_drift(self, lookback_days: int = 90) -> Dict[str, Any]:
        """
        Detect algorithm performance drift over time
        
        Args:
            lookback_days: Number of days to analyze for drift
            
        Returns:
            Algorithm drift analysis
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
            
            # Get quiz responses with satisfaction ratings over time
            responses = self.db.query(QuizResponse).filter(
                and_(
                    QuizResponse.completed_at >= cutoff_date,
                    QuizResponse.user_satisfaction_rating.isnot(None)
                )
            ).order_by(QuizResponse.completed_at).all()
            
            if len(responses) < 20:  # Need minimum data for drift detection
                return {'error': 'Insufficient data for drift detection'}
            
            # Split data into time windows
            window_size = max(7, lookback_days // 10)  # At least 7 days per window
            windows = []
            current_window = []
            current_date = responses[0].completed_at.date()
            
            for response in responses:
                response_date = response.completed_at.date()
                
                if (response_date - current_date).days >= window_size:
                    if current_window:
                        windows.append(current_window)
                    current_window = [response]
                    current_date = response_date
                else:
                    current_window.append(response)
            
            if current_window:
                windows.append(current_window)
            
            if len(windows) < 3:
                return {'error': 'Insufficient time windows for drift analysis'}
            
            # Analyze metrics for each window
            window_metrics = []
            
            for i, window in enumerate(windows):
                satisfaction_scores = [r.user_satisfaction_rating for r in window]
                confidence_scores = [float(r.confidence_score or 0) for r in window]
                
                metrics = {
                    'window_index': i,
                    'start_date': min([r.completed_at for r in window]).date(),
                    'end_date': max([r.completed_at for r in window]).date(),
                    'sample_size': len(window),
                    'avg_satisfaction': np.mean(satisfaction_scores),
                    'avg_confidence': np.mean(confidence_scores),
                    'high_satisfaction_rate': len([s for s in satisfaction_scores if s >= 4]) / len(satisfaction_scores)
                }
                window_metrics.append(metrics)
            
            # Detect trends
            satisfaction_trend = np.polyfit(
                range(len(window_metrics)),
                [w['avg_satisfaction'] for w in window_metrics],
                1
            )[0]
            
            confidence_trend = np.polyfit(
                range(len(window_metrics)),
                [w['avg_confidence'] for w in window_metrics],
                1
            )[0]
            
            analysis = {
                'lookback_days': lookback_days,
                'total_responses': len(responses),
                'time_windows': len(windows),
                'window_metrics': window_metrics,
                'drift_analysis': {
                    'satisfaction_trend': float(satisfaction_trend),
                    'confidence_trend': float(confidence_trend),
                    'satisfaction_declining': satisfaction_trend < -self.trend_significance_threshold,
                    'confidence_declining': confidence_trend < -self.trend_significance_threshold,
                    'performance_stable': abs(satisfaction_trend) <= self.trend_significance_threshold
                },
                'alerts': []
            }
            
            # Generate alerts
            if analysis['drift_analysis']['satisfaction_declining']:
                analysis['alerts'].append({
                    'type': 'satisfaction_decline',
                    'severity': 'high' if satisfaction_trend < -0.2 else 'medium',
                    'message': f'User satisfaction declining at rate of {satisfaction_trend:.3f} per time window',
                    'recommendation': 'Investigate recent algorithm changes and user feedback'
                })
            
            if analysis['drift_analysis']['confidence_declining']:
                analysis['alerts'].append({
                    'type': 'confidence_decline',
                    'severity': 'medium',
                    'message': f'Algorithm confidence declining at rate of {confidence_trend:.3f} per time window',
                    'recommendation': 'Review feature extraction and matching algorithms'
                })
            
            # Check for sudden drops
            for i in range(1, len(window_metrics)):
                prev_satisfaction = window_metrics[i-1]['avg_satisfaction']
                curr_satisfaction = window_metrics[i]['avg_satisfaction']
                
                if prev_satisfaction - curr_satisfaction > 0.5:  # Significant drop
                    analysis['alerts'].append({
                        'type': 'sudden_satisfaction_drop',
                        'severity': 'high',
                        'window': i,
                        'drop_amount': prev_satisfaction - curr_satisfaction,
                        'message': f'Sudden satisfaction drop of {prev_satisfaction - curr_satisfaction:.2f} in window {i}',
                        'recommendation': 'Investigate changes made around this time period'
                    })
            
            logger.info(f"Detected algorithm drift analysis with {len(analysis['alerts'])} alerts")
            return analysis
            
        except Exception as e:
            logger.error(f"Error detecting algorithm drift: {str(e)}")
            return {'error': str(e)}
    
    def generate_improvement_recommendations(self) -> List[Dict[str, Any]]:
        """
        Generate comprehensive improvement recommendations based on behavioral analysis
        
        Returns:
            List of improvement recommendations
        """
        try:
            recommendations = []
            
            # Analyze recent performance
            style_accuracy = self.analyze_style_assignment_accuracy(30)
            upload_patterns = self.analyze_user_upload_patterns()
            drift_analysis = self.detect_algorithm_drift(60)
            
            # Style-specific recommendations
            if 'style_accuracy' in style_accuracy:
                for style, metrics in style_accuracy['style_accuracy'].items():
                    if metrics['high_accuracy_rate'] < 0.6:
                        recommendations.append({
                            'priority': 'high',
                            'category': 'style_improvement',
                            'style': style,
                            'issue': f'Low accuracy rate: {metrics["high_accuracy_rate"]:.2f}',
                            'recommendation': f'Review and update feature mappings for {style} style category',
                            'expected_impact': 'Improve user satisfaction by 15-25%',
                            'implementation_effort': 'medium'
                        })
            
            # Feature alignment recommendations
            if upload_patterns.get('feature_alignment', {}).get('high_alignment_rate', 1) < 0.5:
                recommendations.append({
                    'priority': 'high',
                    'category': 'feature_extraction',
                    'issue': 'Low feature alignment between quiz and uploads',
                    'recommendation': 'Improve computer vision feature extraction accuracy',
                    'expected_impact': 'Better style assignment accuracy',
                    'implementation_effort': 'high'
                })
            
            # Algorithm drift recommendations
            if drift_analysis.get('drift_analysis', {}).get('satisfaction_declining'):
                recommendations.append({
                    'priority': 'critical',
                    'category': 'algorithm_performance',
                    'issue': 'Declining user satisfaction trend detected',
                    'recommendation': 'Investigate recent algorithm changes and revert if necessary',
                    'expected_impact': 'Stop satisfaction decline',
                    'implementation_effort': 'medium'
                })
            
            # Data quality recommendations
            learning_data_quality = self._assess_learning_data_quality()
            if learning_data_quality['needs_improvement']:
                recommendations.append({
                    'priority': 'medium',
                    'category': 'data_quality',
                    'issue': 'Learning data quality issues detected',
                    'recommendation': 'Implement data validation and cleaning procedures',
                    'expected_impact': 'More reliable feature learning',
                    'implementation_effort': 'low'
                })
            
            # Sort by priority
            priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
            recommendations.sort(key=lambda x: priority_order.get(x['priority'], 3))
            
            logger.info(f"Generated {len(recommendations)} improvement recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating improvement recommendations: {str(e)}")
            return []
    
    # Private helper methods
    
    def _calculate_style_consistency(self, assigned_style: str, 
                                   user_uploads: List[ClothingItem]) -> float:
        """Calculate how consistent user uploads are with assigned style"""
        try:
            # Get style category features
            style_category = self.db.query(StyleCategory).filter(
                StyleCategory.name == assigned_style
            ).first()
            
            if not style_category or not style_category.features:
                return 0.0
            
            expected_features = set(style_category.features)
            
            # Analyze user uploads for matching features
            matching_scores = []
            
            for upload in user_uploads:
                # For now, we'll use a simple heuristic based on category and color
                # In a full implementation, this would use computer vision analysis
                upload_features = set()
                
                if upload.category:
                    upload_features.add(upload.category.lower())
                if upload.color:
                    upload_features.add(upload.color.lower())
                
                # Calculate overlap with expected features
                overlap = len(expected_features & upload_features)
                total_expected = len(expected_features)
                
                if total_expected > 0:
                    matching_scores.append(overlap / total_expected)
            
            return np.mean(matching_scores) if matching_scores else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating style consistency: {str(e)}")
            return 0.0
    
    def _calculate_feature_alignment(self, quiz_response: QuizResponse, 
                                   user_uploads: List[ClothingItem]) -> float:
        """Calculate alignment between quiz features and upload features"""
        try:
            # Get features from quiz selected items
            quiz_features = set()
            
            for item in quiz_response.selected_items:
                if item.features:
                    quiz_features.update(item.features)
                if item.auto_extracted_features:
                    quiz_features.update(item.auto_extracted_features)
            
            if not quiz_features:
                return 0.0
            
            # Analyze upload features (simplified for this implementation)
            upload_features = set()
            
            for upload in user_uploads:
                if upload.category:
                    upload_features.add(upload.category.lower())
                if upload.color:
                    upload_features.add(upload.color.lower())
            
            # Calculate Jaccard similarity
            intersection = len(quiz_features & upload_features)
            union = len(quiz_features | upload_features)
            
            return intersection / union if union > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating feature alignment: {str(e)}")
            return 0.0
    
    def _assess_learning_data_quality(self) -> Dict[str, Any]:
        """Assess quality of learning data"""
        try:
            # Get learning data statistics
            total_entries = self.db.query(FeatureLearningData).count()
            validated_entries = self.db.query(FeatureLearningData).filter(
                FeatureLearningData.validation_count > 0
            ).count()
            
            low_confidence_entries = self.db.query(FeatureLearningData).filter(
                FeatureLearningData.confidence_score < 0.5
            ).count()
            
            validation_rate = validated_entries / total_entries if total_entries > 0 else 0
            low_confidence_rate = low_confidence_entries / total_entries if total_entries > 0 else 0
            
            needs_improvement = (
                validation_rate < 0.3 or  # Less than 30% validated
                low_confidence_rate > 0.4  # More than 40% low confidence
            )
            
            return {
                'total_entries': total_entries,
                'validation_rate': validation_rate,
                'low_confidence_rate': low_confidence_rate,
                'needs_improvement': needs_improvement
            }
            
        except Exception as e:
            logger.error(f"Error assessing learning data quality: {str(e)}")
            return {'needs_improvement': False}