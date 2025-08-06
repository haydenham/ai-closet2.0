# Visual Style Quiz System Design

## Overview

A scalable, data-driven visual quiz system that determines user style categories through clothing item selection and feature matching algorithms.

## Quiz Flow

### 1. Gender Selection
- **Question 1**: User selects Male or Female
- **Result**: Determines which clothing database to use for subsequent questions

### 2. Clothing Item Selection (Questions 2-6)
- **Question 2**: Pick a top
- **Question 3**: Pick a bottom  
- **Question 4**: Pick shoes
- **Question 5**: Pick layering piece
- **Question 6**: Pick an accessory

### 3. Complete Outfit Selection
- **Question 7**: Pick a complete outfit from curated options

## Data Structure

### Clothing Items (Key-Value System)
Each clothing item is structured as:
```json
{
  "item_id": "mens_white_tshirt_001",
  "name": "Classic White T-Shirt",
  "image_url": "/images/quiz/mens/tops/white_tshirt_001.jpg",
  "gender": "male",
  "category": "top",
  "features": [
    "t-shirt",
    "cotton",
    "white",
    "neutral",
    "casual",
    "basic",
    "fitted",
    "minimalist"
  ]
}
```

### Style Categories

#### Men's Categories (8)
1. **Minimalist / Clean-Cut**
   - Features: `["clean", "minimal", "neutral", "simple", "fitted", "monochrome"]`

2. **Classic Tailored**
   - Features: `["tailored", "business", "formal", "structured", "classic", "professional"]`

3. **Streetwear**
   - Features: `["graphic", "oversized", "sneakers", "urban", "bold", "casual", "baggy"]`

4. **Workwear / Heritage**
   - Features: `["denim", "rugged", "heritage", "workwear", "boots", "utilitarian", "sturdy"]`

5. **Techwear / Utility**
   - Features: `["technical", "performance", "muted", "functional", "modern", "utility"]`

6. **Preppy / Ivy**
   - Features: `["preppy", "collegiate", "polo", "chino", "loafers", "traditional", "refined"]`

7. **Athleisure / Sport Casual**
   - Features: `["athletic", "sporty", "comfortable", "activewear", "casual", "performance"]`

8. **Retro / Vintage**
   - Features: `["vintage", "retro", "70s", "80s", "90s", "nostalgic", "throwback"]`

#### Women's Categories (8)
1. **Minimalist / Modern Chic**
   - Features: `["minimal", "modern", "clean", "sophisticated", "neutral", "sleek"]`

2. **Classic Elegance**
   - Features: `["elegant", "timeless", "tailored", "refined", "classic", "polished"]`

3. **Streetwear**
   - Features: `["oversized", "graphic", "sneakers", "urban", "bold", "edgy", "casual"]`

4. **Bohemian / Indie**
   - Features: `["boho", "flowy", "prints", "crochet", "indie", "artistic", "free-spirited"]`

5. **Romantic / Feminine**
   - Features: `["romantic", "feminine", "pastels", "ruffles", "soft", "delicate", "pretty"]`

6. **Athleisure / Sport Casual**
   - Features: `["athletic", "sporty", "comfortable", "activewear", "casual", "performance"]`

7. **Trend-Driven / Y2K**
   - Features: `["trendy", "y2k", "micro", "baby-tee", "mesh", "bold", "statement"]`

8. **Vintage Revival**
   - Features: `["vintage", "thrift", "70s", "90s", "corsets", "mom-jeans", "retro"]`

## Matching Algorithm

### Feature Scoring System
```python
def calculate_style_scores(selected_items, style_categories):
    scores = {}
    
    for category_name, category_features in style_categories.items():
        score = 0
        total_features = 0
        
        for item in selected_items:
            for feature in item['features']:
                total_features += 1
                if feature in category_features:
                    score += 1
        
        # Calculate percentage match
        scores[category_name] = (score / total_features) * 100 if total_features > 0 else 0
    
    return scores
```

### Weighted Scoring (Advanced)
- **Complete Outfit**: 40% weight (most indicative)
- **Top + Bottom**: 30% weight (core outfit)
- **Shoes**: 15% weight
- **Layering**: 10% weight
- **Accessories**: 5% weight

## Database Schema

### Tables

