"""
Smart Feature Learning Service using GCP Vision API
Implements continuous learning algorithms for automatic feature discovery and validation
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
from collections import defaultdict, Counter
import numpy as np
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.core.database import get_sync_session
from app.models.quiz_system import (
    QuizClothingItem, FeatureLearningData, FeatureCorrelation,
    StyleAssignmentFeedback, QuizResponse, StyleCategory
)
from app.models.user import User
from app.services.gcp_vision_service import GCPVisionService

logger = logging.getLogger(__name__)


class FeatureLearningService:
    """Service for smart feature learning and algorithm improvement"""
    
    def __init__(self, db: Session):
        self.db = db
        self.vision_service = GCPVisionService()
        
        # Learning parameters
        self.min_confidence_threshold = 0.6
        self.min_validation_count = 3
        self.correlation_threshold = 0.3
        self.clustering_min_samples = 5
        
    async def extract_features_from_image(self, item_id: str, image_data: bytes) -> Dict[str, Any]:
        """
        Extract features from clothing image using GCP Vision API
        
        Args:
            item_id: ID of the clothing item
            image_data: Raw image bytes
            
        Returns:
            Dict containing extracted features and metadata
        """
        try:
            # Get existing item
            item = self.db.query(QuizClothingItem).filter(
                QuizClothingItem.id == item_id
            ).first()
            
            if not item:
                raise ValueError(f"Clothing item {item_id} not found")
            
            # Analyze image with Vision API
            analysis_result = self.vision_service.analyze_clothing_image(image_data)
            
            if 'error' in analysis_result:
                logger.error(f"Vision API error for item {item_id}: {analysis_result['error']}")
                return analysis_result
            
            # Store auto-extracted features
            extracted_features = analysis_result['extracted_features']
            confidence_scores = analysis_result['confidence_scores']
            
            # Update item with auto-extracted features
            item.auto_extracted_features = extracted_features
            item.feature_confidence_scores = confidence_scores
            
            # Create feature learning data entries
            for feature in extracted_features:
                confidence = confidence_scores.get(feature, 0.0)
                
                # Check if feature learning data already exists
                existing_data = self.db.query(FeatureLearningData).filter(
                    and_(
                        FeatureLearningData.item_id == item_id,
                        FeatureLearningData.feature_name == feature,
                        FeatureLearningData.source == 'cv_auto'
                    )
                ).first()
                
                if not existing_data:
                    learning_data = FeatureLearningData(
                        feature_name=feature,
                        item_id=item_id,
                        source='cv_auto',
                        confidence_score=Decimal(str(confidence))
                    )
                    self.db.add(learning_data)
                else:
                    # Update confidence score
                    existing_data.confidence_score = Decimal(str(confidence))
            
            self.db.commit()
            
            logger.info(f"Extracted {len(extracted_features)} features for item {item_id}")
            
            return {
                'item_id': item_id,
                'extracted_features': extracted_features,
                'confidence_scores': confidence_scores,
                'suggested_category': analysis_result.get('suggested_category'),
                'dominant_colors': analysis_result.get('dominant_colors', []),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error extracting features for item {item_id}: {str(e)}")
            return {
                'item_id': item_id,
                'error': str(e),
                'success': False
            }
    
    async def batch_extract_features(self, item_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Extract features from multiple items in batch
        
        Args:
            item_ids: List of clothing item IDs
            
        Returns:
            List of extraction results
        """
        results = []
        
        for item_id in item_ids:
            try:
                # Get item and download image
                item = self.db.query(QuizClothingItem).filter(
                    QuizClothingItem.id == item_id
                ).first()
                
                if not item:
                    results.append({
                        'item_id': item_id,
                        'error': 'Item not found',
                        'success': False
                    })
                    continue
                
                # Download image data (assuming we have a method to get image bytes)
                image_data = await self._download_image_data(item.image_url)
                
                if not image_data:
                    results.append({
                        'item_id': item_id,
                        'error': 'Failed to download image',
                        'success': False
                    })
                    continue
                
                # Extract features
                result = await self.extract_features_from_image(item_id, image_data)
                results.append(result)
                
                # Add small delay to avoid rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in batch extraction for item {item_id}: {str(e)}")
                results.append({
                    'item_id': item_id,
                    'error': str(e),
                    'success': False
                })
        
        return results
    
    def track_user_satisfaction(self, user_id: str, quiz_response_id: str, 
                              satisfaction_data: Dict[str, Any]) -> bool:
        """
        Track user satisfaction with style assignments and feature accuracy
        
        Args:
            user_id: User ID
            quiz_response_id: Quiz response ID
            satisfaction_data: Dict containing satisfaction metrics
            
        Returns:
            Success status
        """
        try:
            # Get quiz response
            quiz_response = self.db.query(QuizResponse).filter(
                QuizResponse.id == quiz_response_id
            ).first()
            
            if not quiz_response:
                logger.error(f"Quiz response {quiz_response_id} not found")
                return False
            
            # Update quiz response satisfaction
            quiz_response.user_satisfaction_rating = satisfaction_data.get('overall_rating')
            quiz_response.user_feedback_text = satisfaction_data.get('feedback_text')
            
            # Create detailed feedback entry
            feedback = StyleAssignmentFeedback(
                quiz_response_id=quiz_response_id,
                user_id=user_id,
                accuracy_rating=satisfaction_data.get('accuracy_rating', 3),
                preferred_style=satisfaction_data.get('preferred_style'),
                feedback_type=satisfaction_data.get('feedback_type', 'mostly_right'),
                feedback_text=satisfaction_data.get('detailed_feedback'),
                feature_feedback=satisfaction_data.get('feature_feedback', {})
            )
            
            self.db.add(feedback)
            
            # Update satisfaction scores for selected items
            for item in quiz_response.selected_items:
                item_satisfaction = satisfaction_data.get('item_ratings', {}).get(str(item.id))
                if item_satisfaction:
                    item.update_satisfaction_score(item_satisfaction)
            
            self.db.commit()
            
            # Trigger feature validation based on feedback
            self._validate_features_from_feedback(feedback)
            
            logger.info(f"Tracked satisfaction for user {user_id}, quiz {quiz_response_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking satisfaction: {str(e)}")
            self.db.rollback()
            return False
    
    def discover_feature_patterns(self, min_support: float = 0.1) -> List[Dict[str, Any]]:
        """
        Discover new feature patterns using clustering algorithms
        
        Args:
            min_support: Minimum support threshold for pattern discovery
            
        Returns:
            List of discovered patterns
        """
        try:
            # Get all items with features
            items = self.db.query(QuizClothingItem).filter(
                QuizClothingItem.features.isnot(None)
            ).all()
            
            if len(items) < self.clustering_min_samples:
                logger.warning("Not enough items for pattern discovery")
                return []
            
            # Create feature matrix
            all_features = set()
            for item in items:
                if item.features:
                    all_features.update(item.features)
                if item.auto_extracted_features:
                    all_features.update(item.auto_extracted_features)
            
            all_features = list(all_features)
            feature_matrix = []
            
            for item in items:
                item_features = (item.features or []) + (item.auto_extracted_features or [])
                feature_vector = [1 if feature in item_features else 0 for feature in all_features]
                feature_matrix.append(feature_vector)
            
            feature_matrix = np.array(feature_matrix)
            
            # Apply DBSCAN clustering
            scaler = StandardScaler()
            scaled_features = scaler.fit_transform(feature_matrix)
            
            clustering = DBSCAN(eps=0.5, min_samples=self.clustering_min_samples)
            cluster_labels = clustering.fit_predict(scaled_features)
            
            # Analyze clusters
            discovered_patterns = []
            unique_labels = set(cluster_labels)
            
            for label in unique_labels:
                if label == -1:  # Noise cluster
                    continue
                
                cluster_items = [items[i] for i, l in enumerate(cluster_labels) if l == label]
                cluster_size = len(cluster_items)
                
                if cluster_size < self.clustering_min_samples:
                    continue
                
                # Find common features in cluster
                feature_counts = Counter()
                for item in cluster_items:
                    item_features = (item.features or []) + (item.auto_extracted_features or [])
                    feature_counts.update(item_features)
                
                # Features that appear in at least min_support of cluster items
                min_count = max(1, int(cluster_size * min_support))
                common_features = [
                    feature for feature, count in feature_counts.items() 
                    if count >= min_count
                ]
                
                if len(common_features) >= 2:  # At least 2 features for a pattern
                    pattern = {
                        'cluster_id': label,
                        'features': common_features,
                        'support': cluster_size / len(items),
                        'item_count': cluster_size,
                        'confidence': min(feature_counts.values()) / cluster_size,
                        'discovered_at': datetime.utcnow()
                    }
                    discovered_patterns.append(pattern)
            
            # Store discovered patterns as feature correlations
            for pattern in discovered_patterns:
                self._store_feature_pattern(pattern)
            
            logger.info(f"Discovered {len(discovered_patterns)} feature patterns")
            return discovered_patterns
            
        except Exception as e:
            logger.error(f"Error discovering feature patterns: {str(e)}")
            return []
    
    def validate_features(self, validation_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate features through expert review and user testing
        
        Args:
            validation_data: List of validation entries with feature assessments
            
        Returns:
            Validation results summary
        """
        try:
            validation_results = {
                'validated': 0,
                'rejected': 0,
                'pending': 0,
                'updated_features': []
            }
            
            for validation in validation_data:
                feature_name = validation['feature_name']
                item_id = validation['item_id']
                is_valid = validation['is_valid']
                validator_type = validation.get('validator_type', 'expert')  # expert, user, cv
                confidence = validation.get('confidence', 1.0)
                
                # Find feature learning data
                learning_data = self.db.query(FeatureLearningData).filter(
                    and_(
                        FeatureLearningData.feature_name == feature_name,
                        FeatureLearningData.item_id == item_id
                    )
                ).first()
                
                if not learning_data:
                    # Create new learning data entry
                    learning_data = FeatureLearningData(
                        feature_name=feature_name,
                        item_id=item_id,
                        source='user_suggested' if validator_type == 'user' else 'manual',
                        confidence_score=Decimal(str(confidence))
                    )
                    self.db.add(learning_data)
                
                # Update validation counts
                if is_valid:
                    learning_data.validation_count += 1
                    validation_results['validated'] += 1
                else:
                    learning_data.rejection_count += 1
                    validation_results['rejected'] += 1
                
                # Update item features based on validation
                item = self.db.query(QuizClothingItem).filter(
                    QuizClothingItem.id == item_id
                ).first()
                
                if item and is_valid and learning_data.validation_ratio >= 0.7:
                    # Add feature to item if validation ratio is high
                    if not item.has_feature(feature_name):
                        item.add_feature(feature_name)
                        validation_results['updated_features'].append({
                            'item_id': item_id,
                            'feature': feature_name,
                            'action': 'added'
                        })
                elif item and not is_valid and learning_data.validation_ratio <= 0.3:
                    # Remove feature if validation ratio is low
                    if item.has_feature(feature_name):
                        item.remove_feature(feature_name)
                        validation_results['updated_features'].append({
                            'item_id': item_id,
                            'feature': feature_name,
                            'action': 'removed'
                        })
            
            self.db.commit()
            
            logger.info(f"Validated {validation_results['validated']} features, "
                       f"rejected {validation_results['rejected']}")
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating features: {str(e)}")
            self.db.rollback()
            return {'error': str(e)}
    
    def mine_feature_correlations(self) -> List[Dict[str, Any]]:
        """
        Mine feature correlations to identify commonly co-occurring features
        
        Returns:
            List of feature correlation data
        """
        try:
            # Get all items with features
            items = self.db.query(QuizClothingItem).filter(
                QuizClothingItem.features.isnot(None)
            ).all()
            
            # Build feature co-occurrence matrix
            feature_pairs = defaultdict(int)
            feature_counts = defaultdict(int)
            total_items = len(items)
            
            for item in items:
                item_features = (item.features or []) + (item.auto_extracted_features or [])
                
                # Count individual features
                for feature in item_features:
                    feature_counts[feature] += 1
                
                # Count feature pairs
                for i, feature_a in enumerate(item_features):
                    for feature_b in item_features[i+1:]:
                        if feature_a != feature_b:
                            pair = tuple(sorted([feature_a, feature_b]))
                            feature_pairs[pair] += 1
            
            # Calculate correlations
            correlations = []
            
            for (feature_a, feature_b), co_count in feature_pairs.items():
                count_a = feature_counts[feature_a]
                count_b = feature_counts[feature_b]
                
                # Calculate correlation strength using lift
                expected = (count_a * count_b) / total_items
                lift = co_count / expected if expected > 0 else 0
                
                # Calculate confidence
                confidence_a_to_b = co_count / count_a if count_a > 0 else 0
                confidence_b_to_a = co_count / count_b if count_b > 0 else 0
                
                correlation_strength = min(lift, max(confidence_a_to_b, confidence_b_to_a))
                
                if correlation_strength >= self.correlation_threshold:
                    correlation_data = {
                        'feature_a': feature_a,
                        'feature_b': feature_b,
                        'correlation_strength': correlation_strength,
                        'co_occurrence_count': co_count,
                        'total_occurrences': count_a + count_b - co_count,
                        'lift': lift,
                        'confidence_a_to_b': confidence_a_to_b,
                        'confidence_b_to_a': confidence_b_to_a
                    }
                    correlations.append(correlation_data)
            
            # Store correlations in database
            for corr in correlations:
                existing_corr = self.db.query(FeatureCorrelation).filter(
                    or_(
                        and_(
                            FeatureCorrelation.feature_a == corr['feature_a'],
                            FeatureCorrelation.feature_b == corr['feature_b']
                        ),
                        and_(
                            FeatureCorrelation.feature_a == corr['feature_b'],
                            FeatureCorrelation.feature_b == corr['feature_a']
                        )
                    )
                ).first()
                
                if existing_corr:
                    # Update existing correlation
                    existing_corr.correlation_strength = Decimal(str(corr['correlation_strength']))
                    existing_corr.co_occurrence_count = corr['co_occurrence_count']
                    existing_corr.total_occurrences = corr['total_occurrences']
                else:
                    # Create new correlation
                    new_corr = FeatureCorrelation(
                        feature_a=corr['feature_a'],
                        feature_b=corr['feature_b'],
                        correlation_strength=Decimal(str(corr['correlation_strength'])),
                        co_occurrence_count=corr['co_occurrence_count'],
                        total_occurrences=corr['total_occurrences']
                    )
                    self.db.add(new_corr)
            
            self.db.commit()
            
            logger.info(f"Mined {len(correlations)} feature correlations")
            return correlations
            
        except Exception as e:
            logger.error(f"Error mining feature correlations: {str(e)}")
            return []    
    def analyze_behavioral_patterns(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze user behavior to validate style assignments
        
        Args:
            user_id: Optional specific user ID to analyze
            
        Returns:
            Behavioral analysis results
        """
        try:
            # Build query for user data
            query = self.db.query(QuizResponse)
            if user_id:
                query = query.filter(QuizResponse.user_id == user_id)
            
            quiz_responses = query.all()
            
            if not quiz_responses:
                return {'error': 'No quiz responses found'}
            
            analysis_results = {
                'total_responses': len(quiz_responses),
                'style_accuracy': {},
                'feature_preferences': {},
                'satisfaction_trends': {},
                'recommendations': []
            }
            
            # Analyze style assignment accuracy
            style_accuracy = defaultdict(list)
            feature_preferences = defaultdict(int)
            satisfaction_by_style = defaultdict(list)
            
            for response in quiz_responses:
                style = response.assigned_category
                satisfaction = response.user_satisfaction_rating
                
                if satisfaction:
                    style_accuracy[style].append(satisfaction)
                    satisfaction_by_style[style].append(satisfaction)
                
                # Analyze feature preferences from selected items
                for item in response.selected_items:
                    if item.features:
                        for feature in item.features:
                            feature_preferences[feature] += 1
            
            # Calculate style accuracy metrics
            for style, ratings in style_accuracy.items():
                analysis_results['style_accuracy'][style] = {
                    'average_satisfaction': sum(ratings) / len(ratings),
                    'response_count': len(ratings),
                    'high_satisfaction_rate': len([r for r in ratings if r >= 4]) / len(ratings)
                }
            
            # Identify top feature preferences
            total_selections = sum(feature_preferences.values())
            analysis_results['feature_preferences'] = {
                feature: {
                    'count': count,
                    'preference_rate': count / total_selections
                }
                for feature, count in sorted(feature_preferences.items(), 
                                           key=lambda x: x[1], reverse=True)[:20]
            }
            
            # Analyze satisfaction trends
            for style, satisfactions in satisfaction_by_style.items():
                if len(satisfactions) >= 3:  # Need minimum data points
                    trend = np.polyfit(range(len(satisfactions)), satisfactions, 1)[0]
                    analysis_results['satisfaction_trends'][style] = {
                        'trend_slope': float(trend),
                        'improving': trend > 0.1,
                        'declining': trend < -0.1,
                        'stable': abs(trend) <= 0.1
                    }
            
            # Generate recommendations
            recommendations = []
            
            # Recommend style category adjustments
            for style, accuracy in analysis_results['style_accuracy'].items():
                if accuracy['high_satisfaction_rate'] < 0.6:
                    recommendations.append({
                        'type': 'style_adjustment',
                        'style': style,
                        'issue': 'low_satisfaction',
                        'suggestion': f'Review feature mapping for {style} style category'
                    })
            
            # Recommend feature validation
            low_preference_features = [
                feature for feature, data in analysis_results['feature_preferences'].items()
                if data['preference_rate'] < 0.05
            ]
            
            if low_preference_features:
                recommendations.append({
                    'type': 'feature_validation',
                    'features': low_preference_features[:5],
                    'suggestion': 'Consider removing or re-evaluating these low-preference features'
                })
            
            analysis_results['recommendations'] = recommendations
            
            logger.info(f"Analyzed behavioral patterns for {len(quiz_responses)} responses")
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error analyzing behavioral patterns: {str(e)}")
            return {'error': str(e)}
    
    async def run_daily_improvement_cycle(self) -> Dict[str, Any]:
        """
        Run daily algorithm improvement cycle
        
        Returns:
            Summary of improvements made
        """
        try:
            improvement_summary = {
                'timestamp': datetime.utcnow(),
                'feature_extraction': {},
                'pattern_discovery': {},
                'correlation_mining': {},
                'behavioral_analysis': {},
                'validation_updates': {},
                'errors': []
            }
            
            logger.info("Starting daily improvement cycle")
            
            # 1. Extract features from new items (items without auto-extracted features)
            try:
                new_items = self.db.query(QuizClothingItem).filter(
                    or_(
                        QuizClothingItem.auto_extracted_features.is_(None),
                        QuizClothingItem.auto_extracted_features == []
                    )
                ).limit(50).all()  # Process up to 50 items per day
                
                if new_items:
                    item_ids = [str(item.id) for item in new_items]
                    extraction_results = await self.batch_extract_features(item_ids)
                    
                    successful_extractions = [r for r in extraction_results if r.get('success')]
                    improvement_summary['feature_extraction'] = {
                        'processed': len(extraction_results),
                        'successful': len(successful_extractions),
                        'failed': len(extraction_results) - len(successful_extractions)
                    }
                
            except Exception as e:
                error_msg = f"Feature extraction error: {str(e)}"
                logger.error(error_msg)
                improvement_summary['errors'].append(error_msg)
            
            # 2. Discover new feature patterns
            try:
                discovered_patterns = self.discover_feature_patterns()
                improvement_summary['pattern_discovery'] = {
                    'patterns_found': len(discovered_patterns),
                    'patterns': [p['features'] for p in discovered_patterns[:5]]  # Top 5
                }
            except Exception as e:
                error_msg = f"Pattern discovery error: {str(e)}"
                logger.error(error_msg)
                improvement_summary['errors'].append(error_msg)
            
            # 3. Mine feature correlations
            try:
                correlations = self.mine_feature_correlations()
                improvement_summary['correlation_mining'] = {
                    'correlations_found': len(correlations),
                    'strong_correlations': len([c for c in correlations if c['correlation_strength'] > 0.7])
                }
            except Exception as e:
                error_msg = f"Correlation mining error: {str(e)}"
                logger.error(error_msg)
                improvement_summary['errors'].append(error_msg)
            
            # 4. Analyze behavioral patterns
            try:
                behavioral_analysis = self.analyze_behavioral_patterns()
                improvement_summary['behavioral_analysis'] = {
                    'responses_analyzed': behavioral_analysis.get('total_responses', 0),
                    'recommendations_generated': len(behavioral_analysis.get('recommendations', []))
                }
            except Exception as e:
                error_msg = f"Behavioral analysis error: {str(e)}"
                logger.error(error_msg)
                improvement_summary['errors'].append(error_msg)
            
            # 5. Update feature validations based on recent feedback
            try:
                validation_updates = self._process_pending_validations()
                improvement_summary['validation_updates'] = validation_updates
            except Exception as e:
                error_msg = f"Validation update error: {str(e)}"
                logger.error(error_msg)
                improvement_summary['errors'].append(error_msg)
            
            # 6. Clean up old data
            try:
                cleanup_results = self._cleanup_old_learning_data()
                improvement_summary['cleanup'] = cleanup_results
            except Exception as e:
                error_msg = f"Cleanup error: {str(e)}"
                logger.error(error_msg)
                improvement_summary['errors'].append(error_msg)
            
            logger.info(f"Daily improvement cycle completed with {len(improvement_summary['errors'])} errors")
            return improvement_summary
            
        except Exception as e:
            logger.error(f"Critical error in daily improvement cycle: {str(e)}")
            return {
                'timestamp': datetime.utcnow(),
                'critical_error': str(e),
                'status': 'failed'
            }
    
    def get_learning_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive metrics about the learning system
        
        Returns:
            Learning system metrics
        """
        try:
            metrics = {}
            
            # Feature extraction metrics
            total_items = self.db.query(QuizClothingItem).count()
            items_with_auto_features = self.db.query(QuizClothingItem).filter(
                QuizClothingItem.auto_extracted_features.isnot(None)
            ).count()
            
            metrics['feature_extraction'] = {
                'total_items': total_items,
                'items_with_auto_features': items_with_auto_features,
                'extraction_coverage': items_with_auto_features / total_items if total_items > 0 else 0
            }
            
            # Feature learning data metrics
            learning_data_count = self.db.query(FeatureLearningData).count()
            validated_features = self.db.query(FeatureLearningData).filter(
                FeatureLearningData.validation_count > 0
            ).count()
            
            metrics['feature_learning'] = {
                'total_learning_entries': learning_data_count,
                'validated_features': validated_features,
                'validation_rate': validated_features / learning_data_count if learning_data_count > 0 else 0
            }
            
            # Correlation metrics
            correlation_count = self.db.query(FeatureCorrelation).count()
            strong_correlations = self.db.query(FeatureCorrelation).filter(
                FeatureCorrelation.correlation_strength > 0.7
            ).count()
            
            metrics['correlations'] = {
                'total_correlations': correlation_count,
                'strong_correlations': strong_correlations,
                'strong_correlation_rate': strong_correlations / correlation_count if correlation_count > 0 else 0
            }
            
            # User satisfaction metrics
            total_responses = self.db.query(QuizResponse).count()
            satisfied_responses = self.db.query(QuizResponse).filter(
                QuizResponse.user_satisfaction_rating >= 4
            ).count()
            
            metrics['user_satisfaction'] = {
                'total_responses': total_responses,
                'satisfied_responses': satisfied_responses,
                'satisfaction_rate': satisfied_responses / total_responses if total_responses > 0 else 0
            }
            
            # Feature source distribution
            source_distribution = self.db.query(
                FeatureLearningData.source,
                func.count(FeatureLearningData.id)
            ).group_by(FeatureLearningData.source).all()
            
            metrics['feature_sources'] = {
                source: count for source, count in source_distribution
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting learning metrics: {str(e)}")
            return {'error': str(e)}
    
    # Private helper methods
    
    async def _download_image_data(self, image_url: str) -> Optional[bytes]:
        """Download image data from URL"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        return await response.read()
            return None
        except Exception as e:
            logger.error(f"Error downloading image from {image_url}: {str(e)}")
            return None
    
    def _validate_features_from_feedback(self, feedback: StyleAssignmentFeedback):
        """Validate features based on user feedback"""
        try:
            if not feedback.feature_feedback:
                return
            
            quiz_response = feedback.quiz_response
            
            for item in quiz_response.selected_items:
                item_feedback = feedback.feature_feedback.get(str(item.id), {})
                
                for feature, is_accurate in item_feedback.items():
                    learning_data = self.db.query(FeatureLearningData).filter(
                        and_(
                            FeatureLearningData.item_id == item.id,
                            FeatureLearningData.feature_name == feature
                        )
                    ).first()
                    
                    if learning_data:
                        if is_accurate:
                            learning_data.validation_count += 1
                        else:
                            learning_data.rejection_count += 1
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error validating features from feedback: {str(e)}")
    
    def _store_feature_pattern(self, pattern: Dict[str, Any]):
        """Store discovered feature pattern as correlations"""
        try:
            features = pattern['features']
            
            # Create correlations for all feature pairs in the pattern
            for i, feature_a in enumerate(features):
                for feature_b in features[i+1:]:
                    existing_corr = self.db.query(FeatureCorrelation).filter(
                        or_(
                            and_(
                                FeatureCorrelation.feature_a == feature_a,
                                FeatureCorrelation.feature_b == feature_b
                            ),
                            and_(
                                FeatureCorrelation.feature_a == feature_b,
                                FeatureCorrelation.feature_b == feature_a
                            )
                        )
                    ).first()
                    
                    correlation_strength = pattern['confidence']
                    
                    if existing_corr:
                        # Update existing correlation
                        existing_corr.correlation_strength = max(
                            existing_corr.correlation_strength,
                            Decimal(str(correlation_strength))
                        )
                    else:
                        # Create new correlation
                        new_corr = FeatureCorrelation(
                            feature_a=feature_a,
                            feature_b=feature_b,
                            correlation_strength=Decimal(str(correlation_strength)),
                            co_occurrence_count=pattern['item_count'],
                            total_occurrences=pattern['item_count']
                        )
                        self.db.add(new_corr)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error storing feature pattern: {str(e)}")
    
    def _process_pending_validations(self) -> Dict[str, Any]:
        """Process pending feature validations"""
        try:
            # Get recent feedback that hasn't been processed
            recent_feedback = self.db.query(StyleAssignmentFeedback).filter(
                StyleAssignmentFeedback.created_at >= datetime.utcnow() - timedelta(days=1)
            ).all()
            
            processed_count = 0
            
            for feedback in recent_feedback:
                self._validate_features_from_feedback(feedback)
                processed_count += 1
            
            return {
                'processed_feedback': processed_count,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error processing pending validations: {str(e)}")
            return {'error': str(e)}
    
    def _cleanup_old_learning_data(self) -> Dict[str, Any]:
        """Clean up old learning data"""
        try:
            # Remove learning data older than 90 days with low validation ratios
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            
            old_data = self.db.query(FeatureLearningData).filter(
                and_(
                    FeatureLearningData.created_at < cutoff_date,
                    FeatureLearningData.validation_count + FeatureLearningData.rejection_count < 3
                )
            ).all()
            
            removed_count = len(old_data)
            
            for data in old_data:
                self.db.delete(data)
            
            self.db.commit()
            
            return {
                'removed_entries': removed_count,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up old learning data: {str(e)}")
            return {'error': str(e)}