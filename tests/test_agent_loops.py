"""Unit tests for the DeepSeek raw-SDK agent loops (support/agents.py).

Mocking boundary is `support.agents.client.chat.completions.create` — the sole
external network call. Everything downstream (execute_tool, real tool functions,
DB writes) runs for real against the test database.
"""
import pytest
from unittest.mock import patch, call

from support.agents import run_support_agent, run_manager_agent, run_risk_agent
from support.event_queue import DONE
from support.models import AgentLog


@pytest.mark.unit
class TestRunSupportAgent:

    @patch('support.agents.client.chat.completions.create')
    def test_final_reply_no_tool_calls(self, mock_create, conversation, make_completion):
        mock_create.return_value = make_completion(content='Your order is dispatched.')

        result = run_support_agent(
            'Where is my order?', conversation.id, conversation.order.id, conversation.user.id
        )

        assert result == 'Your order is dispatched.'
        logs = AgentLog.objects.filter(conversation=conversation, event_type='final')
        assert logs.count() == 1
        assert logs.first().message == 'Your order is dispatched.'

    @patch('support.agents.client.chat.completions.create')
    def test_one_tool_call_round_then_final_reply(self, mock_create, conversation, order, make_completion):
        mock_create.side_effect = [
            make_completion(tool_calls=[('get_order_details', {'order_id': order.id})]),
            make_completion(content="It's on the way."),
        ]

        result = run_support_agent('Where is my order?', conversation.id, order.id, conversation.user.id)

        assert result == "It's on the way."
        event_types = list(
            AgentLog.objects.filter(conversation=conversation)
            .order_by('id')
            .values_list('event_type', flat=True)
        )
        assert event_types == ['tool_call', 'tool_result', 'final']

    @patch('support.agents.publish')
    @patch('support.agents.client.chat.completions.create')
    def test_publishes_done_sentinel_at_end(self, mock_create, mock_publish, conversation, make_completion):
        mock_create.return_value = make_completion(content='All good.')

        run_support_agent(
            'Where is my order?', conversation.id, conversation.order.id, conversation.user.id
        )

        assert mock_publish.call_args_list[-1] == call(conversation.id, DONE)

    @patch('support.agents.client.chat.completions.create')
    def test_messages_include_conversation_history(self, mock_create, conversation_with_messages, make_completion):
        mock_create.return_value = make_completion(content='Sure thing.')

        run_support_agent(
            'ignored',
            conversation_with_messages.id,
            conversation_with_messages.order.id,
            conversation_with_messages.user.id,
        )

        sent_messages = mock_create.call_args.kwargs['messages']
        roles_and_content = [(m['role'], m['content']) for m in sent_messages]
        assert ('user', 'Where is my order?') in roles_and_content
        assert ('assistant', 'Let me check that for you.') in roles_and_content


@pytest.mark.unit
class TestRunManagerAgent:

    @patch('support.agents.client.chat.completions.create')
    def test_final_decision_no_tool_calls(self, mock_create, conversation, make_completion):
        mock_create.return_value = make_completion(content='Refund approved based on policy.')

        result = run_manager_agent('Customer User ID: 1\nComplaint: damaged item', conversation.id)

        assert result == 'Refund approved based on policy.'
        logs = AgentLog.objects.filter(conversation=conversation, event_type='manager')
        assert logs.count() == 2
        assert 'Decision:' in logs.order_by('id').last().message

    @patch('support.agents.execute_tool')
    @patch('support.agents.client.chat.completions.create')
    def test_one_tool_call_round_then_final_decision(
        self, mock_create, mock_execute_tool, conversation, user, make_completion
    ):
        mock_execute_tool.return_value = 'Risk Level: LOW'
        mock_create.side_effect = [
            make_completion(tool_calls=[('assess_fraud_risk', {'user_id': user.id})]),
            make_completion(content='Approved.'),
        ]

        result = run_manager_agent(f'Customer User ID: {user.id}', conversation.id)

        assert result == 'Approved.'
        assert AgentLog.objects.filter(conversation=conversation, event_type='manager').count() == 3


@pytest.mark.unit
class TestRunRiskAgent:

    @patch('support.agents.client.chat.completions.create')
    def test_final_verdict_no_tool_calls(self, mock_create, conversation, user, make_completion):
        mock_create.return_value = make_completion(content='Risk Level: LOW. Recommendation: approve.')

        result = run_risk_agent(user.id, conversation.id)

        assert result == 'Risk Level: LOW. Recommendation: approve.'
        logs = AgentLog.objects.filter(conversation=conversation, event_type='risk')
        assert logs.count() == 2

    @patch('support.agents.client.chat.completions.create')
    def test_one_tool_call_round_then_final_verdict(self, mock_create, conversation, user, make_completion):
        mock_create.side_effect = [
            make_completion(tool_calls=[('get_customer_risk_profile', {'user_id': user.id})]),
            make_completion(content='Risk Level: LOW.'),
        ]

        result = run_risk_agent(user.id, conversation.id)

        assert result == 'Risk Level: LOW.'
        assert AgentLog.objects.filter(conversation=conversation, event_type='risk').count() == 3


@pytest.mark.unit
class TestAgentEscalationChain:
    """Drives the real recursive support -> manager -> risk chain, mocking only
    the DeepSeek client boundary."""

    def _side_effects(self, user, make_completion):
        case_summary = f'Customer User ID: {user.id}\nComplaint: damaged item'
        return [
            make_completion(tool_calls=[('escalate_to_manager', {'case_summary': case_summary})]),
            make_completion(tool_calls=[('assess_fraud_risk', {'user_id': user.id})]),
            make_completion(content='Risk Level: LOW. Key Signals: none. Recommendation: approve.'),
            make_completion(content='Refund approved based on low risk.'),
            make_completion(content='Good news, your refund has been approved.'),
        ]

    @patch('support.agents.client.chat.completions.create')
    def test_support_escalates_to_manager_which_consults_risk_agent(
        self, mock_create, conversation, order, user, make_completion
    ):
        mock_create.side_effect = self._side_effects(user, make_completion)

        result = run_support_agent('My item arrived damaged', conversation.id, order.id, user.id)

        assert result == 'Good news, your refund has been approved.'
        assert AgentLog.objects.filter(conversation=conversation, event_type='risk').count() == 2
        assert AgentLog.objects.filter(conversation=conversation, event_type='manager').count() == 3
        support_event_types = list(
            AgentLog.objects.filter(
                conversation=conversation, event_type__in=['tool_call', 'tool_result', 'final']
            )
            .order_by('id')
            .values_list('event_type', flat=True)
        )
        assert support_event_types == ['tool_call', 'tool_result', 'final']

    @patch('support.agents.publish')
    @patch('support.agents.client.chat.completions.create')
    def test_done_published_exactly_once(
        self, mock_create, mock_publish, conversation, order, user, make_completion
    ):
        mock_create.side_effect = self._side_effects(user, make_completion)

        run_support_agent('My item arrived damaged', conversation.id, order.id, user.id)

        done_calls = [c for c in mock_publish.call_args_list if c == call(conversation.id, DONE)]
        assert len(done_calls) == 1
        assert mock_publish.call_args_list[-1] == call(conversation.id, DONE)
