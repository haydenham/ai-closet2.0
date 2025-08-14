"""
Integration tests for user management API endpoints
"""
import pytest
import uuid
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.style_profile import StyleProfile
from app.models.clothing_item import ClothingItem
from app.models.outfit_recommendation import OutfitRecommendation
from app.services.auth_service import auth_service


class TestUserProfileEndpoints:
    """Test user profile CRUD operations"""
    
    async def test_get_user_profile_success(
        self, 
        async_client: AsyncClient, 
        test_user: User,
        auth_headers: dict
    ):
        """Test successful user profile retrieval"""
        response = await async_client.get("/users/profile", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == str(test_user.id)
        assert data["email"] == test_user.email
        assert data["first_name"] == test_user.first_name
        assert data["last_name"] == test_user.last_name
        assert data["is_verified"] == test_user.is_verified
        assert data["is_active"] == test_user.is_active
        assert "created_at" in data
        assert "updated_at" in data
    
    async def test_get_user_profile_unauthorized(self, async_client: AsyncClient):
        """Test user profile retrieval without authentication"""
        response = await async_client.get("/users/profile")
        
        assert response.status_code == 403
        assert "detail" in response.json()
    
    async def test_update_user_profile_success(
        self, 
        async_client: AsyncClient, 
        test_user: User,
        auth_headers: dict,
        async_session: AsyncSession
    ):
        """Test successful user profile update"""
        update_data = {
            "first_name": "UpdatedFirst",
            "last_name": "UpdatedLast"
        }
        
        response = await async_client.put(
            "/users/profile", 
            json=update_data, 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["first_name"] == "UpdatedFirst"
        assert data["last_name"] == "UpdatedLast"
        assert data["email"] == test_user.email  # Should remain unchanged
        
        # Verify database update
        await async_session.refresh(test_user)
        assert test_user.first_name == "UpdatedFirst"
        assert test_user.last_name == "UpdatedLast"
    
    async def test_update_user_profile_email_change(
        self, 
        async_client: AsyncClient, 
        test_user: User,
        auth_headers: dict,
        async_session: AsyncSession
    ):
        """Test user profile update with email change"""
        new_email = "newemail@example.com"
        update_data = {"email": new_email}
        
        response = await async_client.put(
            "/users/profile", 
            json=update_data, 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["email"] == new_email
        assert data["is_verified"] == False  # Should be marked as unverified
        
        # Verify database update
        await async_session.refresh(test_user)
        assert test_user.email == new_email
        assert test_user.is_verified == False
    
    async def test_update_user_profile_duplicate_email(
        self, 
        async_client: AsyncClient, 
        test_user: User,
        auth_headers: dict,
        async_session: AsyncSession
    ):
        """Test user profile update with duplicate email"""
        # Create another user
        other_user = User(
            email="other@example.com",
            password_hash="hashed_password",
            first_name="Other",
            last_name="User",
            is_verified=True
        )
        async_session.add(other_user)
        await async_session.commit()
        
        # Try to update to existing email
        update_data = {"email": "other@example.com"}
        
        response = await async_client.put(
            "/users/profile", 
            json=update_data, 
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "Email address already exists" in response.json()["detail"]
    
    async def test_update_user_profile_partial_update(
        self, 
        async_client: AsyncClient, 
        test_user: User,
        auth_headers: dict,
        async_session: AsyncSession
    ):
        """Test partial user profile update"""
        original_last_name = test_user.last_name
        update_data = {"first_name": "OnlyFirst"}
        
        response = await async_client.put(
            "/users/profile", 
            json=update_data, 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["first_name"] == "OnlyFirst"
        assert data["last_name"] == original_last_name  # Should remain unchanged
    
    async def test_update_user_profile_unauthorized(self, async_client: AsyncClient):
        """Test user profile update without authentication"""
        update_data = {"first_name": "Unauthorized"}
        
        response = await async_client.put("/users/profile", json=update_data)
        
        assert response.status_code == 403
    
    async def test_delete_user_account_success(
        self, 
        async_client: AsyncClient, 
        test_user: User,
        auth_headers: dict,
        async_session: AsyncSession
    ):
        """Test successful user account deletion"""
        response = await async_client.delete("/users/profile", headers=auth_headers)
        
        assert response.status_code == 200
        assert "successfully deleted" in response.json()["message"]
        
        # Verify user is marked as inactive
        await async_session.refresh(test_user)
        assert test_user.is_active == False
    
    async def test_delete_user_account_unauthorized(self, async_client: AsyncClient):
        """Test user account deletion without authentication"""
        response = await async_client.delete("/users/profile")
        
        assert response.status_code == 403


class TestUserPreferencesEndpoints:
    """Test user preferences management"""
    
    async def test_get_user_preferences_success(
        self, 
        async_client: AsyncClient, 
        test_user_with_style_profile: tuple
    ):
        """Test successful user preferences retrieval"""
        from tests.conftest import create_auth_headers
        
        test_user, style_profile = test_user_with_style_profile
        auth_headers = await create_auth_headers(test_user)
        
        response = await async_client.get("/users/preferences", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == str(style_profile.id)
        assert data["user_id"] == str(test_user.id)
        assert data["assigned_model"] == style_profile.assigned_model
        assert data["style_preferences"] == style_profile.style_preferences
        assert data["fashion_goals"] == style_profile.fashion_goals
        assert data["preferred_colors"] == style_profile.preferred_colors
    
    async def test_get_user_preferences_no_profile(
        self, 
        async_client: AsyncClient, 
        test_user: User,
        auth_headers: dict
    ):
        """Test user preferences retrieval without style profile"""
        response = await async_client.get("/users/preferences", headers=auth_headers)
        
        assert response.status_code == 404
        assert "no style profile" in response.json()["detail"]
    
    async def test_update_user_preferences_success(
        self, 
        async_client: AsyncClient, 
        test_user_with_style_profile: tuple,
        async_session: AsyncSession
    ):
        """Test successful user preferences update"""
        from tests.conftest import create_auth_headers
        
        test_user, style_profile = test_user_with_style_profile
        auth_headers = await create_auth_headers(test_user)
        
        update_data = {
            "style_preferences": ["casual", "modern"],
            "fashion_goals": ["comfort", "versatility"],
            "preferred_colors": ["blue", "black", "white"],
            "body_type": "athletic",
            "lifestyle": "active",
            "budget_range": "mid-range"
        }
        
        response = await async_client.put(
            "/users/preferences", 
            json=update_data, 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["style_preferences"] == ["casual", "modern"]
        assert data["fashion_goals"] == ["comfort", "versatility"]
        assert data["preferred_colors"] == ["blue", "black", "white"]
        assert data["body_type"] == "athletic"
        assert data["lifestyle"] == "active"
        assert data["budget_range"] == "mid-range"
        
        # Verify database update
        await async_session.refresh(style_profile)
        assert style_profile.style_preferences == ["casual", "modern"]
        assert style_profile.fashion_goals == ["comfort", "versatility"]
    
    async def test_update_user_preferences_partial(
        self, 
        async_client: AsyncClient, 
        test_user_with_style_profile: tuple,
        async_session: AsyncSession
    ):
        """Test partial user preferences update"""
        from tests.conftest import create_auth_headers
        
        test_user, style_profile = test_user_with_style_profile
        auth_headers = await create_auth_headers(test_user)
        original_goals = style_profile.fashion_goals
        
        update_data = {"style_preferences": ["minimalist"]}
        
        response = await async_client.put(
            "/users/preferences", 
            json=update_data, 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["style_preferences"] == ["minimalist"]
        assert data["fashion_goals"] == original_goals  # Should remain unchanged
    
    async def test_update_user_preferences_no_profile(
        self, 
        async_client: AsyncClient, 
        test_user: User,
        auth_headers: dict
    ):
        """Test user preferences update without style profile"""
        update_data = {"style_preferences": ["casual"]}
        
        response = await async_client.put(
            "/users/preferences", 
            json=update_data, 
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "no style profile" in response.json()["detail"]
    
    async def test_update_user_preferences_unauthorized(self, async_client: AsyncClient):
        """Test user preferences update without authentication"""
        update_data = {"style_preferences": ["casual"]}
        
        response = await async_client.put("/users/preferences", json=update_data)
        
        assert response.status_code == 403


class TestUserStatisticsEndpoints:
    """Test user statistics and activity tracking"""
    
    async def test_get_user_statistics_success(
        self, 
        async_client: AsyncClient, 
        test_user_with_data: tuple
    ):
        """Test successful user statistics retrieval"""
        from tests.conftest import create_auth_headers
        
        test_user, clothing_items, recommendations = test_user_with_data
        auth_headers = await create_auth_headers(test_user)
        
        response = await async_client.get("/users/statistics", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "period_days" in data
        assert "account_created" in data
        assert "closet" in data
        assert "recommendations" in data
        assert "engagement" in data
        
        # Check closet statistics
        closet_data = data["closet"]
        assert closet_data["total_items"] == len(clothing_items)
        assert "recent_items" in closet_data
        assert "items_by_category" in closet_data
        
        # Check recommendations statistics
        rec_data = data["recommendations"]
        assert rec_data["total_recommendations"] == len(recommendations)
        assert "recent_recommendations" in rec_data
        assert "average_rating" in rec_data
        assert "feedback_count" in rec_data
        
        # Check engagement data
        engagement_data = data["engagement"]
        assert "most_recommended_items" in engagement_data
        assert "recent_activity" in engagement_data
    
    async def test_get_user_statistics_custom_period(
        self, 
        async_client: AsyncClient, 
        test_user_with_data: tuple
    ):
        """Test user statistics with custom time period"""
        from tests.conftest import create_auth_headers
        
        test_user, clothing_items, recommendations = test_user_with_data
        auth_headers = await create_auth_headers(test_user)
        
        response = await async_client.get(
            "/users/statistics?days=7", 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["period_days"] == 7
    
    async def test_get_user_statistics_invalid_period(
        self, 
        async_client: AsyncClient, 
        test_user: User,
        auth_headers: dict
    ):
        """Test user statistics with invalid time period"""
        response = await async_client.get(
            "/users/statistics?days=400", 
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    async def test_get_user_statistics_empty_data(
        self, 
        async_client: AsyncClient, 
        test_user: User,
        auth_headers: dict
    ):
        """Test user statistics with no data"""
        response = await async_client.get("/users/statistics", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return zero values for empty data
        assert data["closet"]["total_items"] == 0
        assert data["recommendations"]["total_recommendations"] == 0
        assert data["recommendations"]["average_rating"] == 0.0
    
    async def test_get_user_statistics_unauthorized(self, async_client: AsyncClient):
        """Test user statistics retrieval without authentication"""
        response = await async_client.get("/users/statistics")
        
        assert response.status_code == 403
    
    async def test_get_user_activity_success(
        self, 
        async_client: AsyncClient, 
        test_user_with_data: tuple
    ):
        """Test successful user activity retrieval"""
        from tests.conftest import create_auth_headers
        
        test_user, clothing_items, recommendations = test_user_with_data
        auth_headers = await create_auth_headers(test_user)
        
        response = await async_client.get("/users/activity", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "items" in data
        assert "pagination" in data
        
        # Check pagination info
        pagination = data["pagination"]
        assert "total" in pagination
        assert "limit" in pagination
        assert "offset" in pagination
        assert "has_more" in pagination
        
        # Check activity items
        items = data["items"]
        assert len(items) <= 50  # Default limit
        
        if items:
            item = items[0]
            assert "id" in item
            assert "type" in item
            assert "prompt" in item
            assert "created_at" in item
    
    async def test_get_user_activity_pagination(
        self, 
        async_client: AsyncClient, 
        test_user_with_data: tuple
    ):
        """Test user activity with pagination"""
        from tests.conftest import create_auth_headers
        
        test_user, clothing_items, recommendations = test_user_with_data
        auth_headers = await create_auth_headers(test_user)
        
        response = await async_client.get(
            "/users/activity?limit=5&offset=0", 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["pagination"]["limit"] == 5
        assert data["pagination"]["offset"] == 0
        assert len(data["items"]) <= 5
    
    async def test_get_user_activity_invalid_pagination(
        self, 
        async_client: AsyncClient, 
        test_user: User,
        auth_headers: dict
    ):
        """Test user activity with invalid pagination parameters"""
        response = await async_client.get(
            "/users/activity?limit=200", 
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    async def test_get_user_activity_unauthorized(self, async_client: AsyncClient):
        """Test user activity retrieval without authentication"""
        response = await async_client.get("/users/activity")
        
        assert response.status_code == 403


class TestUserManagementIntegration:
    """Test integration scenarios for user management"""
    
    async def test_complete_user_profile_workflow(
        self, 
        async_client: AsyncClient, 
        test_user: User,
        auth_headers: dict,
        async_session: AsyncSession
    ):
        """Test complete user profile management workflow"""
        # 1. Get initial profile
        response = await async_client.get("/users/profile", headers=auth_headers)
        assert response.status_code == 200
        initial_data = response.json()
        
        # 2. Update profile
        update_data = {
            "first_name": "Updated",
            "last_name": "Name"
        }
        response = await async_client.put(
            "/users/profile", 
            json=update_data, 
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # 3. Verify update
        response = await async_client.get("/users/profile", headers=auth_headers)
        assert response.status_code == 200
        updated_data = response.json()
        
        assert updated_data["first_name"] == "Updated"
        assert updated_data["last_name"] == "Name"
        assert updated_data["email"] == initial_data["email"]
    
    async def test_user_preferences_workflow(
        self, 
        async_client: AsyncClient, 
        test_user_with_style_profile: tuple
    ):
        """Test complete user preferences workflow"""
        from tests.conftest import create_auth_headers
        
        test_user, style_profile = test_user_with_style_profile
        auth_headers = await create_auth_headers(test_user)
        
        # 1. Get initial preferences
        response = await async_client.get("/users/preferences", headers=auth_headers)
        assert response.status_code == 200
        initial_prefs = response.json()
        
        # 2. Update preferences
        new_prefs = {
            "style_preferences": ["modern", "casual"],
            "preferred_colors": ["navy", "white"]
        }
        response = await async_client.put(
            "/users/preferences", 
            json=new_prefs, 
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # 3. Verify update
        response = await async_client.get("/users/preferences", headers=auth_headers)
        assert response.status_code == 200
        updated_prefs = response.json()
        
        assert updated_prefs["style_preferences"] == ["modern", "casual"]
        assert updated_prefs["preferred_colors"] == ["navy", "white"]
    
    async def test_user_statistics_after_activity(
        self, 
        async_client: AsyncClient, 
        test_user: User,
        auth_headers: dict,
        async_session: AsyncSession
    ):
        """Test user statistics after creating activity"""
        # 1. Get initial statistics (should be empty)
        response = await async_client.get("/users/statistics", headers=auth_headers)
        assert response.status_code == 200
        initial_stats = response.json()
        
        assert initial_stats["closet"]["total_items"] == 0
        assert initial_stats["recommendations"]["total_recommendations"] == 0
        
        # 2. Create some activity (clothing item)
        clothing_item = ClothingItem(
            user_id=test_user.id,
            filename="test_item.jpg",
            original_filename="test_item.jpg",
            category="tops",
            image_url="https://example.com/test.jpg",
            embedding=[0.1] * 512
        )
        async_session.add(clothing_item)
        await async_session.commit()
        
        # 3. Get updated statistics
        response = await async_client.get("/users/statistics", headers=auth_headers)
        assert response.status_code == 200
        updated_stats = response.json()
        
        assert updated_stats["closet"]["total_items"] == 1
        assert "tops" in updated_stats["closet"]["items_by_category"]