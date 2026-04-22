from app.services.usage_tracker import UsageRecord, UsageTracker


def test_usage_tracker_cost_and_stats():
    tracker = UsageTracker()
    tracker.log_usage(
        UsageRecord(
            session_id="sess_unit_1",
            request_type="chat",
            input_tokens=100,
            output_tokens=50,
            tool_tokens=10,
            provider="openai",
            model="gpt-4o-mini",
            tools_used=["calculate"],
        )
    )
    stats = tracker.get_session_stats("sess_unit_1")
    assert stats["requests_count"] == 1
    assert stats["total_tokens"] == 160
    assert stats["total_cost"] > 0

