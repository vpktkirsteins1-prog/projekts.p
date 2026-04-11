import sqlite3
import tkinter as tk
import pytest

import projekts_ir as appmod


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
# 1. REĢISTRĀCIJA
# =========================

def test_register_positive(app):
    app.login_username_entry.insert(0, "janis")
    app.login_password_entry.insert(0, "1234")

    app.register()

    conn = sqlite3.connect(appmod.DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE username = ?", ("janis",))
    result = cursor.fetchone()
    conn.close()

    assert result is not None
    assert result[0] == "janis"


def test_register_negative_duplicate(app):
    conn = sqlite3.connect(appmod.DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        ("janis", appmod.hash_password("1234"))
    )
    conn.commit()
    conn.close()

    app.login_username_entry.insert(0, "janis")
    app.login_password_entry.insert(0, "5678")

    app.register()

    conn = sqlite3.connect(appmod.DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", ("janis",))
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 1


# =========================
# 2. IELOGOŠANĀS
# =========================

def test_login_positive(app):
    conn = sqlite3.connect(appmod.DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        ("anna", appmod.hash_password("abcd"))
    )
    conn.commit()
    conn.close()

    app.login_username_entry.insert(0, "anna")
    app.login_password_entry.insert(0, "abcd")

    app.login()

    assert app.current_user == "anna"


def test_login_negative_wrong_password(app):
    conn = sqlite3.connect(appmod.DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        ("anna", appmod.hash_password("abcd"))
    )
    conn.commit()
    conn.close()

    app.login_username_entry.insert(0, "anna")
    app.login_password_entry.insert(0, "0000")

    app.login()

    assert app.current_user is None


# =========================
# 3. IERAKSTA PIEVIENOŠANA
# =========================

def test_add_record_positive(app):
    app.current_user = "toms"
    app.show_main_app()

    app.type_var.set("Ienākums")
    app.entry_amount.insert(0, "100")
    app.entry_description.insert(0, "Alga")

    app.add_record()

    conn = sqlite3.connect(appmod.DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT type, amount, description FROM records WHERE username = ?",
        ("toms",)
    )
    result = cursor.fetchone()
    conn.close()

    assert result is not None
    assert result[0] == "Ienākums"
    assert result[1] == 100.0
    assert result[2] == "Alga"


def test_add_record_negative_invalid_amount(app):
    app.current_user = "toms"
    app.show_main_app()

    app.type_var.set("Izdevums")
    app.entry_amount.insert(0, "abc")
    app.entry_description.insert(0, "Pārtika")

    app.add_record()

    conn = sqlite3.connect(appmod.DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM records WHERE username = ?", ("toms",))
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 0
    assert app.status_label.cget("text") == "Summai jābūt skaitlim."


# =========================
# 4. BILANCES APRĒĶINS
# =========================

def test_calculate_balance(app):
    app.current_user = "eva"
    app.show_main_app()

    conn = sqlite3.connect(appmod.DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO records (username, type, amount, description) VALUES (?, ?, ?, ?)",
        ("eva", "Ienākums", 200.0, "Alga")
    )
    cursor.execute(
        "INSERT INTO records (username, type, amount, description) VALUES (?, ?, ?, ?)",
        ("eva", "Izdevums", 50.0, "Pārtika")
    )
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

    monkeypatch.setattr(appmod.urllib.request, "urlopen", lambda *args, **kwargs: FakeResponse())

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

    monkeypatch.setattr(appmod.urllib.request, "urlopen", lambda *args, **kwargs: FakeResponse())

    with pytest.raises(Exception):
        appmod.get_exchange_rate("EUR", "USD")


# =========================
# 6. BILANCES KONVERTĒŠANA
# =========================

def test_convert_balance_positive(app, monkeypatch):
    app.current_user = "marta"
    app.show_main_app()

    conn = sqlite3.connect(appmod.DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO records (username, type, amount, description) VALUES (?, ?, ?, ?)",
        ("marta", "Ienākums", 100.0, "Alga")
    )
    cursor.execute(
        "INSERT INTO records (username, type, amount, description) VALUES (?, ?, ?, ?)",
        ("marta", "Izdevums", 20.0, "Pārtika")
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(appmod, "get_exchange_rate", lambda base, target: 2.0)

    app.currency_var.set("USD")
    app.convert_balance()

    assert app.converted_balance_label.cget("text") == "Bilance USD: 160.00"
    assert app.status_label.cget("text") == "Bilance veiksmīgi konvertēta."


def test_convert_balance_negative_api_error(app, monkeypatch):
    app.current_user = "marta"
    app.show_main_app()

    conn = sqlite3.connect(appmod.DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO records (username, type, amount, description) VALUES (?, ?, ?, ?)",
        ("marta", "Ienākums", 100.0, "Alga")
    )
    conn.commit()
    conn.close()

    def fake_rate(base, target):
        raise Exception("API error")

    monkeypatch.setattr(appmod, "get_exchange_rate", fake_rate)

    app.currency_var.set("USD")
    app.convert_balance()

    assert "Neizdevās iegūt valūtas kursu no API" in app.status_label.cget("text")