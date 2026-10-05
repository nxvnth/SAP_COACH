"""Safe, actionable errors for the learner; never include provider payloads."""


# Carry a stable error code, safe display message and HTTP status across the service/server boundary.
class CoachError(Exception):
    def __init__(self, code, message, status=502):
        super().__init__(message)
        self.code = code
        self.status = status


# Translate provider-client failures into actionable UI errors without exposing raw API responses.
def provider_error(error):
    message = str(error)
    if "budget/call cap" in message:
        return CoachError(
            "budget_exhausted",
            "The local API budget or call limit was reached. Review coach/config.json and the usage ledger before increasing it.",
            429,
        )
    if "missing" in message and "AIAPIKEY" in message:
        return CoachError(
            "missing_key", "Add AIAPIKEY to the project root .env before asking a question.", 503
        )
    if "attempted without" in message:
        return CoachError(
            "unresolved_request",
            "This request previously failed after submission. Its usage record needs review before retrying.",
        )
    if "JSON" in message or "Incomplete/refused" in message:
        return CoachError(
            "invalid_model_output",
            "The model did not return a complete structured answer. No automatic retry was made.",
        )
    return CoachError(
        "provider_unavailable",
        "The answer provider could not complete the request. No automatic retry was made.",
    )
