from src.services.validation import ValidationService


def test_validate_summary_success():
    validator = ValidationService(min_summary_words=5)
    summary = "This is sentence one with details. This is sentence two with more details."
    result = validator.validate_summary(summary, input_word_count=60)
    assert result.is_valid


def test_validate_summary_repetition_fails():
    validator = ValidationService(min_summary_words=3)
    summary = "word word word word. Another sentence exists here."
    result = validator.validate_summary(summary, input_word_count=20)
    assert not result.is_valid
    assert any("repeated" in error for error in result.errors)


def test_validate_qa_confidence_threshold():
    validator = ValidationService()
    assert validator.validate_qa_confidence(0.2, threshold=0.2)
    assert not validator.validate_qa_confidence(0.19, threshold=0.2)
