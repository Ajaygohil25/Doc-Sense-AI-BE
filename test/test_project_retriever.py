from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.rag.retriever import get_project_retriever


def test_project_retriever_filters_by_project_and_user():
    project_id = uuid4()
    user_id = uuid4()
    vector_store = MagicMock()

    with patch("app.rag.retriever.get_vector_store", return_value=vector_store):
        retriever = get_project_retriever(project_id, user_id, k=5)

    assert retriever == vector_store.as_retriever.return_value
    vector_store.as_retriever.assert_called_once_with(
        search_type="similarity",
        search_kwargs={
            "k": 5,
            "filter": {
                "$and": [
                    {"project_id": str(project_id)},
                    {"user_id": str(user_id)},
                ]
            },
        },
    )
