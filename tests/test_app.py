"""
Test suite for the Mergington High School Management System API
Uses the AAA (Arrange-Act-Assert) testing pattern for clarity and structure.
"""

import pytest
from fastapi.testclient import TestClient
from copy import deepcopy
from src.app import app, activities


@pytest.fixture
def client():
    """Create a fresh TestClient for each test"""
    return TestClient(app)


@pytest.fixture
def reset_activities_state():
    """
    Reset activities to initial state before each test.
    This fixture ensures test isolation by providing a fresh state.
    """
    # Store original state
    original_state = deepcopy(activities)
    
    yield
    
    # Restore original state after test
    activities.clear()
    activities.update(original_state)


# ==================== ROOT ENDPOINT TESTS ====================

class TestRootEndpoint:
    """Tests for the root (/) endpoint redirecting to static files"""
    
    def test_root_endpoint_redirects_to_static_index(self, client):
        """
        Test: Root endpoint should redirect to /static/index.html
        AAA Pattern:
        - Arrange: TestClient ready
        - Act: Make GET request to root without following redirects
        - Assert: Check redirect response and location header
        """
        # Arrange
        expected_status = 307
        expected_location = "/static/index.html"
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == expected_status
        assert response.headers["location"] == expected_location


# ==================== GET ACTIVITIES ENDPOINT TESTS ====================

class TestGetActivitiesEndpoint:
    """Tests for the GET /activities endpoint"""
    
    def test_get_activities_returns_success_status(self, client, reset_activities_state):
        """
        Test: GET /activities should return 200 status
        AAA Pattern:
        - Arrange: Define expected status code
        - Act: Call GET /activities endpoint
        - Assert: Verify response status
        """
        # Arrange
        expected_status = 200
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == expected_status
    
    def test_get_activities_returns_dict(self, client, reset_activities_state):
        """
        Test: GET /activities should return a dictionary
        AAA Pattern:
        - Arrange: Set expected type
        - Act: Call endpoint and parse response
        - Assert: Verify response is dict
        """
        # Arrange
        expected_type = dict
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert isinstance(data, expected_type)
        assert len(data) > 0
    
    def test_get_activities_contains_all_expected_fields(self, client, reset_activities_state):
        """
        Test: Each activity should contain required fields
        AAA Pattern:
        - Arrange: Define required fields
        - Act: Fetch activities and inspect structure
        - Assert: Verify all activities have required fields
        """
        # Arrange
        required_fields = {
            "description",
            "schedule",
            "max_participants",
            "participants"
        }
        
        # Act
        response = client.get("/activities")
        activities_data = response.json()
        
        # Assert
        for activity_name, activity_info in activities_data.items():
            assert isinstance(activity_name, str), f"Activity name should be string: {activity_name}"
            for field in required_fields:
                assert field in activity_info, f"Missing field '{field}' in activity '{activity_name}'"
            assert isinstance(activity_info["participants"], list)
    
    def test_get_activities_contains_expected_activities(self, client, reset_activities_state):
        """
        Test: Response should include all expected activities
        AAA Pattern:
        - Arrange: Define list of expected activities
        - Act: Fetch all activities
        - Assert: Verify all expected activities present
        """
        # Arrange
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Tennis Club",
            "Drama Club",
            "Art Studio",
            "Debate Team",
            "Robotics Club"
        ]
        
        # Act
        response = client.get("/activities")
        activities_data = response.json()
        activity_names = list(activities_data.keys())
        
        # Assert
        for expected_activity in expected_activities:
            assert expected_activity in activity_names


# ==================== SIGNUP ENDPOINT TESTS ====================

class TestSignupForActivityEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_successful_for_new_student(self, client, reset_activities_state):
        """
        Test: New student should successfully sign up
        AAA Pattern:
        - Arrange: Prepare activity name and new email
        - Act: Make signup POST request
        - Assert: Verify success response
        """
        # Arrange
        activity_name = "Chess Club"
        new_email = "alice@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        
        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert new_email in response.json()["message"]
    
    def test_signup_adds_participant_to_activity(self, client, reset_activities_state):
        """
        Test: Signup should add participant to activity's participant list
        AAA Pattern:
        - Arrange: Get initial participant count
        - Act: Sign up new student
        - Assert: Verify participant count increased and email added
        """
        # Arrange
        activity_name = "Programming Class"
        new_email = "bob@mergington.edu"
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])
        
        # Act
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        
        # Assert
        assert signup_response.status_code == 200
        verify_response = client.get("/activities")
        final_count = len(verify_response.json()[activity_name]["participants"])
        assert final_count == initial_count + 1
        assert new_email in verify_response.json()[activity_name]["participants"]
    
    def test_signup_nonexistent_activity_returns_404(self, client, reset_activities_state):
        """
        Test: Signup to nonexistent activity returns 404
        AAA Pattern:
        - Arrange: Create nonexistent activity name
        - Act: Attempt signup to nonexistent activity
        - Assert: Verify 404 status and error message
        """
        # Arrange
        nonexistent_activity = "Nonexistent Activity"
        email = "student@mergington.edu"
        expected_status = 404
        expected_detail = "Activity not found"
        
        # Act
        response = client.post(
            f"/activities/{nonexistent_activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == expected_status
        assert response.json()["detail"] == expected_detail
    
    def test_signup_duplicate_registration_returns_400(self, client, reset_activities_state):
        """
        Test: Duplicate signup (student already registered) returns 400
        AAA Pattern:
        - Arrange: Identify already-registered student
        - Act: Attempt to sign up with same email
        - Assert: Verify 400 status and error message
        """
        # Arrange
        activity_name = "Chess Club"
        initial_response = client.get("/activities")
        already_registered_email = initial_response.json()[activity_name]["participants"][0]
        expected_status = 400
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": already_registered_email}
        )
        
        # Assert
        assert response.status_code == expected_status
        assert "already signed up" in response.json()["detail"].lower()
    
    def test_signup_same_student_multiple_activities(self, client, reset_activities_state):
        """
        Test: Same student can sign up for multiple different activities
        AAA Pattern:
        - Arrange: Prepare email and two different activities
        - Act: Sign up for first activity, then second
        - Assert: Verify success for both and student in both activities
        """
        # Arrange
        student_email = "carlos@mergington.edu"
        activity_1 = "Chess Club"
        activity_2 = "Robotics Club"
        
        # Act
        response1 = client.post(
            f"/activities/{activity_1}/signup",
            params={"email": student_email}
        )
        response2 = client.post(
            f"/activities/{activity_2}/signup",
            params={"email": student_email}
        )
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        verify_response = client.get("/activities")
        activities_data = verify_response.json()
        assert student_email in activities_data[activity_1]["participants"]
        assert student_email in activities_data[activity_2]["participants"]
    
    def test_signup_activity_name_case_sensitive(self, client, reset_activities_state):
        """
        Test: Activity name lookup is case-sensitive
        AAA Pattern:
        - Arrange: Create wrong-case activity name
        - Act: Attempt signup with wrong case
        - Assert: Verify 404 response
        """
        # Arrange
        correct_case = "Chess Club"
        wrong_case = "chess club"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{wrong_case}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404


# ==================== UNREGISTER ENDPOINT TESTS ====================

