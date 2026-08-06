"""Unit tests for the ChromaDB RAG module (support/rag.py).

Only the `collection` object's `.add`/`.query` methods and the filesystem/PDF
reads are mocked — the real embedding function is never invoked, so these tests
never touch the network or download an embedding model.
"""
import pytest
from unittest.mock import patch, MagicMock

from support.rag import chunk_text, load_documents, search_knowledge_base


@pytest.mark.unit
class TestChunkText:

    def test_splits_long_text_into_multiple_chunks(self):
        text = ' '.join(['word'] * 200)
        chunks = chunk_text(text, chunk_size=50)
        assert len(chunks) > 1
        assert ' '.join(chunks).split() == text.split()

    def test_short_text_returns_single_chunk(self):
        assert chunk_text('short text', chunk_size=500) == ['short text']

    def test_empty_string_returns_empty_list(self):
        assert chunk_text('') == []

    def test_default_chunk_size_is_500(self):
        text = ' '.join(['word'] * 200)
        assert chunk_text(text) == chunk_text(text, chunk_size=500)


@pytest.mark.unit
class TestLoadDocuments:

    @patch('support.rag.collection.add')
    @patch('support.rag.PdfReader')
    @patch('support.rag.os.listdir')
    def test_loads_pdf_files_and_calls_collection_add(self, mock_listdir, mock_pdf_reader, mock_add):
        mock_listdir.return_value = ['refund_policy.pdf', 'readme.txt']
        page = MagicMock()
        page.extract_text.return_value = 'Refund text ' * 100
        mock_pdf_reader.return_value = MagicMock(pages=[page])

        load_documents()

        mock_pdf_reader.assert_called_once()
        mock_add.assert_called_once()
        _, kwargs = mock_add.call_args
        assert len(kwargs['documents']) > 0
        assert all(i.startswith('refund_policy.pdf_') for i in kwargs['ids'])

    @patch('support.rag.collection.add')
    @patch('support.rag.os.listdir')
    def test_no_pdf_files_skips_collection_add(self, mock_listdir, mock_add):
        mock_listdir.return_value = []

        load_documents()

        mock_add.assert_not_called()


@pytest.mark.unit
class TestSearchKnowledgeBase:

    @patch('support.rag.collection.query')
    def test_returns_joined_chunks_when_results_found(self, mock_query):
        mock_query.return_value = {'documents': [['chunk one', 'chunk two']]}

        result = search_knowledge_base('refund policy')

        assert result == 'chunk one\n\nchunk two'
        mock_query.assert_called_once_with(query_texts=['refund policy'], n_results=3)

    @patch('support.rag.collection.query')
    def test_returns_fallback_message_when_no_results(self, mock_query):
        mock_query.return_value = {'documents': [[]]}

        result = search_knowledge_base('nonexistent topic')

        assert result == 'No relevant information found in company documents.'
