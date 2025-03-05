import pytest
from fastapi.testclient import TestClient
from fastapi import status
from datetime import date, timedelta

@pytest.mark.tafakur
@pytest.mark.api
class TestTafakurAPI:
    """Tests for the Tafakur API endpoints"""
    
    def test_create_reflection(self, authenticated_client):
        """Test creating a reflection"""
        # Define reflection data
        reflection_data = {
            "reflection_date": date.today().isoformat(),
            "mood": "Good",
            "highlights": "Test highlights",
            "challenges": "Test challenges",
            "gratitude": "Test gratitude",
            "lessons": "Test lessons",
            "tomorrow_goals": "Test goals",
            "tags": ["test", "api"]
        }
        
        # Create reflection
        response = authenticated_client.post(
            "/api/tafakur/reflections",
            json=reflection_data
        )
        
        # Verify successful response
        assert response.status_code == status.HTTP_200_OK
        
        # Verify the response data
        data = response.json()
        assert data["reflection_date"] == reflection_data["reflection_date"]
        assert data["mood"] == reflection_data["mood"]
        assert data["highlights"] == reflection_data["highlights"]
        
        # Verify tags
        assert len(data["tags"]) == 2
        tag_names = [tag["tag_name"] for tag in data["tags"]]
        assert "test" in tag_names
        assert "api" in tag_names
    
    def test_get_reflections(self, authenticated_client, user_with_reflection):
        """Test getting user reflections"""
        # Get reflections
        response = authenticated_client.get("/api/tafakur/reflections")
        
        # Verify successful response
        assert response.status_code == status.HTTP_200_OK
        
        # Verify the response is a list
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1  # At least the one from fixture
        
        # Verify the reflection structure
        if data:
            reflection = data[0]
            assert "id" in reflection
            assert "reflection_date" in reflection
            assert "mood" in reflection
            assert "tags" in reflection
    
    def test_get_reflection_by_id(self, authenticated_client, user_with_reflection):
        """Test getting a reflection by ID"""
        user, reflection = user_with_reflection
        
        # Get reflection by ID
        response = authenticated_client.get(f"/api/tafakur/reflections/{reflection.id}")
        
        # Verify successful response
        assert response.status_code == status.HTTP_200_OK
        
        # Verify reflection data
        data = response.json()
        assert data["id"] == reflection.id
        assert data["mood"] == reflection.mood
        assert data["highlights"] == reflection.highlights
    
    def test_get_reflection_by_date(self, authenticated_client, user_with_reflection):
        """Test getting a reflection by date"""
        user, reflection = user_with_reflection
        
        # Format the date for URL
        reflection_date = date.today().isoformat()
        
        # Get reflection by date
        response = authenticated_client.get(f"/api/tafakur/reflections/date/{reflection_date}")
        
        # Verify successful response
        assert response.status_code == status.HTTP_200_OK
        
        # Verify reflection data
        data = response.json()
        assert data["id"] == reflection.id
        assert data["mood"] == reflection.mood
        assert data["reflection_date"] == reflection_date
    
    def test_get_todays_reflection(self, authenticated_client, user_with_reflection):
        """Test getting today's reflection"""
        # Get today's reflection
        response = authenticated_client.get("/api/tafakur/reflections/today")
        
        # Verify successful response
        assert response.status_code == status.HTTP_200_OK
        
        # Verify reflection data
        data = response.json()
        assert data["reflection_date"] == date.today().isoformat()
    
    def test_update_reflection(self, authenticated_client, user_with_reflection):
        """Test updating a reflection"""
        user, reflection = user_with_reflection
        
        # Define update data
        update_data = {
            "mood": "Great",  # Changed from "Good"
            "highlights": "Updated highlights",
            "tags": ["productivity", "focus", "health"]  # New tags
        }
        
        # Update reflection
        response = authenticated_client.put(
            f"/api/tafakur/reflections/{reflection.id}",
            json=update_data
        )
        
        # Verify successful response
        assert response.status_code == status.HTTP_200_OK
        
        # Verify update was applied
        data = response.json()
        assert data["mood"] == update_data["mood"]
        assert data["highlights"] == update_data["highlights"]
        
        # Verify tags were updated
        assert len(data["tags"]) == 3
        tag_names = [tag["tag_name"] for tag in data["tags"]]
        for tag in update_data["tags"]:
            assert tag in tag_names
    
    def test_delete_reflection(self, authenticated_client, user_with_reflection):
        """Test deleting a reflection"""
        user, reflection = user_with_reflection
        
        # Delete reflection
        response = authenticated_client.delete(f"/api/tafakur/reflections/{reflection.id}")
        
        # Verify successful response
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify reflection was deleted
        get_response = authenticated_client.get(f"/api/tafakur/reflections/{reflection.id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_get_reflection_streak(self, authenticated_client):
        """Test getting reflection streak information"""
        # Get streak
        response = authenticated_client.get("/api/tafakur/streak")
        
        # Verify successful response
        assert response.status_code == status.HTTP_200_OK
        
        # Verify streak data
        data = response.json()
        assert "current_streak" in data
        assert "longest_streak" in data
        assert "last_reflection_date" in data
    
    def test_get_insights(self, authenticated_client):
        """Test getting reflection insights"""
        # Get insights
        response = authenticated_client.get("/api/tafakur/insights")
        
        # Verify successful response
        assert response.status_code == status.HTTP_200_OK
        
        # Verify insights data
        data = response.json()
        assert "date_range" in data
        assert "mood_distribution" in data
        assert "common_tags" in data
        assert "streak" in data
        assert "total_reflections" in data
        assert "word_frequency" in data
    
    def test_get_insights_with_date_range(self, authenticated_client):
        """Test getting insights with date range"""
        # Define date range
        from_date = (date.today() - timedelta(days=10)).isoformat()
        to_date = date.today().isoformat()
        
        # Get insights with date range
        response = authenticated_client.get(
            f"/api/tafakur/insights?from_date={from_date}&to_date={to_date}"
        )
        
        # Verify successful response
        assert response.status_code == status.HTTP_200_OK
        
        # Verify insights data has correct date range
        data = response.json()
        assert len(data["date_range"]) == 11  # 11 days (inclusive range) 