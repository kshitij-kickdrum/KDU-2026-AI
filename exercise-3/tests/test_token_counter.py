from src.utils.token_counter import TokenCounter


def test_count_tokens_single_text():
    counter = TokenCounter(max_tokens=5)
    assert counter.count_tokens("one two three") == 3


def test_count_question_and_context_tokens():
    counter = TokenCounter(max_tokens=10)
    assert counter.count_question_and_context("what is this", "this is context") == 6


def test_limit_checks():
    counter = TokenCounter(max_tokens=4)
    assert counter.exceeds_limit("one two three four five")
    assert counter.exceeds_combined_limit("one two", "three four five")
