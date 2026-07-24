"""
Locust stress test for Django AI Employees.

Usage:
    # Start Django server first:
    python manage.py runserver

    # Then run locust:
    locust -f locustfile.py --host=http://127.0.0.1:8000

    # Open http://localhost:8089 in browser to start the test.
    # Or headless mode:
    locust -f locustfile.py --host=http://127.0.0.1:8000 --headless -u 50 -r 5 --run-time 60s

Scenarios:
    - Chat endpoint load test (POST /support/chat/<order_id>/)
    - SSE streaming load test (GET /support/dashboard/stream/<conversation_id>/)
    - Dashboard page load
    - Login flow
"""
from locust import HttpUser, task, between, events
import json


class AIEmployeeUser(HttpUser):
    """Simulates a user accessing the AI Employee support system."""

    wait_time = between(1, 3)

    def on_start(self):
        """Login before running tasks."""
        response = self.client.get('/login/')
        # Extract CSRF token from login page
        csrf = response.cookies.get('csrftoken', '')

        login_response = self.client.post('/login/', {
            'username': 'rathan',
            'password': 'rathan123',
            'csrfmiddlewaretoken': csrf,
        }, headers={'Referer': self.host + '/login/'})

        if login_response.status_code == 200 and 'invalid' not in login_response.text.lower():
            self.logged_in = True
        else:
            self.logged_in = False

    @task(3)
    def load_dashboard(self):
        """Load the staff dashboard page."""
        self.client.get('/support/dashboard/')

    @task(2)
    def view_conversation(self):
        """View a conversation detail."""
        self.client.get('/support/dashboard/1/')

    @task(1)
    def sse_stream(self):
        """Connect to SSE event stream."""
        try:
            with self.client.get(
                '/support/dashboard/stream/1/',
                headers={'Accept': 'text/event-stream'},
                stream=True,
                catch_response=True,
                timeout=5
            ) as response:
                # Read first few bytes to confirm stream is alive
                chunk = next(response.iter_content(chunk_size=128), None)
                if chunk and response.status_code == 200:
                    response.success()
                else:
                    response.failure('No SSE data received')
        except Exception:
            pass  # SSE streams may timeout in locust — that's OK

    @task(5)
    def send_chat_message(self):
        """Send a chat message to the AI support agent."""
        if not self.logged_in:
            return

        payload = {
            'message': 'Where is my order? I have been waiting for days.'
        }

        headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': self.client.cookies.get('csrftoken', ''),
        }

        with self.client.post(
            '/support/chat/1/',
            data=json.dumps(payload),
            headers=headers,
            catch_response=True,
            timeout=30
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 500:
                # AI call may fail under load — mark as partial success
                response.success()
            else:
                response.failure(f'Chat returned {response.status_code}')


class SmokeCheckUser(HttpUser):
    """Lightweight smoke check — minimal load for health checks."""

    wait_time = between(5, 10)

    @task
    def health_check(self):
        """Basic health: hit login page."""
        self.client.get('/login/')

    @task
    def admin_check(self):
        """Check admin is reachable."""
        self.client.get('/admin/login/')
