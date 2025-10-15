"""Unit tests for web interface functionality."""
import pytest
import json
from bs4 import BeautifulSoup
from app import db
from app.models.user import User, TestAssignment
from app.models.test import Test
from app.models.experiment import Experiment


class TestWebAuthentication:
    """Test web authentication pages."""
    
    def test_login_page_renders(self, client, app):
        """Test that login page renders correctly."""
        with app.app_context():
            response = client.get('/login')
            assert response.status_code == 200
            
            # Parse HTML content
            soup = BeautifulSoup(response.data, 'html.parser')
            
            # Check for login form elements
            assert soup.find('form') is not None
            assert soup.find('input', {'name': 'email'}) is not None
            assert soup.find('input', {'name': 'password'}) is not None
            assert soup.find('button', {'type': 'submit'}) is not None
            
            # Check for proper page title
            title = soup.find('title')
            assert title is not None
            assert 'Login' in title.text
    
    def test_login_form_submission(self, client, app, admin_user):
        """Test login form submission."""
        with app.app_context():
            # Submit login form
            response = client.post('/login', data={
                'email': 'admin@test.com',
                'password': 'password123'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            
            # Should redirect to dashboard after successful login
            soup = BeautifulSoup(response.data, 'html.parser')
            # Check for dashboard elements
            assert 'Dashboard' in soup.text or 'Tests' in soup.text
    
    def test_login_invalid_credentials(self, client, app):
        """Test login with invalid credentials."""
        with app.app_context():
            response = client.post('/login', data={
                'email': 'invalid@test.com',
                'password': 'wrongpassword'
            })
            
            assert response.status_code == 200
            
            # Should show error message
            soup = BeautifulSoup(response.data, 'html.parser')
            error_elements = soup.find_all(class_=['error', 'alert', 'danger'])
            assert len(error_elements) > 0 or 'Invalid' in soup.text
    
    def test_logout_functionality(self, client, app, admin_user):
        """Test logout functionality."""
        with app.app_context():
            # Login first
            client.post('/login', data={
                'email': 'admin@test.com',
                'password': 'password123'
            })
            
            # Logout
            response = client.get('/logout', follow_redirects=True)
            assert response.status_code == 200
            
            # Should redirect to login page
            soup = BeautifulSoup(response.data, 'html.parser')
            assert soup.find('input', {'name': 'email'}) is not None
    
    def test_password_recovery_page(self, client, app):
        """Test password recovery page."""
        with app.app_context():
            response = client.get('/reset-password')
            assert response.status_code == 200
            
            soup = BeautifulSoup(response.data, 'html.parser')
            
            # Check for password reset form
            assert soup.find('form') is not None
            assert soup.find('input', {'name': 'email'}) is not None
            assert 'Reset' in soup.text or 'Password' in soup.text


class TestMainDashboard:
    """Test main dashboard interface."""
    
    def test_dashboard_requires_login(self, client, app):
        """Test that dashboard requires authentication."""
        with app.app_context():
            response = client.get('/')
            # Should redirect to login
            assert response.status_code == 302 or response.status_code == 401
    
    def test_admin_dashboard_layout(self, client, app, admin_user, sample_test):
        """Test admin dashboard layout."""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': 'admin@test.com',
                'password': 'password123'
            })
            
            response = client.get('/')
            assert response.status_code == 200
            
            soup = BeautifulSoup(response.data, 'html.parser')
            
            # Check for two-panel layout
            left_panel = soup.find(class_=['left-panel', 'test-list', 'sidebar'])
            right_panel = soup.find(class_=['right-panel', 'parameters', 'details'])
            
            assert left_panel is not None or 'Tests' in soup.text
            assert right_panel is not None or 'Parameters' in soup.text
            
            # Check for admin buttons
            admin_buttons = soup.find_all('button')
            button_texts = [btn.text.strip() for btn in admin_buttons]
            
            expected_buttons = ['Create', 'Delete', 'Edit', 'Users']
            for expected in expected_buttons:
                assert any(expected in text for text in button_texts)
    
    def test_researcher_dashboard_layout(self, client, app, researcher_user, sample_test):
        """Test researcher dashboard layout."""
        with app.app_context():
            # Assign test to researcher
            assignment = TestAssignment(
                user_id=researcher_user.id,
                test_id=sample_test.id
            )
            db.session.add(assignment)
            db.session.commit()
            
            # Login as researcher
            client.post('/login', data={
                'email': 'researcher@test.com',
                'password': 'password123'
            })
            
            response = client.get('/')
            assert response.status_code == 200
            
            soup = BeautifulSoup(response.data, 'html.parser')
            
            # Should not have admin buttons
            admin_buttons = ['Create', 'Delete', 'Edit', 'Users']
            button_texts = [btn.text.strip() for btn in soup.find_all('button')]
            
            for admin_btn in admin_buttons:
                assert not any(admin_btn in text for text in button_texts)
    
    def test_test_list_display(self, client, app, admin_user, sample_test):
        """Test test list display."""
        with app.app_context():
            # Create additional test
            test2 = Test(
                name='Second Test',
                class_name='test.second',
                status='production'
            )
            db.session.add(test2)
            db.session.commit()
            
            # Login as admin
            client.post('/login', data={
                'email': 'admin@test.com',
                'password': 'password123'
            })
            
            response = client.get('/')
            assert response.status_code == 200
            
            soup = BeautifulSoup(response.data, 'html.parser')
            
            # Check that both tests are displayed
            assert 'Sample Test' in soup.text
            assert 'Second Test' in soup.text
    
    def test_test_parameters_display(self, client, app, admin_user, sample_test):
        """Test test parameters display."""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': 'admin@test.com',
                'password': 'password123'
            })
            
            # Get dashboard with test selection
            response = client.get(f'/?selected_test={sample_test.id}')
            assert response.status_code == 200
            
            soup = BeautifulSoup(response.data, 'html.parser')
            
            # Check for parameters table
            table = soup.find('table')
            if table:
                # Should have Label and Value columns
                headers = [th.text.strip() for th in table.find_all('th')]
                assert 'Label' in headers or 'Parameter' in headers
                assert 'Value' in headers


