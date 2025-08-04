"""
Unit tests for ClothingItem model and related models
"""
import pytest
import uuid
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.clothing_item import ClothingItem, ClothingCategory


class TestClothingCategoryModel:
    """Test cases for ClothingCategory model"""
    
    def test_create_clothing_category(self, db_session: Session):
        """Test creating a new clothing category"""
        category = ClothingCategory(
            name="Tops",
            description="Upper body clothing items"
        )
        
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)
        
        assert category.id is not None
        assert category.name == "Tops"
        assert category.description == "Upper body clothing items"
        assert category.parent_category_id is None
    
    def test_clothing_category_hierarchical_relationship(self, db_session: Session):
        """Test hierarchical relationship between categories"""
        # Create parent category
        parent_category = ClothingCategory(
            name="Clothing",
            description="All clothing items"
        )
        
        db_session.add(parent_category)
        db_session.commit()
        db_session.refresh(parent_category)
        
        # Create child category
        child_category = ClothingCategory(
            name="Tops",
            description="Upper body clothing",
            parent_category_id=parent_category.id
        )
        
        db_session.add(child_category)
        db_session.commit()
        db_session.refresh(child_category)
        
        # Test relationships
        assert child_category.parent_category.id == parent_category.id
        assert child_category.parent_category.name == "Clothing"
        assert len(parent_category.subcategories) == 1
        assert parent_category.subcategories[0].id == child_category.id
    
    def test_clothing_category_unique_name_constraint(self, db_session: Session):
        """Test that category name must be unique"""
        category1 = ClothingCategory(name="Tops", description="First tops category")
        category2 = ClothingCategory(name="Tops", description="Second tops category")
        
        db_session.add(category1)
        db_session.commit()
        
        db_session.add(category2)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_clothing_category_repr(self, db_session: Session):
        """Test clothing category string representation"""
        category = ClothingCategory(name="Tops", description="Upper body clothing")
        
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)
        
        expected_repr = f"<ClothingCategory(id={category.id}, name=Tops)>"
        assert repr(category) == expected_repr


