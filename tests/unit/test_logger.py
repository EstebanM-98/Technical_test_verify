import logging

import logger as logger_module


def test_get_logger_configures_handlers_and_registry(tmp_path, monkeypatch):
    monkeypatch.setattr(logger_module, "_LOG_DIR", str(tmp_path / "logs"))
    logger_module._configured_loggers.clear()

    lg = logger_module.get_logger("unit.test.logger", "unit.log")

    assert isinstance(lg, logging.Logger)
    assert (tmp_path / "logs").exists()
    assert lg.propagate is False
    assert lg.level == logging.DEBUG

    stream_handlers = [
        h
        for h in lg.handlers
        if isinstance(h, logging.StreamHandler)
        and not isinstance(h, logging.handlers.RotatingFileHandler)
    ]
    file_handlers = [h for h in lg.handlers if isinstance(h, logging.handlers.RotatingFileHandler)]

    assert len(stream_handlers) == 1
    assert len(file_handlers) == 1
    assert stream_handlers[0].level == logging.INFO
    assert file_handlers[0].level == logging.DEBUG


def test_get_logger_repeated_calls_do_not_duplicate_handlers(tmp_path, monkeypatch):
    monkeypatch.setattr(logger_module, "_LOG_DIR", str(tmp_path / "logs"))
    logger_module._configured_loggers.clear()

    l1 = logger_module.get_logger("unit.test.same", "x.log")
    handlers_before = len(l1.handlers)

    l2 = logger_module.get_logger("unit.test.same", "x.log")

    assert l1 is l2
    assert len(l2.handlers) == handlers_before
