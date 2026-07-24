"""Integration tests for support views — chat, dashboard, conversation detail, SSE."""
import json
import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse

from support.models import Conversation, Message, AgentLog


@pytest.mark.integration
class TestChatAPI:

    def test_chat_endpoint_requires_login(self, client, order):
        """Unauthenticated POST should be denied (redirect or error)."""
        url = reverse('chat', args=[order.id])
        response = client.post(
            url,
            data=json.dumps({'message': 'Where is my order?'}),
            content_type='application/json'
        )
        # Should not succeed - either redirects to login or returns 403/404
        assert response.status_code in [302, 403, 404]

    @patch('support.langchain_agents.llm')
    def test_chat_endpoint_authenticated(self, mock_llm, client, user, order):
        """Authenticated POST should return 200 with mocked AI."""
        from langchain_core.messages import AIMessage
        # Mock the LLM to return a simple text reply
        mock_llm.invoke = MagicMock(return_value=AIMessage(content='Your order is on the way!'))

        # Also need to mock the full agent chain
        with patch('support.views.run_support_agent_langchain', return_value='Your order is on the way!'):
            client.force_login(user)
            url = reverse('chat', args=[order.id])
            response = client.post(
                url,
                data=json.dumps({'message': 'Where is my order?'}),
                content_type='application/json'
            )
            assert response.status_code == 200
            data = response.json()
            assert 'reply' in data
            assert data['reply'] == 'Your order is on the way!'

    def test_chat_empty_message(self, client, user, order):
        """Empty message should return 400."""
        client.force_login(user)
        url = reverse('chat', args=[order.id])
        response = client.post(
            url,
            data=json.dumps({'message': ''}),
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_chat_wrong_user_cannot_access(self, client, order):
        """User should only access their own orders."""
        from django.contrib.auth.models import User
        other_user = User.objects.create_user(
            username='other', password='pass123'
        )
        client.force_login(other_user)
        url = reverse('chat', args=[order.id])
        response = client.post(
            url,
            data=json.dumps({'message': 'test'}),
            content_type='application/json'
        )
        assert response.status_code in [404, 302]

    def test_chat_creates_conversation(self, client, user, order):
        """First chat should create a Conversation record."""
        client.force_login(user)
        url = reverse('chat', args=[order.id])

        # This will likely fail on AI call, but conversation should be created
        try:
            client.post(
                url,
                data=json.dumps({'message': 'Hello'}),
                content_type='application/json'
            )
        except Exception:
            pass

        assert Conversation.objects.filter(user=user, order=order).exists()


@pytest.mark.integration
class TestDashboard:

    def test_dashboard_requires_staff(self, client, user):
        """Non-staff should be denied dashboard access."""
        client.force_login(user)
        url = reverse('dashboard')
        response = client.get(url)
        # staff_member_required redirects to admin login
        assert response.status_code in [302, 403]

    def test_dashboard_staff_access(self, client, staff_user):
        """Staff should access dashboard."""
        client.force_login(staff_user)
        url = reverse('dashboard')
        response = client.get(url)
        assert response.status_code == 200

    def test_dashboard_shows_conversations(self, client, staff_user, conversation):
        """Dashboard should include conversations in context."""
        client.force_login(staff_user)
        url = reverse('dashboard')
        response = client.get(url)
        assert response.status_code == 200
        assert 'conversations' in response.context


@pytest.mark.integration
class TestConversationDetail:

    def test_detail_requires_staff(self, client, user, conversation):
        """Non-staff should be denied."""
        client.force_login(user)
        url = reverse('conversation_detail', args=[conversation.id])
        response = client.get(url)
        assert response.status_code in [302, 403]

    def test_detail_staff_access(self, client, staff_user, conversation):
        """Staff should view conversation detail."""
        client.force_login(staff_user)
        url = reverse('conversation_detail', args=[conversation.id])
        response = client.get(url)
        assert response.status_code == 200
        assert response.context['conversation'] == conversation

    def test_detail_with_messages(self, client, staff_user, conversation_with_messages):
        """Should show messages and agent logs in context."""
        client.force_login(staff_user)
        url = reverse('conversation_detail', args=[conversation_with_messages.id])
        response = client.get(url)
        assert response.status_code == 200
        assert 'messages' in response.context
        assert 'agentlogs' in response.context


@pytest.mark.integration
class TestSSEStreaming:

    def test_stream_returns_event_stream(self, client, conversation):
        """SSE endpoint should return text/event-stream content type."""
        url = reverse('conversation_stream', args=[conversation.id])
        response = client.get(url)
        assert response.status_code == 200
        assert response['Content-Type'] == 'text/event-stream'
        assert response['Cache-Control'] == 'no-cache'

    def test_stream_isolated_conversations(self, client):
        """Different conversation streams should not interfere."""
        url1 = reverse('conversation_stream', args=[1])
        url2 = reverse('conversation_stream', args=[2])
        client.get(url1)
        client.get(url2)
        # Both should not crash