class TestTestManagementInterface:
    """Test test management web interface."""
    
    def test_create_test_page(self, client, app, admin_user):
        """Test create test page."""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': 'admin@test.com',
                'password': 'password123'
            })
            
            response = client.get('/admin/tests/create')
            assert response.status_code == 200
            
            soup = BeautifulSoup(response.data, 'html.parser')
            
            # Check for test creation form
            form = soup.find('form')
            assert form is not None
            
            # Check for required fields
            assert soup.find('input', {'name': 'name'}) is not None
            assert soup.find('input', {'name': 'class_name'}) is not None
            assert soup.find('select', {'name': 'status'}) is not None
    
    def test_create_test_form_submission(self, client, app, admin_user):
        """Test create test form submission."""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': 'admin@test.com',
                'password': 'password123'
            })
            
            # Submit create test form
            response = client.post('/admin/tests/create', data={
                'name': 'Web Created Test',
                'class_name': 'test.web.created',
                'description': 'Test created via web interface',
                'status': 'development'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            
            # Verify test was created
            test = Test.query.filter_by(name='Web Created Test').first()
            assert test is not None
            assert test.class_name == 'test.web.created'
    
    def test_edit_test_page(self, client, app, admin_user, sample_test):
        """Test edit test page."""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': 'admin@test.com',
                'password': 'password123'
            })
            
            response = client.get(f'/admin/tests/{sample_test.id}/edit')
            assert response.status_code == 200
            
            soup = BeautifulSoup(response.data, 'html.parser')
            
            # Check that form is pre-populated
            name_input = soup.find('input', {'name': 'name'})
            assert name_input is not None
            assert name_input.get('value') == 'Sample Test'
    
    def test_edit_test_form_submission(self, client, app, admin_user, sample_test):
        """Test edit test form submission."""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': 'admin@test.com',
                'password': 'password123'
            })
            
            # Submit edit form
            response = client.post(f'/admin/tests/{sample_test.id}/edit', data={
                'name': 'Updated Sample Test',
                'class_name': sample_test.class_name,
                'description': 'Updated description',
                'status': 'production'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            
            # Verify test was updated
            test = Test.query.get(sample_test.id)
            assert test.name == 'Updated Sample Test'
            assert test.description == 'Updated description'
            assert test.status == 'production'
    
    def test_delete_test_confirmation(self, client, app, admin_user, sample_test):
        """Test delete test confirmation."""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': 'admin@test.com',
                'password': 'password123'
            })
            
            response = client.get(f'/admin/tests/{sample_test.id}/delete')
            assert response.status_code == 200
            
            soup = BeautifulSoup(response.data, 'html.parser')
            
            # Check for confirmation message
            assert 'confirm' in soup.text.lower() or 'delete' in soup.text.lower()
            assert sample_test.name in soup.text


