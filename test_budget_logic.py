from budget_logic import (
    ensure_files,
    register_user,
    validate_user,
    add_record,
)


def test_register_user_positive(tmp_path):
    users_file = tmp_path / "users.csv"
    records_file = tmp_path / "records.csv"
    ensure_files(str(users_file), str(records_file))

    result = register_user(str(users_file), "janis", "1234")

    assert result is True


def test_register_user_negative_duplicate(tmp_path):
    users_file = tmp_path / "users.csv"
    records_file = tmp_path / "records.csv"
    ensure_files(str(users_file), str(records_file))

    register_user(str(users_file), "janis", "1234")
    result = register_user(str(users_file), "janis", "5678")

    assert result is False


def test_login_positive(tmp_path):
    users_file = tmp_path / "users.csv"
    records_file = tmp_path / "records.csv"
    ensure_files(str(users_file), str(records_file))

    register_user(str(users_file), "anna", "abcd")
    result = validate_user(str(users_file), "anna", "abcd")

    assert result is True


def test_login_negative_wrong_password(tmp_path):
    users_file = tmp_path / "users.csv"
    records_file = tmp_path / "records.csv"
    ensure_files(str(users_file), str(records_file))

    register_user(str(users_file), "anna", "abcd")
    result = validate_user(str(users_file), "anna", "0000")

    assert result is False


def test_add_record_positive(tmp_path):
    users_file = tmp_path / "users.csv"
    records_file = tmp_path / "records.csv"
    ensure_files(str(users_file), str(records_file))

    result = add_record(str(records_file), "kristofers", "Ienākums", 100, "Alga")

    assert result is True


def test_add_record_negative_invalid_amount(tmp_path):
    users_file = tmp_path / "users.csv"
    records_file = tmp_path / "records.csv"
    ensure_files(str(users_file), str(records_file))

    result = add_record(str(records_file), "kristofers", "Izdevums", "abc", "Pārtika")

    assert result is False