class TestUnregisterFromActivityEndpoint:
    """Tests for the POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_successful_for_registered_student(self, client, reset_activities_state):
        """
        Test: Registered student should successfully unregister
        AAA Pattern:
        - Arrange: Identify registered student
        - Act: Make unregister POST request
        - Assert: Verify success response
        """
        # Arrange
        activity_name = "Chess Club"
        registered_email = client.get("/activities").json()[activity_name]["participants"][0]
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": registered_email}
        )
        
        # Assert
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
    
    def test_unregister_removes_participant_from_activity(self, client, reset_activities_state):
        """
        Test: Unregister should remove participant from activity
        AAA Pattern:
        - Arrange: Get initial participant count
        - Act: Unregister a student
        - Assert: Verify count decreased and email removed
        """
        # Arrange
        activity_name = "Tennis Club"
        email_to_remove = client.get("/activities").json()[activity_name]["participants"][0]
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])
        
        # Act
        unregister_response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email_to_remove}
        )
        
        # Assert
        assert unregister_response.status_code == 200
        verify_response = client.get("/activities")
        final_count = len(verify_response.json()[activity_name]["participants"])
        assert final_count == initial_count - 1
        assert email_to_remove not in verify_response.json()[activity_name]["participants"]
    
    def test_unregister_nonexistent_activity_returns_404(self, client, reset_activities_state):
        """
        Test: Unregister from nonexistent activity returns 404
        AAA Pattern:
        - Arrange: Create nonexistent activity name
        - Act: Attempt unregister from nonexistent activity
        - Assert: Verify 404 status
        """
        # Arrange
        nonexistent_activity = "Fake Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{nonexistent_activity}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_unregister_not_registered_student_returns_400(self, client, reset_activities_state):
        """
        Test: Unregister of non-registered student returns 400
        AAA Pattern:
        - Arrange: Choose student not registered
        - Act: Attempt to unregister non-registered student
        - Assert: Verify 400 status and error message
        """
        # Arrange
        activity_name = "Drama Club"
        not_registered_email = "notregistered@mergington.edu"
        expected_status = 400
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": not_registered_email}
        )
        
        # Assert
        assert response.status_code == expected_status
        assert "not registered" in response.json()["detail"].lower()
    
    def test_unregister_does_not_affect_other_activities(self, client, reset_activities_state):
        """
        Test: Unregister from one activity doesn't affect other activities
        AAA Pattern:
        - Arrange: Sign up for two activities
        - Act: Unregister from first activity
        - Assert: Verify still in second activity
        """
        # Arrange
        student_email = "diana@mergington.edu"
        activity_1 = "Art Studio"
        activity_2 = "Debate Team"
        
        # Sign up for both
        client.post(f"/activities/{activity_1}/signup", params={"email": student_email})
        client.post(f"/activities/{activity_2}/signup", params={"email": student_email})
        
        # Act
        unregister_response = client.post(
            f"/activities/{activity_1}/unregister",
            params={"email": student_email}
        )
        
        # Assert
        assert unregister_response.status_code == 200
        verify_response = client.get("/activities")
        activities_data = verify_response.json()
        assert student_email not in activities_data[activity_1]["participants"]
        assert student_email in activities_data[activity_2]["participants"]


# ==================== INTEGRATION TESTS ====================

class TestIntegrationWorkflows:
    """Integration tests for complete workflows involving multiple endpoints"""
    
    def test_signup_unregister_signup_workflow(self, client, reset_activities_state):
        """
        Test: Complete workflow - signup, unregister, signup again
        AAA Pattern:
        - Arrange: Prepare email and activity
        - Act: Signup, capture count; Unregister; Signup again
        - Assert: Verify each action succeeds and state changes correctly
        """
        # Arrange
        student_email = "eve@mergington.edu"
        activity_name = "Robotics Club"
        initial_state = client.get("/activities").json()
        initial_count = len(initial_state[activity_name]["participants"])
        
        # Act: Sign up
        signup1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": student_email}
        )
        after_signup = client.get("/activities").json()
        count_after_signup = len(after_signup[activity_name]["participants"])
        
        # Act: Unregister
        unregister = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": student_email}
        )
        after_unregister = client.get("/activities").json()
        count_after_unregister = len(after_unregister[activity_name]["participants"])
        
        # Act: Sign up again
        signup2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": student_email}
        )
        final_state = client.get("/activities").json()
        final_count = len(final_state[activity_name]["participants"])
        
        # Assert
        assert signup1.status_code == 200
        assert count_after_signup == initial_count + 1
        assert unregister.status_code == 200
        assert count_after_unregister == initial_count
        assert signup2.status_code == 200
        assert final_count == initial_count + 1
        assert student_email in final_state[activity_name]["participants"]
    
    def test_multiple_students_signup_for_same_activity(self, client, reset_activities_state):
        """
        Test: Multiple different students can sign up for the same activity
        AAA Pattern:
        - Arrange: Prepare multiple student emails
        - Act: Each student signs up for same activity
        - Assert: All students successfully added to activity
        """
        # Arrange
        students = [
            "frank@mergington.edu",
            "grace@mergington.edu",
            "henry@mergington.edu"
        ]
        activity_name = "Basketball Team"
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])
        
        # Act
        responses = []
        for student in students:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": student}
            )
            responses.append(response)
        
        # Assert
        for response in responses:
            assert response.status_code == 200
        
        final_response = client.get("/activities")
        final_count = len(final_response.json()[activity_name]["participants"])
        assert final_count == initial_count + len(students)
        
        for student in students:
            assert student in final_response.json()[activity_name]["participants"]
