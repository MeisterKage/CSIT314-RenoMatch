"""US-05 call order: the controller makes the entity calls the sequence diagram shows."""

from app.control.reset_password_controller import ResetPasswordController


class Recorder:
    def __init__(self, entityResult=True):
        self.calls = []
        self.entityResult = entityResult

    def requestPasswordReset(self, email):
        self.calls.append(("entity.requestPasswordReset", email))
        return self.entityResult

    def resetPassword(self, token, newPassword):
        self.calls.append(("entity.resetPassword", token, newPassword))
        return self.entityResult


def controller_with(recorder, monkeypatch):
    controller = ResetPasswordController()
    controller.entity = recorder
    monkeypatch.setattr(
        controller, "sendResetLink", lambda email: recorder.calls.append(("sendResetLink", email))
    )
    return controller


def test_registered_email_calls_entity_then_sendResetLink(monkeypatch):
    rec = Recorder(True)
    assert controller_with(rec, monkeypatch).requestPasswordReset("a@b.co") is True
    assert rec.calls == [("entity.requestPasswordReset", "a@b.co"), ("sendResetLink", "a@b.co")]


def test_unknown_email_calls_entity_only_and_still_returns_true(monkeypatch):
    rec = Recorder(False)
    assert controller_with(rec, monkeypatch).requestPasswordReset("a@b.co") is True
    assert rec.calls == [("entity.requestPasswordReset", "a@b.co")]


def test_valid_password_calls_entity_and_returns_its_result(monkeypatch):
    rec = Recorder(True)
    assert controller_with(rec, monkeypatch).resetPassword("tok", "N3wPassword") is True
    assert rec.calls == [("entity.resetPassword", "tok", "N3wPassword")]
    rec = Recorder(False)
    assert controller_with(rec, monkeypatch).resetPassword("tok", "N3wPassword") is False


def test_invalid_password_returns_false_without_touching_the_entity(monkeypatch):
    rec = Recorder(True)
    assert controller_with(rec, monkeypatch).resetPassword("tok", "bad") is False
    assert rec.calls == []