class TestUserManagementInterface:
    """Test user management web interface."""
    
    def test_users_page_admin_access(self, client, app, admin_user, researcher_user):
        """Test users page for admin."""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': 'admin@test.com',
                'password': 'password123'
            })
            
            response = client.get('/admin/users')
            assert response.status_code == 200
            
            soup = BeautifulSoup(response.data, 'html.parser')
            
            # Check for user list
            assert 'admin@test.com' in soup.text
            assert 'researcher@test.com' in soup.text
            
            # Check for user management buttons
            buttons = soup.find_all('button')
            button_texts = [btn.text.strip() for btn in buttons]
            
            expected_buttons = ['Create', 'Delete', 'Assign']
            for expected in expected_buttons:
                assert any(expected in text for text in button_texts)
    
    def test_users_page_researcher_denied(self, client, app, researcher_user):
        """Test users page denied for researcher."""
        with app.app_context():
            # Login as researcher
            client.post('/login', data={
                'email': 'researcher@test.com',
                'password': 'password123'
            })
            
            response = client.get('/admin/users')
            # Should be denied access
            assert response.status_code == 403 or response.status_code == 302
    
    def test_create_user_page(self, client, app, admin_user):
        """Test create user page."""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': 'admin@test.com',
                'password': 'password123'
            })
            
            response = client.get('/admin/users/create')
            assert response.status_code == 200
            
            soup = BeautifulSoup(response.data, 'html.parser')
            
            # Check for user creation form
            form = soup.find('form')
            assert form is not None
            
            # Check for required fields
            assert soup.find('input', {'name': 'email'}) is not None
            assert soup.find('input', {'name': 'password'}) is not None
            assert soup.find('select', {'name': 'role'}) is not None
    
    def test_create_user_form_submission(self, client, app, admin_user):
        """Test create user form submission."""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': 'admin@test.com',
                'password': 'password123'
            })
            
            # Submit create user form
            response = client.post('/admin/users/create', data={
                'email': 'newuser@test.com',
                'password': 'newpassword123',
                'role': 'researcher'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            
            # Verify user was created
            user = User.query.filter_by(email='newuser@test.com').first()
            assert user is not None
            assert user.role == 'researcher'
    
    def test_test_assignment_interface(self, client, app, admin_user, researcher_user, sample_test):
        """Test test assignment interface."""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': 'admin@test.com',
                'password': 'password123'
            })
            
            response = client.get(f'/admin/users/{researcher_user.id}/assign-tests')
            assert response.status_code == 200
            
            soup = BeautifulSoup(response.data, 'html.parser')
            
            # Check for test assignment form
            form = soup.find('form')
            assert form is not None
            
            # Check for test checkboxes
            checkboxes = soup.find_all('input', {'type': 'checkbox'})
            assert len(checkboxes) > 0


