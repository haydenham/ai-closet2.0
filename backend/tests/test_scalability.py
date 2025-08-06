"""
Scalability and performance tests for the Fashion AI Platform
"""
import pytest
import asyncio
import time
import concurrent.futures
from typing import List, Dict, Any
from unittest.mock import Mock, patch
import statistics

from app.services.quiz_service import QuizClothingItemService, StyleCategoryService
from app.services.gcp_storage_service import GCPStorageService
from app.services.gcp_vision_service import GCPVisionService
from app.core.database import get_sync_session


class TestDatabaseScalability:
    """Test database operations under load"""
    
    def test_concurrent_quiz_item_creation(self, db_session):
        """Test creating multiple quiz items concurrently"""
        def create_item(index: int):
            return QuizClothingItemService.create_clothing_item(
                db=db_session,
                name=f"Test Item {index}",
                image_url=f"/test/image_{index}.jpg",
                gender="male",
                category="top",
                features=[f"feature_{index}", "test"]
            )
        
        # Test concurrent creation
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_item, i) for i in range(50)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Assertions
        assert len(results) == 50
        assert all(item.id is not None for item in results)
        assert duration < 10.0  # Should complete within 10 seconds
        
        # Verify no duplicates
        item_ids = [item.id for item in results]
        assert len(set(item_ids)) == len(item_ids)
    
    def test_bulk_quiz_item_retrieval(self, db_session):
        """Test retrieving large numbers of quiz items efficiently"""
        # Create test data
        items = []
        for i in range(100):
            item = QuizClothingItemService.create_clothing_item(
                db=db_session,
                name=f"Bulk Test Item {i}",
                image_url=f"/bulk/image_{i}.jpg",
                gender="male" if i % 2 == 0 else "female",
                category="top",
                features=[f"bulk_feature_{i % 5}"]
            )
            items.append(item)
        
        # Test bulk retrieval performance
        start_time = time.time()
        
        # Test different retrieval patterns
        male_items = QuizClothingItemService.get_clothing_items_by_category(
            db_session, "male", "top"
        )
        female_items = QuizClothingItemService.get_clothing_items_by_category(
            db_session, "female", "top"
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Assertions
        assert len(male_items) == 50
        assert len(female_items) == 50
        assert duration < 1.0  # Should be very fast with proper indexing
    
    def test_feature_search_performance(self, db_session):
        """Test feature-based search performance with large datasets"""
        # Create items with various feature combinations
        feature_combinations = [
            ["casual", "cotton", "comfortable"],
            ["formal", "silk", "elegant"],
            ["sporty", "polyester", "athletic"],
            ["vintage", "denim", "retro"],
            ["minimalist", "linen", "simple"]
        ]
        
        for i in range(200):
            features = feature_combinations[i % len(feature_combinations)]
            QuizClothingItemService.create_clothing_item(
                db=db_session,
                name=f"Feature Test Item {i}",
                image_url=f"/feature/image_{i}.jpg",
                gender="male",
                category="top",
                features=features
            )
        
        # Test feature search performance
        search_terms = ["casual", "formal", "sporty"]
        
        start_time = time.time()
        for term in search_terms:
            results = QuizClothingItemService.get_items_by_features(
                db_session, "male", [term]
            )
            assert len(results) > 0
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete all searches quickly
        assert duration < 2.0
    
    def test_concurrent_style_scoring(self, db_session):
        """Test concurrent style score calculations"""
        # Create test categories
        categories = []
        for i in range(5):
            category = StyleCategoryService.create_style_category(
                db=db_session,
                name=f"Test Style {i}",
                gender="male",
                features=[f"style_{i}", "test_feature"]
            )
            categories.append(category)
        
        # Create test items
        items = []
        for i in range(20):
            item = QuizClothingItemService.create_clothing_item(
                db=db_session,
                name=f"Score Test Item {i}",
                image_url=f"/score/image_{i}.jpg",
                gender="male",
                category="top",
                features=[f"style_{i % 5}", "test_feature"]
            )
            items.append(item)
        
        def calculate_scores():
            return StyleCategoryService.calculate_style_scores(
                db_session, items[:5], "male"
            )
        
        # Test concurrent score calculations
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(calculate_scores) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Assertions
        assert len(results) == 10
        assert all(isinstance(result, dict) for result in results)
        assert duration < 5.0  # Should complete within 5 seconds


class TestAPIScalability:
    """Test API endpoint performance under load"""
    
    @pytest.mark.asyncio
    async def test_concurrent_api_requests(self, client, test_user):
        """Test API endpoints under concurrent load"""
        
        async def make_request():
            response = await client.get("/quiz/categories")
            return response.status_code
        
        # Test concurrent requests
        start_time = time.time()
        tasks = [make_request() for _ in range(50)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        duration = end_time - start_time
        
        # Assertions
        assert all(status == 200 for status in results)
        assert duration < 10.0  # Should handle 50 concurrent requests quickly
        
        # Calculate average response time
        avg_response_time = duration / len(results)
        assert avg_response_time < 0.2  # Average response time under 200ms
    
    def test_memory_usage_under_load(self, db_session):
        """Test memory usage patterns under load"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform memory-intensive operations
        items = []
        for i in range(1000):
            item = QuizClothingItemService.create_clothing_item(
                db=db_session,
                name=f"Memory Test Item {i}",
                image_url=f"/memory/image_{i}.jpg",
                gender="male",
                category="top",
                features=[f"memory_feature_{j}" for j in range(10)]
            )
            items.append(item)
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        # Clean up
        del items
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Assertions
        assert memory_increase < 100  # Should not use more than 100MB
        assert final_memory < peak_memory + 10  # Memory should be mostly freed


class TestCachePerformance:
    """Test caching performance and effectiveness"""
    
    @patch('app.services.quiz_service.QuizClothingItemService.get_clothing_items_by_category')
    def test_cache_hit_performance(self, mock_get_items, db_session):
        """Test cache performance for frequently accessed data"""
        # Mock database response
        mock_items = [Mock() for _ in range(10)]
        mock_get_items.return_value = mock_items
        
        # Simulate cache implementation
        cache = {}
        
        def cached_get_items(gender: str, category: str):
            cache_key = f"{gender}_{category}"
            if cache_key in cache:
                return cache[cache_key]
            
            result = QuizClothingItemService.get_clothing_items_by_category(
                db_session, gender, category
            )
            cache[cache_key] = result
            return result
        
        # Test cache performance
        start_time = time.time()
        
        # First call - cache miss
        result1 = cached_get_items("male", "top")
        
        # Subsequent calls - cache hits
        for _ in range(100):
            result = cached_get_items("male", "top")
            assert result == result1
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Assertions
        assert mock_get_items.call_count == 1  # Only called once due to caching
        assert duration < 0.1  # Cache hits should be very fast
    
    def test_cache_invalidation_strategy(self):
        """Test cache invalidation patterns"""
        cache = {}
        cache_timestamps = {}
        
        def set_cache(key: str, value: Any, ttl: int = 300):
            cache[key] = value
            cache_timestamps[key] = time.time() + ttl
        
        def get_cache(key: str) -> Any:
            if key in cache:
                if time.time() < cache_timestamps[key]:
                    return cache[key]
                else:
                    # Expired
                    del cache[key]
                    del cache_timestamps[key]
            return None
        
        # Test TTL-based invalidation
        set_cache("test_key", "test_value", ttl=1)
        
        # Should be available immediately
        assert get_cache("test_key") == "test_value"
        
        # Should expire after TTL
        time.sleep(1.1)
        assert get_cache("test_key") is None


class TestStorageScalability:
    """Test storage service scalability"""
    
    @patch('google.cloud.storage.Client')
    def test_concurrent_image_uploads(self, mock_storage_client):
        """Test concurrent image upload performance"""
        # Mock GCS client
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.public_url = "https://storage.googleapis.com/test/image.jpg"
        mock_bucket.blob.return_value = mock_blob
        mock_storage_client.return_value.bucket.return_value = mock_bucket
        
        storage_service = GCPStorageService()
        
        def upload_image(index: int):
            fake_image_data = b"fake_image_data_" + str(index).encode()
            return storage_service.upload_clothing_image(
                fake_image_data, f"test_image_{index}.jpg"
            )
        
        # Test concurrent uploads
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(upload_image, i) for i in range(20)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Assertions
        assert len(results) == 20
        assert all(len(result) == 2 for result in results)  # (url, filename) tuple
        assert duration < 15.0  # Should complete within reasonable time
    
    def test_image_optimization_performance(self):
        """Test image optimization performance"""
        from PIL import Image
        import io
        
        # Create test image
        test_image = Image.new('RGB', (2000, 2000), color='red')
        image_bytes = io.BytesIO()
        test_image.save(image_bytes, format='JPEG')
        image_data = image_bytes.getvalue()
        
        storage_service = GCPStorageService()
        
        # Test optimization performance
        start_time = time.time()
        optimized_data = storage_service._optimize_image(
            io.BytesIO(image_data), 'jpg'
        )
        end_time = time.time()
        
        duration = end_time - start_time
        
        # Assertions
        assert len(optimized_data) < len(image_data)  # Should be smaller
        assert duration < 2.0  # Should optimize quickly


class TestLoadTestingHelpers:
    """Helper functions for load testing"""
    
    @staticmethod
    def generate_test_data(db_session, num_items: int = 1000):
        """Generate test data for load testing"""
        categories = ["top", "bottom", "shoes", "layering", "accessory"]
        genders = ["male", "female"]
        features_pool = [
            "casual", "formal", "sporty", "elegant", "comfortable",
            "cotton", "silk", "denim", "leather", "polyester",
            "red", "blue", "black", "white", "gray"
        ]
        
        items = []
        for i in range(num_items):
            gender = genders[i % 2]
            category = categories[i % len(categories)]
            features = [features_pool[j] for j in range(i % 3 + 1)]
            
            item = QuizClothingItemService.create_clothing_item(
                db=db_session,
                name=f"Load Test Item {i}",
                image_url=f"/load_test/image_{i}.jpg",
                gender=gender,
                category=category,
                features=features
            )
            items.append(item)
        
        return items
    
    @staticmethod
    def measure_performance(func, *args, **kwargs) -> Dict[str, float]:
        """Measure function performance metrics"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Initial measurements
        start_time = time.time()
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        start_cpu = process.cpu_percent()
        
        # Execute function
        result = func(*args, **kwargs)
        
        # Final measurements
        end_time = time.time()
        end_memory = process.memory_info().rss / 1024 / 1024  # MB
        end_cpu = process.cpu_percent()
        
        return {
            'execution_time': end_time - start_time,
            'memory_used': end_memory - start_memory,
            'cpu_usage': end_cpu - start_cpu,
            'result': result
        }
    
    @staticmethod
    def run_stress_test(func, num_iterations: int = 100, max_workers: int = 10):
        """Run stress test on a function"""
        results = []
        errors = []
        
        def execute_with_error_handling(*args, **kwargs):
            try:
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()
                return {
                    'success': True,
                    'duration': end_time - start_time,
                    'result': result
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'duration': None
                }
        
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(execute_with_error_handling)
                for _ in range(num_iterations)
            ]
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result['success']:
                    results.append(result)
                else:
                    errors.append(result)
        
        end_time = time.time()
        
        # Calculate statistics
        if results:
            durations = [r['duration'] for r in results]
            stats = {
                'total_time': end_time - start_time,
                'successful_requests': len(results),
                'failed_requests': len(errors),
                'success_rate': len(results) / num_iterations * 100,
                'avg_response_time': statistics.mean(durations),
                'min_response_time': min(durations),
                'max_response_time': max(durations),
                'median_response_time': statistics.median(durations),
                'requests_per_second': len(results) / (end_time - start_time)
            }
        else:
            stats = {
                'total_time': end_time - start_time,
                'successful_requests': 0,
                'failed_requests': len(errors),
                'success_rate': 0,
                'errors': errors
            }
        
        return stats


# Performance benchmarks
class TestPerformanceBenchmarks:
    """Performance benchmark tests"""
    
    def test_quiz_completion_benchmark(self, db_session, test_user):
        """Benchmark complete quiz flow performance"""
        # Setup test data
        TestLoadTestingHelpers.generate_test_data(db_session, 100)
        
        # Create style categories
        for i in range(5):
            StyleCategoryService.create_style_category(
                db=db_session,
                name=f"Benchmark Style {i}",
                gender="male",
                features=[f"benchmark_{i}", "test"]
            )
        
        def complete_quiz():
            # Simulate quiz completion
            items = QuizClothingItemService.get_clothing_items_by_category(
                db_session, "male", "top"
            )[:5]
            
            scores = StyleCategoryService.calculate_style_scores(
                db_session, items, "male"
            )
            
            return len(items), len(scores)
        
        # Run benchmark
        performance = TestLoadTestingHelpers.measure_performance(complete_quiz)
        
        # Assertions
        assert performance['execution_time'] < 1.0  # Should complete within 1 second
        assert performance['memory_used'] < 50  # Should use less than 50MB
        assert performance['result'][0] > 0  # Should return items
        assert performance['result'][1] > 0  # Should return scores
    
    def test_database_query_benchmark(self, db_session):
        """Benchmark database query performance"""
        # Generate test data
        TestLoadTestingHelpers.generate_test_data(db_session, 500)
        
        def run_queries():
            # Test various query patterns
            results = []
            
            # Simple category query
            items1 = QuizClothingItemService.get_clothing_items_by_category(
                db_session, "male", "top"
            )
            results.append(len(items1))
            
            # Feature search query
            items2 = QuizClothingItemService.get_items_by_features(
                db_session, "female", ["casual", "comfortable"]
            )
            results.append(len(items2))
            
            return results
        
        # Run benchmark
        performance = TestLoadTestingHelpers.measure_performance(run_queries)
        
        # Assertions
        assert performance['execution_time'] < 0.5  # Should be very fast
        assert all(count >= 0 for count in performance['result'])
    
    def test_concurrent_load_benchmark(self, db_session):
        """Benchmark system under concurrent load"""
        # Generate test data
        TestLoadTestingHelpers.generate_test_data(db_session, 200)
        
        def query_function():
            return QuizClothingItemService.get_clothing_items_by_category(
                db_session, "male", "top"
            )
        
        # Run stress test
        stats = TestLoadTestingHelpers.run_stress_test(
            query_function, 
            num_iterations=50, 
            max_workers=5
        )
        
        # Assertions
        assert stats['success_rate'] > 95  # At least 95% success rate
        assert stats['avg_response_time'] < 1.0  # Average response under 1 second
        assert stats['requests_per_second'] > 10  # At least 10 RPS