"""Unit tests for the active LangChain/LangGraph agent orchestration
(support/langchain_agents.py).

Mocking boundary is `support.langchain_agents.create_agent` — the outermost call
into LangGraph's agent-execution machinery, mirroring the same conceptual
boundary used for the raw-SDK path (client.chat.completions.create).

Known limitation: the inner @tool / @wrap_tool_call closures (escalate_to_manager,
assess_fraud_risk, and the three log_*_tool_calls_middleware functions) only run
when the real LangGraph loop decides to call a tool, which can't happen once
create_agent itself is mocked out. Those closure bodies stay uncovered here.
"""
import pytest
from types import SimpleNamespace
from unittest.mock import patch, call

from support.langchain_agents import (
    run_support_agent_langchain,
    run_manager_agent_langchain,
    run_risk_agent_langchain,
    checkpointer,
)
from support.agents import SUPPORT_SYSTEM_PROMPT, MANAGER_SYSTEM_PROMPT, RISK_SYSTEM_PROMPT
from support.event_queue import DONE
from support.models import AgentLog


def _agent_mock(mock_create_agent, content):
    """Wire mock_create_agent so calling it returns an agent whose .invoke()
    returns a LangGraph-shaped result with the given final message content."""
    agent = mock_create_agent.return_value
    agent.invoke.return_value = {"messages": [SimpleNamespace(content=content)]}
    return agent


@pytest.mark.unit
class TestRunSupportAgentLangchain:

    @patch('support.langchain_agents.create_agent')
    def test_returns_final_reply_and_logs(self, mock_create_agent, conversation, order, user):
        _agent_mock(mock_create_agent, 'Your order is dispatched.')

        result = run_support_agent_langchain('Where is my order?', conversation.id, order.id, user.id)

        assert result == 'Your order is dispatched.'
        kwargs = mock_create_agent.call_args.kwargs
        assert kwargs['system_prompt'] == SUPPORT_SYSTEM_PROMPT
        assert kwargs['checkpointer'] is checkpointer
        assert len(kwargs['tools']) == 5

        logs = AgentLog.objects.filter(conversation=conversation, event_type='final')
        assert logs.count() == 1
        assert logs.first().message == 'Your order is dispatched.'

    @patch('support.langchain_agents.publish')
    @patch('support.langchain_agents.create_agent')
    def test_invoke_called_with_thread_id_and_contextual_message(
        self, mock_create_agent, mock_publish, conversation, order, user
    ):
        agent = _agent_mock(mock_create_agent, 'On its way.')

        run_support_agent_langchain('Where is my order?', conversation.id, order.id, user.id)

        invoke_args = agent.invoke.call_args
        assert invoke_args.kwargs['config'] == {"configurable": {"thread_id": str(conversation.id)}}
        contextual_message = invoke_args.args[0]['messages'][0]['content']
        assert f'Order #{order.id}' in contextual_message
        assert 'Where is my order?' in contextual_message

        assert mock_publish.call_args_list[-1] == call(conversation.id, DONE)


@pytest.mark.unit
class TestRunManagerAgentLangchain:

    @patch('support.langchain_agents.create_agent')
    def test_returns_decision_and_logs(self, mock_create_agent, conversation, user):
        _agent_mock(mock_create_agent, 'Refund approved.')

        result = run_manager_agent_langchain(f'Customer User ID: {user.id}', conversation.id)

        assert result == 'Refund approved.'
        logs = AgentLog.objects.filter(conversation=conversation, event_type='manager')
        assert logs.count() == 2

    @patch('support.langchain_agents.publish')
    @patch('support.langchain_agents.create_agent')
    def test_tools_kwarg_is_assess_fraud_risk_only_and_no_done_published(
        self, mock_create_agent, mock_publish, conversation, user
    ):
        _agent_mock(mock_create_agent, 'Approved.')

        run_manager_agent_langchain(f'Customer User ID: {user.id}', conversation.id)

        tools = mock_create_agent.call_args.kwargs['tools']
        assert len(tools) == 1
        assert mock_create_agent.call_args.kwargs['system_prompt'] == MANAGER_SYSTEM_PROMPT
        assert call(conversation.id, DONE) not in mock_publish.call_args_list


@pytest.mark.unit
class TestRunRiskAgentLangchain:

    @patch('support.langchain_agents.create_agent')
    def test_returns_verdict_and_logs(self, mock_create_agent, conversation, user):
        _agent_mock(mock_create_agent, 'Risk Level: LOW.')

        result = run_risk_agent_langchain(user.id, conversation.id)

        assert result == 'Risk Level: LOW.'
        logs = AgentLog.objects.filter(conversation=conversation, event_type='risk')
        assert logs.count() == 2

    @patch('support.langchain_agents.create_agent')
    def test_system_prompt_is_risk_prompt(self, mock_create_agent, conversation, user):
        _agent_mock(mock_create_agent, 'Risk Level: LOW.')

        run_risk_agent_langchain(user.id, conversation.id)

        assert mock_create_agent.call_args.kwargs['system_prompt'] == RISK_SYSTEM_PROMPT
        assert len(mock_create_agent.call_args.kwargs['tools']) == 1