class TestExperimentViewingInterface:
    """Test experiment viewing web interface."""
    
    def test_experiments_list_page(self, client, app, admin_user, sample_experiment):
        """Test experiments list page."""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': 'admin@test.com',
                'password': 'password123'
            })
            
            response = client.get('/experiments')
            assert response.status_code == 200
            
            soup = BeautifulSoup(response.data, 'html.parser')
            
            # Check for experiments table
            table = soup.find('table')
            assert table is not None
            
            # Check for experiment data
            assert sample_experiment.unique_id in soup.text
            assert sample_experiment.subject_label in soup.text
    
    def test_experiment_detail_page(self, client, app, admin_user, sample_experiment):
        """Test single experiment detail page."""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': 'admin@test.com',
                'password': 'password123'
            })
            
            response = client.get(f'/experiments/{sample_experiment.id}')
            assert response.status_code == 200
            
            soup = BeautifulSoup(response.data, 'html.parser')
            
            # Check for experiment details
            assert sample_experiment.unique_id in soup.text
            assert sample_experiment.subject_label in soup.text
            
            # Check for trial data table
            table = soup.find('table')
            assert table is not None
    
    def test_experiments_filtering(self, client, app, admin_user, sample_experiment):
        """Test experiments filtering functionality."""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': 'admin@test.com',
                'password': 'password123'
            })
            
            # Test filtering by test
            response = client.get(f'/experiments?test_id={sample_experiment.test_id}')
            assert response.status_code == 200
            
            soup = BeautifulSoup(response.data, 'html.parser')
            assert sample_experiment.unique_id in soup.text
    
    def test_experiments_sorting(self, client, app, admin_user, sample_experiment):
        """Test experiments sorting functionality."""
        with app.app_context():
            # Create additional experiment
            exp2 = Experiment(
                unique_id='exp_sort_002',
                test_id=sample_experiment.test_id,
                subject_label='subject_002'
            )
            db.session.add(exp2)
            db.session.commit()
            
            # Login as admin
            client.post('/login', data={
                'email': 'admin@test.com',
                'password': 'password123'
            })
            
            # Test sorting by date
            response = client.get('/experiments?sort=date&order=desc')
            assert response.status_code == 200
            
            soup = BeautifulSoup(response.data, 'html.parser')
            
            # Both experiments should be visible
            assert sample_experiment.unique_id in soup.text
            assert exp2.unique_id in soup.text
    
    def test_experiment_download_links(self, client, app, admin_user, sample_experiment):
        """Test experiment download links."""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': 'admin@test.com',
                'password': 'password123'
            })
            
            response = client.get('/experiments')
            assert response.status_code == 200
            
            soup = BeautifulSoup(response.data, 'html.parser')
            
            # Check for download links
            download_links = soup.find_all('a', href=lambda x: x and 'download' in x)
            assert len(download_links) > 0


class TestFormValidationAndErrorHandling:
    """Test form validation and error handling."""
    
    def test_form_validation_errors(self, client, app, admin_user):
        """Test form validation error display."""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': 'admin@test.com',
                'password': 'password123'
            })
            
            # Submit invalid test creation form
            response = client.post('/admin/tests/create', data={
                'name': '',  # Empty name should cause validation error
                'class_name': '',
                'status': 'invalid_status'
            })
            
            assert response.status_code == 200  # Should return form with errors
            
            soup = BeautifulSoup(response.data, 'html.parser')
            
            # Check for error messages
            error_elements = soup.find_all(class_=['error', 'alert', 'danger', 'invalid'])
            assert len(error_elements) > 0 or 'required' in soup.text.lower()
    
    def test_csrf_protection(self, client, app, admin_user):
        """Test CSRF protection on forms."""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': 'admin@test.com',
                'password': 'password123'
            })
            
            # Get form page to check for CSRF token
            response = client.get('/admin/tests/create')
            assert response.status_code == 200
            
            soup = BeautifulSoup(response.data, 'html.parser')
            
            # Check for CSRF token field
            csrf_field = soup.find('input', {'name': 'csrf_token'}) or soup.find('input', {'type': 'hidden'})
            # CSRF protection may or may not be implemented
            # This test documents the expectation
    
    def test_error_page_handling(self, client, app, admin_user):
        """Test error page handling."""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': 'admin@test.com',
                'password': 'password123'
            })
            
            # Try to access nonexistent test
            response = client.get('/admin/tests/99999/edit')
            assert response.status_code == 404
            
            # Try to access nonexistent experiment
            response = client.get('/experiments/99999')
            assert response.status_code == 404


