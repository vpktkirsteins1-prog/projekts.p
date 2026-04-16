import sqlite3
import tkinter as tk
import pytest

import projekts_ir as appmod


# =========================
# PALĪGFUNKCIJAS
# =========================

def create_user(username, password, blocked=0, active_from="date('now')", active_until=None):
    """
    Izveido lietotāju testu datubāzē un atgriež user_id.
    """
    conn = sqlite3.connect(appmod.DB_FILE)
    cursor = conn.cursor()

    password_hash = appmod.hash_password(password)

    if active_until is None:
        cursor.execute(f"""
            INSERT INTO user (username, password_hash, blocked, active_from, active_until)
            VALUES (?, ?, ?, {active_from}, NULL)
        """, (username, password_hash, blocked))
    else:
        cursor.execute(f"""
            INSERT INTO user (username, password_hash, blocked, active_from, active_until)
            VALUES (?, ?, ?, {active_from}, ?)
        """, (username, password_hash, blocked, active_until))

    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id


def get_category_id(category_name):
    conn = sqlite3.connect(appmod.DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM categories WHERE name = ?", (category_name,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


# =========================
# FIXTURES
# =========================

@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    test_db = tmp_path / "test_budzets.db"
    monkeypatch.setattr(appmod, "DB_FILE", str(test_db))
    appmod.ensure_database()
    return str(test_db)


@pytest.fixture
def app(temp_db, monkeypatch):
    root = tk.Tk()
    root.withdraw()

    monkeypatch.setattr(appmod.messagebox, "showinfo", lambda *args, **kwargs: None)
    monkeypatch.setattr(appmod.messagebox, "showerror", lambda *args, **kwargs: None)
    monkeypatch.setattr(appmod.messagebox, "askyesno", lambda *args, **kwargs: True)

    test_app = appmod.BudgetApp(root)

    yield test_app

    root.destroy()


# =========================
# 1. LIETOTĀJA REĢISTRĀCIJA
# =========================

def test_register_positive(app):
    app.login_username_entry.insert(0, "janis")
    app.login_password_entry.insert(0, "Janis123!")

    app.register()

    conn = sqlite3.connect(appmod.DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM user WHERE username = ?", ("janis",))
    result = cursor.fetchone()
    conn.close()

    assert result is not None
    assert result[0] == "janis"


def test_register_negative_duplicate_username(app):
    create_user("anna", "Anna2024#")

    app.login_username_entry.insert(0, "anna")
    app.login_password_entry.insert(0, "Anna2024#")

    app.register()

    conn = sqlite3.connect(appmod.DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM user WHERE username = ?", ("anna",))
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 1


def test_register_negative_weak_password(app):
    app.login_username_entry.insert(0, "peteris")
    app.login_password_entry.insert(0, "1234")

    app.register()

    conn = sqlite3.connect(appmod.DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM user WHERE username = ?", ("peteris",))
    result = cursor.fetchone()
    conn.close()

    assert result is None


# =========================
# 2. IELOGOŠANĀS
# =========================

def test_login_positive(app):
    user_id = create_user("anna", "Anna2024#")

    app.login_username_entry.insert(0, "anna")
    app.login_password_entry.insert(0, "Anna2024#")

    app.login()

    assert app.current_user_id == user_id
    assert app.current_username == "anna"


def test_login_negative_wrong_password(app):
    create_user("anna", "Anna2024#")

    app.login_username_entry.insert(0, "anna")
    app.login_password_entry.insert(0, "Nepareiza1!")

    app.login()

    assert app.current_user_id is None
    assert app.current_username is None


def test_login_negative_blocked_user(app):
    create_user("blocked_user", "Blocked123!", blocked=1)

    app.login_username_entry.insert(0, "blocked_user")
    app.login_password_entry.insert(0, "Blocked123!")

    app.login()

    assert app.current_user_id is None
    assert app.current_username is None


# =========================
# 3. IERAKSTA PIEVIENOŠANA
# =========================

def test_add_record_positive(app):
    user_id = create_user("toms", "Toms123!")
    app.current_user_id = user_id
    app.current_username = "toms"
    app.show_main_app()

    app.type_var.set("Ienākums")
    app.category_var.set("Alga")
    app.entry_amount.insert(0, "100")
    app.entry_description.insert(0, "Alga")

    app.add_record()

    conn = sqlite3.connect(appmod.DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT records.type, categories.name, records.amount, records.description
        FROM records
        LEFT JOIN categories ON records.category_id = categories.id
        WHERE records.user_id = ?
    """, (user_id,))
    result = cursor.fetchone()
    conn.close()

    assert result is not None
    assert result[0] == "Ienākums"
    assert result[1] == "Alga"
    assert result[2] == 100.0
    assert result[3] == "Alga"


def test_add_record_negative_invalid_amount(app):
    user_id = create_user("toms", "Toms123!")
    app.current_user_id = user_id
    app.current_username = "toms"
    app.show_main_app()

    app.type_var.set("Izdevums")
    app.category_var.set("Pārtika")
    app.entry_amount.insert(0, "abc")
    app.entry_description.insert(0, "Pārtika")

    app.add_record()

    conn = sqlite3.connect(appmod.DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM records WHERE user_id = ?", (user_id,))
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 0
    assert app.status_label.cget("text") == "Summai jābūt skaitlim."


def test_add_record_negative_empty_amount(app):
    user_id = create_user("laura", "Laura123!")
    app.current_user_id = user_id
    app.current_username = "laura"
    app.show_main_app()

    app.type_var.set("Izdevums")
    app.category_var.set("Pārtika")
    app.entry_description.insert(0, "Pārtika")

    app.add_record()

    conn = sqlite3.connect(appmod.DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM records WHERE user_id = ?", (user_id,))
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 0
    assert app.status_label.cget("text") == "Ievadi summu."


# =========================
# 4. BILANCES APRĒĶINS
# =========================

def test_calculate_balance(app):
    user_id = create_user("eva", "Eva12345!")
    app.current_user_id = user_id
    app.current_username = "eva"
    app.show_main_app()

    conn = sqlite3.connect(appmod.DB_FILE)
    cursor = conn.cursor()

    income_category_id = get_category_id("Alga")
    expense_category_id = get_category_id("Pārtika")

    cursor.execute("""
        INSERT INTO records (user_id, category_id, type, amount, description)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, income_category_id, "Ienākums", 200.0, "Alga"))

    cursor.execute("""
        INSERT INTO records (user_id, category_id, type, amount, description)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, expense_category_id, "Izdevums", 50.0, "Pārtika"))

    conn.commit()
    conn.close()

    app.calculate_balance()

    assert app.balance_label.cget("text") == "Bilance: 150.00 €"


# =========================
# 5. VALŪTAS KURSA IEGŪŠANA
# =========================

def test_get_exchange_rate_positive(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def read(self):
            return b'{"result":"success","rates":{"USD":1.10,"GBP":0.85}}'

    monkeypatch.setattr(
        appmod.urllib.request,
        "urlopen",
        lambda *args, **kwargs: FakeResponse()
    )

    rate = appmod.get_exchange_rate("EUR", "USD")

    assert rate == 1.10


def test_get_exchange_rate_negative_missing_currency(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def read(self):
            return b'{"result":"success","rates":{"GBP":0.85}}'

    monkeypatch.setattr(
        appmod.urllib.request,
        "urlopen",
        lambda *args, **kwargs: FakeResponse()
    )

    with pytest.raises(Exception):
        appmod.get_exchange_rate("EUR", "USD")


def test_get_exchange_rate_negative_api_failure(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def read(self):
            return b'{"result":"error"}'

    monkeypatch.setattr(
        appmod.urllib.request,
        "urlopen",
        lambda *args, **kwargs: FakeResponse()
    )

    with pytest.raises(Exception):
        appmod.get_exchange_rate("EUR", "USD")


# =========================
# 6. BILANCES KONVERTĒŠANA
# =========================

def test_convert_balance_positive(app, monkeypatch):
    user_id = create_user("marta", "Marta123!")
    app.current_user_id = user_id
    app.current_username = "marta"
    app.show_main_app()

    conn = sqlite3.connect(appmod.DB_FILE)
    cursor = conn.cursor()

    income_category_id = get_category_id("Alga")
    expense_category_id = get_category_id("Pārtika")

    cursor.execute("""
        INSERT INTO records (user_id, category_id, type, amount, description)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, income_category_id, "Ienākums", 100.0, "Alga"))

    cursor.execute("""
        INSERT INTO records (user_id, category_id, type, amount, description)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, expense_category_id, "Izdevums", 20.0, "Pārtika"))

    conn.commit()
    conn.close()

    monkeypatch.setattr(appmod, "get_exchange_rate", lambda base, target: 2.0)

    app.currency_var.set("USD")
    app.convert_balance()

    assert app.converted_balance_label.cget("text") == "Bilance USD: 160.00"
    assert app.status_label.cget("text") == "Bilance veiksmīgi konvertēta."


def test_convert_balance_negative_api_error(app, monkeypatch):
    user_id = create_user("marta", "Marta123!")
    app.current_user_id = user_id
    app.current_username = "marta"
    app.show_main_app()

    conn = sqlite3.connect(appmod.DB_FILE)
    cursor = conn.cursor()

    income_category_id = get_category_id("Alga")
    cursor.execute("""
        INSERT INTO records (user_id, category_id, type, amount, description)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, income_category_id, "Ienākums", 100.0, "Alga"))

    conn.commit()
    conn.close()

    def fake_rate(base, target):
        raise Exception("API error")

    monkeypatch.setattr(appmod, "get_exchange_rate", fake_rate)

    app.currency_var.set("USD")
    app.convert_balance()

    assert "Neizdevās iegūt valūtas kursu no API" in app.status_label.cget("text")