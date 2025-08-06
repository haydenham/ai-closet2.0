"""
Admin interface for managing quiz clothing items and categories
"""
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.database import get_sync_session
from app.services.quiz_service import QuizClothingItemService, StyleCategoryService
from app.models.quiz_system import QuizClothingItem, StyleCategory


class QuizAdminManager:
    """Admin manager for quiz system"""
    
    def __init__(self):
        self.db = next(get_sync_session())
    
    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()
    
    def list_clothing_items(self, gender: Optional[str] = None, category: Optional[str] = None) -> List[QuizClothingItem]:
        """List all clothing items with optional filters"""
        query = self.db.query(QuizClothingItem)
        
        if gender:
            query = query.filter(QuizClothingItem.gender == gender)
        if category:
            query = query.filter(QuizClothingItem.category == category)
        
        return query.all()
    
    def create_clothing_item(
        self,
        name: str,
        image_url: str,
        gender: str,
        category: str,
        features: List[str]
    ) -> QuizClothingItem:
        """Create a new clothing item"""
        return QuizClothingItemService.create_clothing_item(
            db=self.db,
            name=name,
            image_url=image_url,
            gender=gender,
            category=category,
            features=features
        )
    
    def update_clothing_item(
        self,
        item_id: uuid.UUID,
        **updates
    ) -> Optional[QuizClothingItem]:
        """Update a clothing item"""
        return QuizClothingItemService.update_clothing_item(
            self.db, item_id, **updates
        )
    
    def delete_clothing_item(self, item_id: uuid.UUID) -> bool:
        """Delete a clothing item"""
        return QuizClothingItemService.delete_clothing_item(self.db, item_id)
    
    def add_feature_to_item(self, item_id: uuid.UUID, feature: str) -> Optional[QuizClothingItem]:
        """Add a feature to an item"""
        return QuizClothingItemService.add_feature_to_item(self.db, item_id, feature)
    
    def remove_feature_from_item(self, item_id: uuid.UUID, feature: str) -> Optional[QuizClothingItem]:
        """Remove a feature from an item"""
        return QuizClothingItemService.remove_feature_from_item(self.db, item_id, feature)
    
    def list_style_categories(self, gender: Optional[str] = None) -> List[StyleCategory]:
        """List style categories"""
        if gender:
            return StyleCategoryService.get_categories_by_gender(self.db, gender)
        else:
            male_categories = StyleCategoryService.get_categories_by_gender(self.db, "male")
            female_categories = StyleCategoryService.get_categories_by_gender(self.db, "female")
            return male_categories + female_categories
    
    def create_style_category(
        self,
        name: str,
        gender: str,
        features: List[str],
        ai_theme_prompt: Optional[str] = None,
        description: Optional[str] = None
    ) -> StyleCategory:
        """Create a new style category"""
        return StyleCategoryService.create_style_category(
            db=self.db,
            name=name,
            gender=gender,
            features=features,
            ai_theme_prompt=ai_theme_prompt,
            description=description
        )
    
    def update_category_features(
        self,
        category_id: uuid.UUID,
        features: List[str]
    ) -> Optional[StyleCategory]:
        """Update category features"""
        return StyleCategoryService.update_category_features(
            self.db, category_id, features
        )
    
    def get_item_statistics(self) -> dict:
        """Get statistics about quiz items"""
        total_items = self.db.query(QuizClothingItem).count()
        active_items = self.db.query(QuizClothingItem).filter(
            QuizClothingItem.is_active == True
        ).count()
        
        male_items = self.db.query(QuizClothingItem).filter(
            QuizClothingItem.gender == "male"
        ).count()
        
        female_items = self.db.query(QuizClothingItem).filter(
            QuizClothingItem.gender == "female"
        ).count()
        
        # Get category distribution
        categories = {}
        for gender in ["male", "female"]:
            for category in ["top", "bottom", "shoes", "layering", "accessory", "complete_outfit"]:
                count = self.db.query(QuizClothingItem).filter(
                    QuizClothingItem.gender == gender,
                    QuizClothingItem.category == category
                ).count()
                categories[f"{gender}_{category}"] = count
        
        return {
            "total_items": total_items,
            "active_items": active_items,
            "male_items": male_items,
            "female_items": female_items,
            "category_distribution": categories
        }
    
    def print_statistics(self):
        """Print quiz system statistics"""
        stats = self.get_item_statistics()
        
        print("=== Quiz System Statistics ===")
        print(f"Total Items: {stats['total_items']}")
        print(f"Active Items: {stats['active_items']}")
        print(f"Male Items: {stats['male_items']}")
        print(f"Female Items: {stats['female_items']}")
        print("\n=== Category Distribution ===")
        
        for category, count in stats['category_distribution'].items():
            print(f"{category}: {count}")
    
    def print_items(self, gender: Optional[str] = None, category: Optional[str] = None):
        """Print clothing items"""
        items = self.list_clothing_items(gender, category)
        
        filter_str = ""
        if gender:
            filter_str += f" (Gender: {gender})"
        if category:
            filter_str += f" (Category: {category})"
        
        print(f"=== Clothing Items{filter_str} ===")
        
        for item in items:
            status = "Active" if item.is_active else "Inactive"
            print(f"ID: {item.id}")
            print(f"Name: {item.name}")
            print(f"Gender: {item.gender}")
            print(f"Category: {item.category}")
            print(f"Features: {', '.join(item.features or [])}")
            print(f"Status: {status}")
            print(f"Selection Count: {item.selection_count}")
            print("-" * 50)
    
    def print_categories(self, gender: Optional[str] = None):
        """Print style categories"""
        categories = self.list_style_categories(gender)
        
        filter_str = f" (Gender: {gender})" if gender else ""
        print(f"=== Style Categories{filter_str} ===")
        
        for category in categories:
            status = "Active" if category.is_active else "Inactive"
            print(f"ID: {category.id}")
            print(f"Name: {category.name}")
            print(f"Gender: {category.gender}")
            print(f"Features: {', '.join(category.features or [])}")
            print(f"Status: {status}")
            if category.description:
                print(f"Description: {category.description}")
            print("-" * 50)