#### `quiz_clothing_items`
```sql
CREATE TABLE quiz_clothing_items (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    image_url VARCHAR(500) NOT NULL,
    gender VARCHAR(10) NOT NULL CHECK (gender IN ('male', 'female')),
    category VARCHAR(50) NOT NULL,
    features JSONB NOT NULL,
    auto_extracted_features JSONB, -- Features from computer vision
    feature_confidence_scores JSONB, -- Confidence in each feature
    selection_count INTEGER DEFAULT 0, -- How often this item is selected
    satisfaction_score DECIMAL(3,2), -- Average user satisfaction when selected
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### `style_categories`
```sql
CREATE TABLE style_categories (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    gender VARCHAR(10) NOT NULL CHECK (gender IN ('male', 'female')),
    features JSONB NOT NULL,
    ai_theme_prompt TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### `quiz_responses`
```sql
CREATE TABLE quiz_responses (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    selected_items JSONB NOT NULL,
    calculated_scores JSONB NOT NULL,
    assigned_category VARCHAR(100) NOT NULL,
    confidence_score DECIMAL(3,2), -- Algorithm confidence in assignment
    user_satisfaction_rating INTEGER, -- User feedback 1-5
    user_feedback_text TEXT, -- Optional user comments
    completed_at TIMESTAMP DEFAULT NOW()
);
```

#### `feature_learning_data`
```sql
CREATE TABLE feature_learning_data (
    id UUID PRIMARY KEY,
    feature_name VARCHAR(100) NOT NULL,
    item_id UUID REFERENCES quiz_clothing_items(id),
    source VARCHAR(50) NOT NULL, -- 'manual', 'cv_auto', 'user_suggested', 'algorithm_discovered'
    confidence_score DECIMAL(3,2),
    validation_count INTEGER DEFAULT 0, -- How many times this feature was validated
    rejection_count INTEGER DEFAULT 0, -- How many times this feature was rejected
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### `feature_correlations`
```sql
CREATE TABLE feature_correlations (
    id UUID PRIMARY KEY,
    feature_a VARCHAR(100) NOT NULL,
    feature_b VARCHAR(100) NOT NULL,
    correlation_strength DECIMAL(3,2), -- -1 to 1, how often they appear together
    co_occurrence_count INTEGER DEFAULT 0,
    total_occurrences INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## Scalability Features

### 1. Smart Feature Learning System
- **User Satisfaction Tracking**: Monitor which feature combinations lead to high user satisfaction scores
- **Automatic Feature Discovery**: Use clustering algorithms to identify new features from user selection patterns
- **Computer Vision Auto-Tagging**: Implement CV models to automatically extract features from clothing images
- **Feature Correlation Analysis**: Track which features commonly appear together and suggest new combinations
- **Behavioral Feature Mining**: Analyze user behavior post-quiz to identify missing or inaccurate features

### 2. Dynamic Category Management
- Add new categories without code changes
- Update feature mappings through admin interface
- A/B test different category definitions

### 3. Feature Expansion & Intelligence
- Add new features to existing items based on learning algorithms
- Create feature hierarchies (e.g., "casual" → "very-casual", "semi-casual")
- Implement feature synonyms and aliases
- Auto-suggest features for new clothing items based on visual similarity

### 4. Algorithm Improvements
- Machine learning-based feature weighting based on user outcomes
- User feedback integration to improve matching accuracy
- Seasonal category adjustments
- Predictive feature importance scoring

### 4. Content Management
- Admin interface for adding new clothing items
- Bulk import/export capabilities
- Image optimization and CDN integration

## Suggested Improvements

### 1. Enhanced Feature System
```json
{
  "features": {
    "primary": ["t-shirt", "cotton", "white"],
    "style": ["minimalist", "casual", "basic"],
    "fit": ["fitted", "regular"],
    "occasion": ["everyday", "casual"],
    "season": ["all-season"]
  }
}
```

### 2. Confidence Scoring
- Return confidence percentage with style assignment
- Handle edge cases where no clear category emerges
- Suggest hybrid styles (e.g., "Minimalist with Streetwear influences")

### 3. Progressive Enhancement
- Start with 8 categories, expand based on user data
- Track which items are most/least selected
- Identify gaps in current category coverage

### 4. User Feedback Loop
- "How accurate was this style assessment?" after quiz
- Allow users to manually adjust their assigned style
- Use feedback to improve algorithm weights

### 5. Advanced Matching
- Consider color harmony in selections
- Factor in price point preferences
- Account for seasonal preferences

## Implementation Priority

### Phase 1: Core System
1. Basic database schema and clothing item management
2. Simple feature matching algorithm
3. 8 starter categories per gender

### Phase 2: Enhancement
1. Weighted scoring system
2. Admin interface for content management
3. User feedback collection

### Phase 3: Smart Feature Learning
1. Computer vision integration for auto-feature extraction
2. Machine learning-based feature discovery and validation
3. User behavior analysis for feature correlation mining
4. Dynamic category suggestions based on learned patterns
5. Personalization based on user behavior and satisfaction feedback

## API Endpoints

### Quiz Management
- `GET /api/quiz/clothing-items/{gender}/{category}` - Get clothing options
- `POST /api/quiz/submit` - Submit quiz responses
- `POST /api/quiz/feedback` - Submit user satisfaction feedback
- `GET /api/quiz/categories` - Get available style categories

### Smart Feature Learning
- `POST /api/features/auto-extract` - Trigger CV feature extraction for new items
- `GET /api/features/suggestions/{item_id}` - Get AI-suggested features for item
- `POST /api/features/validate` - User/admin validation of suggested features
- `GET /api/features/correlations` - Get feature correlation data
- `POST /api/features/user-suggest` - User-suggested features for items

### Admin Management
- `POST /api/admin/clothing-items` - Add new clothing item
- `PUT /api/admin/categories/{id}` - Update category features
- `GET /api/admin/analytics` - Quiz completion analytics
- `GET /api/admin/feature-insights` - Feature learning insights and recommendations
- `POST /api/admin/feature-approval` - Approve/reject auto-discovered features

## Smart Feature Learning System (Detailed)

### 1. Computer Vision Auto-Tagging
```python
class CVFeatureExtractor:
    def extract_features(self, image_url):
        """Extract visual features from clothing images"""
        features = {
            'colors': self.extract_dominant_colors(image_url),
            'patterns': self.detect_patterns(image_url),  # stripes, polka dots, etc.
            'textures': self.analyze_texture(image_url),  # smooth, rough, knit, etc.
            'fit': self.analyze_fit(image_url),          # fitted, loose, oversized
            'style_elements': self.detect_style_elements(image_url)  # buttons, zippers, etc.
        }
        return features
```

### 2. User Satisfaction Tracking
```python
def track_satisfaction_correlation(user_id, quiz_response, satisfaction_rating):
    """Track which feature combinations lead to user satisfaction"""
    selected_features = extract_all_features(quiz_response.selected_items)
    
    # Update feature satisfaction scores
    for feature in selected_features:
        update_feature_satisfaction(feature, satisfaction_rating)
    
    # Track feature combinations that work well together
    for combo in get_feature_combinations(selected_features):
        update_combination_satisfaction(combo, satisfaction_rating)
```

### 3. Automatic Feature Discovery
```python
def discover_new_features():
    """Use clustering to find new feature patterns"""
    # Get all user selections and their satisfaction scores
    high_satisfaction_selections = get_selections_with_high_satisfaction()
    
    # Cluster similar selections to find common patterns
    clusters = cluster_selections(high_satisfaction_selections)
    
    # Analyze clusters to suggest new features
    for cluster in clusters:
        common_elements = find_common_visual_elements(cluster)
        suggested_features = generate_feature_suggestions(common_elements)
        
        # Queue for admin review
        queue_for_feature_review(suggested_features)
```

### 4. Feature Validation Pipeline
```python
class FeatureValidationPipeline:
    def validate_suggested_feature(self, feature_name, item_id):
        """Multi-stage validation for new features"""
        
        # Stage 1: Computer Vision Confidence
        cv_confidence = self.cv_validator.validate_feature(feature_name, item_id)
        
        # Stage 2: User Validation (A/B test)
        user_validation = self.run_user_validation_test(feature_name, item_id)
        
        # Stage 3: Expert Review
        expert_review = self.queue_for_expert_review(feature_name, item_id)
        
        # Combine scores for final decision
        final_score = self.combine_validation_scores(
            cv_confidence, user_validation, expert_review
        )
        
        return final_score > VALIDATION_THRESHOLD
```

### 5. Feature Correlation Mining
```python
def mine_feature_correlations():
    """Find features that commonly appear together"""
    all_items = get_all_clothing_items()
    
    for item_a in all_items:
        for item_b in all_items:
            if item_a.id != item_b.id:
                common_features = set(item_a.features) & set(item_b.features)
                
                # Update correlation matrix
                for feature_combo in combinations(common_features, 2):
                    update_correlation_strength(feature_combo[0], feature_combo[1])
    
    # Suggest new feature combinations based on strong correlations
    suggest_feature_combinations()
```

### 6. Behavioral Feature Mining
```python
def analyze_post_quiz_behavior(user_id, assigned_style):
    """Analyze user behavior after quiz to validate style assignment"""
    
    # Track what users actually upload to their closet
    uploaded_items = get_user_uploaded_items(user_id, days=30)
    
    # Extract features from uploaded items
    uploaded_features = extract_features_from_uploads(uploaded_items)
    
    # Compare with assigned style features
    style_features = get_style_category_features(assigned_style)
    
    # Calculate alignment score
    alignment = calculate_feature_alignment(uploaded_features, style_features)
    
    if alignment < ALIGNMENT_THRESHOLD:
        # User's actual style differs from quiz result
        suggest_style_reassignment(user_id, uploaded_features)
        
        # Learn from this mismatch
        update_quiz_algorithm_weights(quiz_features, uploaded_features, alignment)
```

### 7. Continuous Learning Loop
```python
class ContinuousLearningSystem:
    def daily_learning_cycle(self):
        """Run daily to improve the system"""
        
        # 1. Process new user feedback
        self.process_user_feedback()
        
        # 2. Run CV feature extraction on new items
        self.extract_features_from_new_items()
        
        # 3. Update feature correlations
        self.update_feature_correlations()
        
        # 4. Discover new feature patterns
        self.discover_new_features()
        
        # 5. Validate pending features
        self.validate_pending_features()
        
        # 6. Update algorithm weights
        self.update_algorithm_weights()
        
        # 7. Generate insights report
        self.generate_insights_report()
```

### Data Quality Metrics
- **Feature Accuracy**: % of auto-extracted features validated by users
- **Satisfaction Correlation**: How well feature combinations predict user satisfaction
- **Discovery Rate**: Number of new valid features discovered per week
- **Validation Efficiency**: Time from feature suggestion to validation
- **Algorithm Improvement**: Improvement in style assignment accuracy over time

This system creates a self-improving, data-rich environment where the more users interact with the quiz, the better and more detailed it becomes!