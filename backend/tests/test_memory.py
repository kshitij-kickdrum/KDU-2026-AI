from app.memory.session_memory import add_turn, clear_session, create_session, get_history, list_sessions


def test_history_empty_for_new_session():
    assert get_history("sess_new") == []


def test_create_session_adds_empty_session_summary():
    create_session("sess_new", "u_001")
    sessions = list_sessions("u_001")
    assert len(sessions) == 1
    assert sessions[0]["session_id"] == "sess_new"
    assert sessions[0]["title"] == "New chat"
    assert sessions[0]["message_count"] == 0


def test_add_turn_stores_both_messages():
    add_turn("sess_1", "u_001", "Hello", {"answer": "Hi there!", "follow_up": None})
    history = get_history("sess_1")
    assert len(history) == 2
    assert history[0] == {"role": "human", "content": "Hello"}
    assert history[1] == {"role": "ai", "content": '{"answer": "Hi there!", "follow_up": null}'}


def test_multiple_turns_accumulate():
    add_turn("sess_1", "u_001", "Turn 1", {"answer": "Response 1", "follow_up": None})
    add_turn("sess_1", "u_001", "Turn 2", {"answer": "Response 2", "follow_up": None})
    assert len(get_history("sess_1")) == 4


def test_clear_session_empties_history():
    add_turn("sess_1", "u_001", "Hello", {"answer": "Hi", "follow_up": None})
    clear_session("sess_1")
    assert get_history("sess_1") == []


def test_sessions_are_isolated():
    add_turn("sess_a", "u_001", "Hello from A", {"answer": "Response A", "follow_up": None})
    add_turn("sess_b", "u_001", "Hello from B", {"answer": "Response B", "follow_up": None})
    assert len(get_history("sess_a")) == 2
    assert len(get_history("sess_b")) == 2
    clear_session("sess_a")
    assert get_history("sess_a") == []
    assert len(get_history("sess_b")) == 2


def test_history_endpoint_returns_correct_shape(client):
    add_turn("sess_1", "u_001", "What is the weather?", '{"temperature": "32C"}')
    response = client.get("/api/v1/history?session_id=sess_1&user_id=u_001")
    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == "sess_1"
    assert body["message_count"] == 2
    assert len(body["messages"]) == 2


def test_delete_session_endpoint(client):
    add_turn("sess_1", "u_001", "Hello", {"answer": "Hi", "follow_up": None})
    response = client.request(
        "DELETE",
        "/api/v1/session",
        json={"user_id": "u_001", "session_id": "sess_1"},
    )
    assert response.status_code == 200
    assert get_history("sess_1") == []


def test_list_sessions_returns_summary_data():
    add_turn("sess_1", "u_001", "What is the weather in Delhi?", '{"temperature": "32C", "summary": "Sunny"}')
    sessions = list_sessions("u_001")
    assert len(sessions) == 1
    assert sessions[0]["session_id"] == "sess_1"
    assert sessions[0]["title"] == "What is the weather in Delhi?"
    assert sessions[0]["preview"] == "32C - Sunny"
    assert sessions[0]["message_count"] == 2


def test_sessions_endpoint_returns_user_scoped_recents(client):
    add_turn("sess_1", "u_001", "Hello", '{"answer": "Hi"}')
    add_turn("sess_2", "u_002", "Hello", '{"answer": "Hi from elsewhere"}')
    response = client.get("/api/v1/sessions?user_id=u_001")
    assert response.status_code == 200
    body = response.json()
    assert len(body["sessions"]) == 1
    assert body["sessions"][0]["session_id"] == "sess_1"


def test_create_session_endpoint(client):
    response = client.post(
        "/api/v1/session",
        json={"user_id": "u_001", "session_id": "sess_new"},
    )
    assert response.status_code == 200
    body = client.get("/api/v1/sessions?user_id=u_001").json()
    assert body["sessions"][0]["session_id"] == "sess_new"


def test_list_sessions_uses_plain_answer_preview_for_general_chat():
    add_turn("sess_1", "u_001", "what is a cow?", {"answer": "A cow is a domesticated animal.", "follow_up": None})
    sessions = list_sessions("u_001")
    assert sessions[0]["preview"] == "A cow is a domesticated animal."
