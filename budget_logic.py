import csv
import os
import hashlib


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def ensure_files(users_file: str, records_file: str) -> None:
    if not os.path.exists(users_file):
        with open(users_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["username", "password_hash"])

    if not os.path.exists(records_file):
        with open(records_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["username", "type", "amount", "description"])


def user_exists(users_file: str, username: str) -> bool:
    with open(users_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["username"] == username:
                return True
    return False


def register_user(users_file: str, username: str, password: str) -> bool:
    if not username or not password:
        return False

    if user_exists(users_file, username):
        return False

    password_hash = hash_password(password)

    with open(users_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([username, password_hash])

    return True


def validate_user(users_file: str, username: str, password: str) -> bool:
    password_hash = hash_password(password)

    with open(users_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["username"] == username and row["password_hash"] == password_hash:
                return True
    return False


def add_record(records_file: str, username: str, record_type: str, amount, description: str) -> bool:
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return False

    if amount <= 0:
        return False

    with open(records_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([username, record_type, f"{amount:.2f}", description])

    return True