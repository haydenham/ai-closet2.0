#!/usr/bin/env python3
"""
Debug script to investigate the outfit matching algorithm
"""
import asyncio
import logging
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock classes for testing
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class MockUser:
    id: str = "test-user"

@dataclass  
class MockClothingItem:
    id: str
    category: str
    color: Optional[str] = None
    brand: Optional[str] = None
    size: Optional[str] = None
    tags: Optional[List[str]] = None
    description: Optional[str] = None

@dataclass
class MockOutfitItem:
    type: str
    features: List[str]

@dataclass
class MockOutfitRecommendation:
    top: Optional[MockOutfitItem] = None
    bottom: Optional[MockOutfitItem] = None
    shoes: Optional[MockOutfitItem] = None
    outerwear: Optional[MockOutfitItem] = None
    accessories: Optional[List[MockOutfitItem]] = None

def debug_matching():
    """Debug the matching algorithm with mock data"""
    
    # Create mock closet items (simulating your blue flip flops and other items)
    mock_closet = [
        MockClothingItem(
            id="1",
            category="shoes",
            color="blue", 
            tags=["casual", "summer", "flip-flops", "blue", "comfortable"],
            description="Blue flip flops for casual summer wear"
        ),
        MockClothingItem(
            id="2", 
            category="tops",
            color="white",
            tags=["casual", "cotton", "t-shirt", "white", "comfortable"],
            description="White cotton t-shirt, casual and comfortable"
        ),
        MockClothingItem(
            id="3",
            category="bottoms", 
            color="black",
            tags=["formal", "dress-pants", "black", "business"],
            description="Black dress pants for business occasions"
        ),
        MockClothingItem(
            id="4",
            category="bottoms",
            color="blue",
            tags=["casual", "denim", "jeans", "blue", "comfortable"],
            description="Blue denim jeans, casual everyday wear"
        )
    ]
    
    # Create mock AI recommendation (example of what Gemini might generate)
    mock_ai_recommendation = MockOutfitRecommendation(
        top=MockOutfitItem(
            type="t-shirt",
            features=["casual", "cotton", "comfortable", "white", "relaxed"]
        ),
        bottom=MockOutfitItem(
            type="jeans", 
            features=["casual", "denim", "blue", "comfortable", "everyday"]
        ),
        shoes=MockOutfitItem(
            type="sneakers",
            features=["casual", "comfortable", "white", "sporty", "everyday"]
        )
    )
    
    logger.info("=== DEBUGGING OUTFIT MATCHING ===")
    logger.info(f"Mock closet has {len(mock_closet)} items:")
    for item in mock_closet:
        logger.info(f"  - {item.category}: {item.color} | tags: {item.tags}")
    
    logger.info(f"\nAI Recommendation:")
    if mock_ai_recommendation.top:
        logger.info(f"  - Top: {mock_ai_recommendation.top.type} | features: {mock_ai_recommendation.top.features}")
    if mock_ai_recommendation.bottom:
        logger.info(f"  - Bottom: {mock_ai_recommendation.bottom.type} | features: {mock_ai_recommendation.bottom.features}")
    if mock_ai_recommendation.shoes:
        logger.info(f"  - Shoes: {mock_ai_recommendation.shoes.type} | features: {mock_ai_recommendation.shoes.features}")
    
    # Simulate the matching logic
    logger.info(f"\n=== MATCHING SIMULATION ===")
    
    # Group items by category (like the real algorithm)
    items_by_category = {}
    for item in mock_closet:
        category = item.category.lower()
        if category not in items_by_category:
            items_by_category[category] = []
        items_by_category[category].append(item)
    
    logger.info(f"Items grouped by category: {list(items_by_category.keys())}")
    
    # Try to match each component
    def simulate_match(candidate_items, target_item, component_name):
        logger.info(f"\n--- Matching {component_name} ---")
        logger.info(f"Target features: {target_item.features}")
        logger.info(f"Available candidates: {len(candidate_items)}")
        
        best_match = None
        best_score = 0.0
        
        for item in candidate_items:
            # Simulate feature extraction
            item_features = set()
            
            if item.tags:
                item_features.update(tag.lower() for tag in item.tags)
            if item.color:
                item_features.add(item.color.lower())
            item_features.add(item.category.lower())
            
            target_features = set(feature.lower() for feature in target_item.features)
            
            # Calculate match
            matched_features = list(item_features.intersection(target_features))
            missing_features = list(target_features - item_features)
            
            if target_features:
                feature_score = len(matched_features) / len(target_features)
            else:
                feature_score = 0.5
            
            logger.info(f"  Item {item.id} ({item.color} {item.category}):")
            logger.info(f"    Item features: {sorted(item_features)}")
            logger.info(f"    Matched: {matched_features}")
            logger.info(f"    Missing: {missing_features}")
            logger.info(f"    Score: {feature_score:.2f}")
            
            if feature_score > best_score:
                best_score = feature_score
                best_match = item
        
        logger.info(f"  BEST MATCH: {best_match.id if best_match else 'None'} (score: {best_score:.2f})")
        return best_match, best_score
    
    # Match top
    if mock_ai_recommendation.top:
        tops_candidates = items_by_category.get('tops', [])
        simulate_match(tops_candidates, mock_ai_recommendation.top, "TOP")
    
    # Match bottom  
    if mock_ai_recommendation.bottom:
        bottoms_candidates = items_by_category.get('bottoms', [])
        simulate_match(bottoms_candidates, mock_ai_recommendation.bottom, "BOTTOM")
    
    # Match shoes
    if mock_ai_recommendation.shoes:
        shoes_candidates = items_by_category.get('shoes', [])
        simulate_match(shoes_candidates, mock_ai_recommendation.shoes, "SHOES")

if __name__ == "__main__":
    debug_matching()
