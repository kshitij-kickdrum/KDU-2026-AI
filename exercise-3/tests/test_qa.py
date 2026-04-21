from src.services.qa_service import QAService
from src.services.validation import ValidationService
from src.utils.token_counter import TokenCounter


class FakeRoberta:
    def __init__(self, answers):
        self.answers = answers
        self.idx = 0

    def answer_question(self, question, context):
        answer = self.answers[self.idx]
        self.idx = min(self.idx + 1, len(self.answers) - 1)
        return answer


class FakeQwen:
    def compress_context(self, question, context):
        return context[:50]

    def generative_qa(self, question, summary):
        return "Not found in context."


def test_qa_level_1_success():
    service = QAService(
        roberta_model=FakeRoberta([("answer from refined context", 0.9)]),
        qwen_client=FakeQwen(),
        token_counter=TokenCounter(max_tokens=512),
        validation_service=ValidationService(),
        confidence_threshold=0.2,
        max_context_tokens=512,
    )

    result = service.answer_question("What is AI?", "base summary", "refined summary")
    assert result["fallback_level"] == 1
    assert result["answer"] is not None


def test_qa_level_4_error_when_all_fail():
    service = QAService(
        roberta_model=FakeRoberta([("", 0.1), ("", 0.1)]),
        qwen_client=FakeQwen(),
        token_counter=TokenCounter(max_tokens=512),
        validation_service=ValidationService(),
        confidence_threshold=0.2,
        max_context_tokens=512,
    )

    result = service.answer_question("What is AI?", "base summary", "refined summary")
    assert result["fallback_level"] == 4
    assert result["answer"] is None
    assert result["error"] is not None