def main():
    """Interactive admin interface"""
    admin = QuizAdminManager()
    
    while True:
        print("\n=== Quiz Admin Manager ===")
        print("1. View Statistics")
        print("2. List Clothing Items")
        print("3. List Style Categories")
        print("4. Create Clothing Item")
        print("5. Create Style Category")
        print("6. Add Feature to Item")
        print("7. Remove Feature from Item")
        print("8. Exit")
        
        choice = input("\nEnter your choice (1-8): ").strip()
        
        try:
            if choice == "1":
                admin.print_statistics()
            
            elif choice == "2":
                gender = input("Enter gender (male/female, or press Enter for all): ").strip() or None
                category = input("Enter category (or press Enter for all): ").strip() or None
                admin.print_items(gender, category)
            
            elif choice == "3":
                gender = input("Enter gender (male/female, or press Enter for all): ").strip() or None
                admin.print_categories(gender)
            
            elif choice == "4":
                print("\n=== Create Clothing Item ===")
                name = input("Name: ").strip()
                image_url = input("Image URL: ").strip()
                gender = input("Gender (male/female): ").strip()
                category = input("Category: ").strip()
                features_str = input("Features (comma-separated): ").strip()
                features = [f.strip() for f in features_str.split(",") if f.strip()]
                
                if name and image_url and gender and category:
                    item = admin.create_clothing_item(name, image_url, gender, category, features)
                    print(f"Created item: {item.name} (ID: {item.id})")
                else:
                    print("Error: All fields except features are required")
            
            elif choice == "5":
                print("\n=== Create Style Category ===")
                name = input("Name: ").strip()
                gender = input("Gender (male/female): ").strip()
                features_str = input("Features (comma-separated): ").strip()
                features = [f.strip() for f in features_str.split(",") if f.strip()]
                description = input("Description (optional): ").strip() or None
                ai_theme_prompt = input("AI Theme Prompt (optional): ").strip() or None
                
                if name and gender and features:
                    category = admin.create_style_category(
                        name, gender, features, ai_theme_prompt, description
                    )
                    print(f"Created category: {category.name} (ID: {category.id})")
                else:
                    print("Error: Name, gender, and features are required")
            
            elif choice == "6":
                print("\n=== Add Feature to Item ===")
                item_id_str = input("Item ID: ").strip()
                feature = input("Feature to add: ").strip()
                
                try:
                    item_id = uuid.UUID(item_id_str)
                    updated_item = admin.add_feature_to_item(item_id, feature)
                    if updated_item:
                        print(f"Added feature '{feature}' to {updated_item.name}")
                    else:
                        print("Item not found")
                except ValueError:
                    print("Invalid UUID format")
            
            elif choice == "7":
                print("\n=== Remove Feature from Item ===")
                item_id_str = input("Item ID: ").strip()
                feature = input("Feature to remove: ").strip()
                
                try:
                    item_id = uuid.UUID(item_id_str)
                    updated_item = admin.remove_feature_from_item(item_id, feature)
                    if updated_item:
                        print(f"Removed feature '{feature}' from {updated_item.name}")
                    else:
                        print("Item not found")
                except ValueError:
                    print("Invalid UUID format")
            
            elif choice == "8":
                print("Goodbye!")
                break
            
            else:
                print("Invalid choice. Please try again.")
        
        except Exception as e:
            print(f"Error: {e}")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()