class TestClothingItemModel:
    """Test cases for ClothingItem model"""
    
    def test_create_clothing_item(self, db_session: Session):
        """Test creating a new clothing item"""
        # Create a user first
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create clothing item
        clothing_item = ClothingItem(
            user_id=user.id,
            filename="shirt_001.jpg",
            original_filename="blue_shirt.jpg",
            image_url="https://storage.example.com/shirt_001.jpg",
            category="shirt",
            color="blue",
            brand="Nike",
            size="M",
            tags=["casual", "cotton"],
            description="Comfortable blue cotton shirt",
            embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
            image_width=800,
            image_height=600,
            file_size=1024000
        )
        
        db_session.add(clothing_item)
        db_session.commit()
        db_session.refresh(clothing_item)
        
        assert clothing_item.id is not None
        assert clothing_item.user_id == user.id
        assert clothing_item.filename == "shirt_001.jpg"
        assert clothing_item.original_filename == "blue_shirt.jpg"
        assert clothing_item.image_url == "https://storage.example.com/shirt_001.jpg"
        assert clothing_item.category == "shirt"
        assert clothing_item.color == "blue"
        assert clothing_item.brand == "Nike"
        assert clothing_item.size == "M"
        assert clothing_item.tags == ["casual", "cotton"]
        assert clothing_item.description == "Comfortable blue cotton shirt"
        assert clothing_item.embedding == [0.1, 0.2, 0.3, 0.4, 0.5]
        assert clothing_item.image_width == 800
        assert clothing_item.image_height == 600
        assert clothing_item.file_size == 1024000
        assert clothing_item.times_recommended == 0
        assert clothing_item.last_recommended is None
        assert clothing_item.upload_date is not None
        assert clothing_item.updated_at is not None
    
    def test_clothing_item_user_relationship(self, db_session: Session):
        """Test clothing item relationship with user"""
        # Create a user first
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create clothing item
        clothing_item = ClothingItem(
            user_id=user.id,
            filename="shirt_001.jpg",
            original_filename="blue_shirt.jpg",
            image_url="https://storage.example.com/shirt_001.jpg",
            category="shirt"
        )
        
        db_session.add(clothing_item)
        db_session.commit()
        db_session.refresh(clothing_item)
        
        # Test relationships
        assert clothing_item.user.id == user.id
        assert clothing_item.user.email == "test@example.com"
        assert len(user.clothing_items) == 1
        assert user.clothing_items[0].id == clothing_item.id
    
    def test_clothing_item_category_relationship(self, db_session: Session):
        """Test clothing item relationship with category"""
        # Create a user first
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create category
        category = ClothingCategory(name="Shirts", description="Shirt items")
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)
        
        # Create clothing item
        clothing_item = ClothingItem(
            user_id=user.id,
            filename="shirt_001.jpg",
            original_filename="blue_shirt.jpg",
            image_url="https://storage.example.com/shirt_001.jpg",
            category="shirt",
            category_id=category.id
        )
        
        db_session.add(clothing_item)
        db_session.commit()
        db_session.refresh(clothing_item)
        
        # Test relationships
        assert clothing_item.category_obj.id == category.id
        assert clothing_item.category_obj.name == "Shirts"
        assert len(category.clothing_items) == 1
        assert category.clothing_items[0].id == clothing_item.id
    
    def test_has_tag(self, db_session: Session):
        """Test checking if item has specific tag"""
        # Create a user first
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create clothing item
        clothing_item = ClothingItem(
            user_id=user.id,
            filename="shirt_001.jpg",
            original_filename="blue_shirt.jpg",
            image_url="https://storage.example.com/shirt_001.jpg",
            category="shirt",
            tags=["casual", "cotton"]
        )
        
        db_session.add(clothing_item)
        db_session.commit()
        
        # Test tag checking
        assert clothing_item.has_tag("casual") is True
        assert clothing_item.has_tag("cotton") is True
        assert clothing_item.has_tag("formal") is False
    
    def test_add_tag(self, db_session: Session):
        """Test adding tag to item"""
        # Create a user first
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create clothing item
        clothing_item = ClothingItem(
            user_id=user.id,
            filename="shirt_001.jpg",
            original_filename="blue_shirt.jpg",
            image_url="https://storage.example.com/shirt_001.jpg",
            category="shirt",
            tags=["casual"]
        )
        
        db_session.add(clothing_item)
        db_session.commit()
        
        # Add tag
        clothing_item.add_tag("cotton")
        assert clothing_item.has_tag("cotton") is True
        assert len(clothing_item.tags) == 2
        
        # Adding duplicate should not increase count
        clothing_item.add_tag("casual")
        assert len(clothing_item.tags) == 2
    
    def test_remove_tag(self, db_session: Session):
        """Test removing tag from item"""
        # Create a user first
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create clothing item
        clothing_item = ClothingItem(
            user_id=user.id,
            filename="shirt_001.jpg",
            original_filename="blue_shirt.jpg",
            image_url="https://storage.example.com/shirt_001.jpg",
            category="shirt",
            tags=["casual", "cotton"]
        )
        
        db_session.add(clothing_item)
        db_session.commit()
        
        # Remove tag
        clothing_item.remove_tag("cotton")
        assert clothing_item.has_tag("cotton") is False
        assert len(clothing_item.tags) == 1
        
        # Removing non-existent tag should not error
        clothing_item.remove_tag("formal")
        assert len(clothing_item.tags) == 1
    
    def test_increment_recommendation_count(self, db_session: Session):
        """Test incrementing recommendation count"""
        # Create a user first
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create clothing item
        clothing_item = ClothingItem(
            user_id=user.id,
            filename="shirt_001.jpg",
            original_filename="blue_shirt.jpg",
            image_url="https://storage.example.com/shirt_001.jpg",
            category="shirt"
        )
        
        db_session.add(clothing_item)
        db_session.commit()
        
        # Test initial state
        assert clothing_item.times_recommended == 0
        assert clothing_item.last_recommended is None
        
        # Increment count
        clothing_item.increment_recommendation_count()
        assert clothing_item.times_recommended == 1
        assert clothing_item.last_recommended is not None
        
        # Increment again
        first_recommendation_time = clothing_item.last_recommended
        clothing_item.increment_recommendation_count()
        assert clothing_item.times_recommended == 2
        assert clothing_item.last_recommended > first_recommendation_time
    
    def test_file_extension_property(self, db_session: Session):
        """Test file extension property"""
        # Create a user first
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create clothing item
        clothing_item = ClothingItem(
            user_id=user.id,
            filename="shirt_001.jpg",
            original_filename="blue_shirt.jpg",
            image_url="https://storage.example.com/shirt_001.jpg",
            category="shirt"
        )
        
        assert clothing_item.file_extension == "jpg"
        
        # Test with different extension
        clothing_item.filename = "shirt_002.PNG"
        assert clothing_item.file_extension == "png"
        
        # Test with no extension
        clothing_item.filename = "shirt_003"
        assert clothing_item.file_extension == ""
    
    def test_is_image_property(self, db_session: Session):
        """Test is_image property"""
        # Create a user first
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create clothing item
        clothing_item = ClothingItem(
            user_id=user.id,
            filename="shirt_001.jpg",
            original_filename="blue_shirt.jpg",
            image_url="https://storage.example.com/shirt_001.jpg",
            category="shirt"
        )
        
        assert clothing_item.is_image is True
        
        # Test with different image extensions
        for ext in ['jpeg', 'png', 'gif', 'webp', 'bmp']:
            clothing_item.filename = f"shirt_001.{ext}"
            assert clothing_item.is_image is True
        
        # Test with non-image extension
        clothing_item.filename = "document.pdf"
        assert clothing_item.is_image is False
    
    def test_clothing_item_repr(self, db_session: Session):
        """Test clothing item string representation"""
        # Create a user first
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create clothing item
        clothing_item = ClothingItem(
            user_id=user.id,
            filename="shirt_001.jpg",
            original_filename="blue_shirt.jpg",
            image_url="https://storage.example.com/shirt_001.jpg",
            category="shirt"
        )
        
        db_session.add(clothing_item)
        db_session.commit()
        db_session.refresh(clothing_item)
        
        expected_repr = f"<ClothingItem(id={clothing_item.id}, category=shirt, user_id={user.id})>"
        assert repr(clothing_item) == expected_repr