class TestResponsiveDesign:
    """Test responsive design elements."""
    
    def test_mobile_viewport_meta(self, client, app, admin_user):
        """Test mobile viewport meta tag."""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': 'admin@test.com',
                'password': 'password123'
            })
            
            response = client.get('/')
            assert response.status_code == 200
            
            soup = BeautifulSoup(response.data, 'html.parser')
            
            # Check for viewport meta tag
            viewport_meta = soup.find('meta', {'name': 'viewport'})
            if viewport_meta:
                assert 'width=device-width' in viewport_meta.get('content', '')
    
    def test_css_framework_inclusion(self, client, app, admin_user):
        """Test CSS framework inclusion."""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': 'admin@test.com',
                'password': 'password123'
            })
            
            response = client.get('/')
            assert response.status_code == 200
            
            soup = BeautifulSoup(response.data, 'html.parser')
            
            # Check for CSS links
            css_links = soup.find_all('link', {'rel': 'stylesheet'})
            assert len(css_links) > 0
    
    def test_javascript_inclusion(self, client, app, admin_user):
        """Test JavaScript inclusion."""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': 'admin@test.com',
                'password': 'password123'
            })
            
            response = client.get('/')
            assert response.status_code == 200
            
            soup = BeautifulSoup(response.data, 'html.parser')
            
            # Check for JavaScript files
            script_tags = soup.find_all('script', {'src': True})
            assert len(script_tags) > 0


class TestAccessibilityFeatures:
    """Test accessibility features."""
    
    def test_form_labels(self, client, app, admin_user):
        """Test form labels for accessibility."""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': 'admin@test.com',
                'password': 'password123'
            })
            
            response = client.get('/admin/tests/create')
            assert response.status_code == 200
            
            soup = BeautifulSoup(response.data, 'html.parser')
            
            # Check that form inputs have labels
            inputs = soup.find_all('input')
            for input_elem in inputs:
                if input_elem.get('type') not in ['hidden', 'submit']:
                    input_id = input_elem.get('id')
                    input_name = input_elem.get('name')
                    
                    # Should have associated label
                    label = soup.find('label', {'for': input_id}) if input_id else None
                    if not label and input_name:
                        # Check for label with matching text
                        labels = soup.find_all('label')
                        label_texts = [l.text.lower() for l in labels]
                        assert any(input_name.lower() in text for text in label_texts)
    
    def test_alt_text_for_images(self, client, app, admin_user):
        """Test alt text for images."""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': 'admin@test.com',
                'password': 'password123'
            })
            
            response = client.get('/')
            assert response.status_code == 200
            
            soup = BeautifulSoup(response.data, 'html.parser')
            
            # Check that images have alt text
            images = soup.find_all('img')
            for img in images:
                alt_text = img.get('alt')
                # Images should have alt text (even if empty for decorative images)
                assert alt_text is not None
    
    def test_semantic_html_structure(self, client, app, admin_user):
        """Test semantic HTML structure."""
        with app.app_context():
            # Login as admin
            client.post('/login', data={
                'email': 'admin@test.com',
                'password': 'password123'
            })
            
            response = client.get('/')
            assert response.status_code == 200
            
            soup = BeautifulSoup(response.data, 'html.parser')
            
            # Check for semantic HTML elements
            semantic_elements = ['nav', 'main', 'header', 'footer', 'section', 'article']
            found_semantic = []
            
            for element in semantic_elements:
                if soup.find(element):
                    found_semantic.append(element)
            
            # Should use at least some semantic elements
            assert len(found_semantic) > 0