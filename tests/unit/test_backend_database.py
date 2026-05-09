from backend import database


def test_get_db_yields_session_and_closes(mocker):
    fake_session = mocker.Mock()
    mocker.patch.object(database, "SessionLocal", return_value=fake_session)

    gen = database.get_db()
    yielded = next(gen)
    assert yielded is fake_session

    try:
        next(gen)
    except StopIteration:
        pass

    fake_session.close.assert_called_once()
    fake_session.rollback.assert_not_called()


def test_get_db_rolls_back_on_exception_and_closes(mocker):
    fake_session = mocker.Mock()
    mocker.patch.object(database, "SessionLocal", return_value=fake_session)

    gen = database.get_db()
    next(gen)

    try:
        gen.throw(RuntimeError("boom"))
    except RuntimeError:
        pass

    fake_session.rollback.assert_called_once()
    fake_session.close.assert_called_once()
