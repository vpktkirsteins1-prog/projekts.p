import tkinter as tk
from tkinter import ttk, messagebox
import csv
import os
import hashlib

USERS_FILE = "users.csv"
RECORDS_FILE = "records.csv"


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def ensure_files():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["username", "password_hash"])

    if not os.path.exists(RECORDS_FILE):
        with open(RECORDS_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["username", "type", "amount", "description"])


ensure_files()


class BudgetApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Personīgā budžeta aplikācija")
        self.root.geometry("900x550")
        self.root.configure(bg="#f4f6f8")

        self.current_user = None
        self.table = None
        self.balance_label = None
        self.status_label = None
        self.entry_amount = None
        self.entry_description = None
        self.type_var = None

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Treeview", rowheight=28, font=("Arial", 11))
        self.style.configure("Treeview.Heading", font=("Arial", 11, "bold"))
        self.style.configure("TButton", font=("Arial", 11))
        self.style.configure("TLabel", font=("Arial", 11))

        self.show_login_screen()

    def clear_root(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_login_screen(self):
        self.clear_root()

        container = tk.Frame(self.root, bg="#f4f6f8")
        container.pack(expand=True)

        card = tk.Frame(container, bg="white", bd=1, relief="solid", padx=30, pady=30)
        card.pack()

        tk.Label(
            card,
            text="Personīgā budžeta aplikācija",
            font=("Arial", 20, "bold"),
            bg="white",
            fg="#1f2937"
        ).grid(row=0, column=0, columnspan=2, pady=(0, 20))

        tk.Label(card, text="Lietotājvārds", bg="white", font=("Arial", 11)).grid(
            row=1, column=0, sticky="w", pady=5
        )
        self.login_username_entry = ttk.Entry(card, width=30)
        self.login_username_entry.grid(row=1, column=1, pady=5)

        tk.Label(card, text="Parole", bg="white", font=("Arial", 11)).grid(
            row=2, column=0, sticky="w", pady=5
        )
        self.login_password_entry = ttk.Entry(card, width=30, show="*")
        self.login_password_entry.grid(row=2, column=1, pady=5)

        ttk.Button(card, text="Ielogoties", command=self.login).grid(
            row=3, column=0, pady=15, padx=5
        )
        ttk.Button(card, text="Reģistrēties", command=self.register).grid(
            row=3, column=1, pady=15, padx=5
        )

    def user_exists(self, username):
        with open(USERS_FILE, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["username"] == username:
                    return True
        return False

    def validate_user(self, username, password):
        password_hash = hash_password(password)

        with open(USERS_FILE, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["username"] == username and row["password_hash"] == password_hash:
                    return True
        return False

    def register(self):
        username = self.login_username_entry.get().strip()
        password = self.login_password_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Kļūda", "Aizpildi lietotājvārdu un paroli.")
            return

        if len(password) < 4:
            messagebox.showerror("Kļūda", "Parolei jābūt vismaz 4 simbolus garai.")
            return

        if self.user_exists(username):
            messagebox.showerror("Kļūda", "Šāds lietotājs jau eksistē.")
            return

        password_hash = hash_password(password)

        with open(USERS_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([username, password_hash])

        messagebox.showinfo("Veiksmīgi", "Lietotājs reģistrēts. Tagad vari ielogoties.")
        self.login_username_entry.delete(0, tk.END)
        self.login_password_entry.delete(0, tk.END)

    def login(self):
        username = self.login_username_entry.get().strip()
        password = self.login_password_entry.get().strip()

        if self.validate_user(username, password):
            self.current_user = username
            self.show_main_app()
        else:
            messagebox.showerror("Kļūda", "Nepareizs lietotājvārds vai parole.")

    def logout(self):
        self.current_user = None
        self.show_login_screen()

    def show_main_app(self):
        self.clear_root()

        app_frame = tk.Frame(self.root, bg="#f4f6f8")
        app_frame.pack(fill="both", expand=True, padx=20, pady=20)

        top_bar = tk.Frame(app_frame, bg="#f4f6f8")
        top_bar.pack(fill="x", pady=(0, 10))

        tk.Label(
            top_bar,
            text=f"Personīgā budžeta pārvaldība — {self.current_user}",
            font=("Arial", 20, "bold"),
            bg="#f4f6f8",
            fg="#1f2937"
        ).pack(side="left")

        ttk.Button(top_bar, text="Izlogoties", command=self.logout).pack(side="right")

        input_card = tk.Frame(app_frame, bg="white", bd=1, relief="solid", padx=15, pady=15)
        input_card.pack(fill="x", pady=(0, 15))

        self.type_var = tk.StringVar(value="Izdevums")

        tk.Label(input_card, text="Tips", bg="white", font=("Arial", 11)).grid(row=0, column=0, padx=8, pady=8)
        type_combo = ttk.Combobox(
            input_card,
            textvariable=self.type_var,
            values=["Ienākums", "Izdevums"],
            state="readonly",
            width=15
        )
        type_combo.grid(row=0, column=1, padx=8, pady=8)

        tk.Label(input_card, text="Summa", bg="white", font=("Arial", 11)).grid(row=0, column=2, padx=8, pady=8)
        self.entry_amount = ttk.Entry(input_card, width=18)
        self.entry_amount.grid(row=0, column=3, padx=8, pady=8)

        tk.Label(input_card, text="Apraksts", bg="white", font=("Arial", 11)).grid(row=0, column=4, padx=8, pady=8)
        self.entry_description = ttk.Entry(input_card, width=25)
        self.entry_description.grid(row=0, column=5, padx=8, pady=8)

        ttk.Button(input_card, text="Pievienot", command=self.add_record).grid(row=0, column=6, padx=12, pady=8)

        table_card = tk.Frame(app_frame, bg="white", bd=1, relief="solid", padx=10, pady=10)
        table_card.pack(fill="both", expand=True)

        columns = ("Tips", "Summa", "Apraksts")
        self.table = ttk.Treeview(table_card, columns=columns, show="headings")
        self.table.heading("Tips", text="Tips")
        self.table.heading("Summa", text="Summa (€)")
        self.table.heading("Apraksts", text="Apraksts")

        self.table.column("Tips", width=140, anchor="center")
        self.table.column("Summa", width=140, anchor="center")
        self.table.column("Apraksts", width=400, anchor="w")

        scrollbar = ttk.Scrollbar(table_card, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)

        self.table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        bottom_bar = tk.Frame(app_frame, bg="#f4f6f8")
        bottom_bar.pack(fill="x", pady=(15, 0))

        left_buttons = tk.Frame(bottom_bar, bg="#f4f6f8")
        left_buttons.pack(side="left")

        ttk.Button(left_buttons, text="Dzēst izvēlēto", command=self.delete_selected).pack(side="left", padx=5)
        ttk.Button(left_buttons, text="Dzēst visus manus ierakstus", command=self.delete_all).pack(side="left", padx=5)

        self.balance_label = tk.Label(
            bottom_bar,
            text="Bilance: 0.00 €",
            font=("Arial", 16, "bold"),
            bg="#f4f6f8",
            fg="#111827"
        )
        self.balance_label.pack(side="right")

        self.status_label = tk.Label(
            app_frame,
            text="",
            font=("Arial", 10),
            bg="#f4f6f8",
            fg="#b91c1c"
        )
        self.status_label.pack(anchor="w", pady=(8, 0))

        self.load_records()
        self.calculate_balance()

    def add_record(self):
        record_type = self.type_var.get()
        amount_text = self.entry_amount.get().strip()
        description = self.entry_description.get().strip()

        if not amount_text:
            self.status_label.config(text="Ievadi summu.")
            return

        try:
            amount = float(amount_text)
        except ValueError:
            self.status_label.config(text="Summai jābūt skaitlim.")
            return

        if amount <= 0:
            self.status_label.config(text="Summai jābūt lielākai par 0.")
            return

        with open(RECORDS_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([self.current_user, record_type, f"{amount:.2f}", description])

        self.entry_amount.delete(0, tk.END)
        self.entry_description.delete(0, tk.END)
        self.status_label.config(text="Ieraksts veiksmīgi pievienots.")
        self.load_records()
        self.calculate_balance()

    def load_records(self):
        for row in self.table.get_children():
            self.table.delete(row)

        with open(RECORDS_FILE, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["username"] == self.current_user:
                    self.table.insert("", tk.END, values=(row["type"], row["amount"], row["description"]))

    def calculate_balance(self):
        income = 0.0
        expense = 0.0

        with open(RECORDS_FILE, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["username"] == self.current_user:
                    amount = float(row["amount"])
                    if row["type"] == "Ienākums":
                        income += amount
                    elif row["type"] == "Izdevums":
                        expense += amount

        balance = income - expense
        self.balance_label.config(text=f"Bilance: {balance:.2f} €")

    def delete_selected(self):
        selected = self.table.selection()
        if not selected:
            self.status_label.config(text="Izvēlies ierakstu, ko dzēst.")
            return

        values = self.table.item(selected[0])["values"]
        selected_type = str(values[0])
        selected_amount = str(values[1])
        selected_description = str(values[2])

        rows_to_keep = []
        deleted = False

        with open(RECORDS_FILE, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        for row in rows:
            if (
                not deleted
                and row["username"] == self.current_user
                and row["type"] == selected_type
                and row["amount"] == selected_amount
                and row["description"] == selected_description
            ):
                deleted = True
                continue
            rows_to_keep.append(row)

        with open(RECORDS_FILE, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["username", "type", "amount", "description"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows_to_keep)

        self.status_label.config(text="Izvēlētais ieraksts izdzēsts.")
        self.load_records()
        self.calculate_balance()

    def delete_all(self):
        confirm = messagebox.askyesno("Apstiprinājums", "Vai tiešām dzēst visus šī lietotāja ierakstus?")
        if not confirm:
            return

        rows_to_keep = []

        with open(RECORDS_FILE, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["username"] != self.current_user:
                    rows_to_keep.append(row)

        with open(RECORDS_FILE, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["username", "type", "amount", "description"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows_to_keep)

        self.status_label.config(text="Visi tavi ieraksti izdzēsti.")
        self.load_records()
        self.calculate_balance()


if __name__ == "__main__":
    root = tk.Tk()
    app = BudgetApp(root)
    root.mainloop()