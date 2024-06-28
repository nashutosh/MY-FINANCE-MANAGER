import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import datetime
import csv

class PersonalFinanceManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Personal Finance Manager")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.connection = sqlite3.connect("database.db")
        self.cursor = self.connection.cursor()
        self.create_tables()

        self.current_user = 1  # Using a fixed user ID for simplicity

        self.create_main_widgets()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                type TEXT NOT NULL
            )
        """)
        self.connection.commit()

    def create_main_widgets(self):
        self.clear_widgets()

        title_label = ttk.Label(self.root, text="Personal Finance Manager", font=("Helvetica", 16))
        title_label.pack(pady=10)

        self.transaction_frame = ttk.LabelFrame(self.root, text="Add Transaction")
        self.transaction_frame.pack(padx=10, pady=10, fill="x", expand="yes")

        self.create_transaction_fields()

        self.history_frame = ttk.LabelFrame(self.root, text="Transaction History")
        self.history_frame.pack(padx=10, pady=10, fill="both", expand="yes")

        self.create_transaction_history()

        self.balance_frame = ttk.LabelFrame(self.root, text="Balance Summary")
        self.balance_frame.pack(padx=10, pady=10, fill="x", expand="yes")

        self.create_balance_summary()

        self.summary_frame = ttk.LabelFrame(self.root, text="Income vs Expenses")
        self.summary_frame.pack(padx=10, pady=10, fill="both", expand="yes")

        self.create_income_expense_summary()

        self.load_transactions()

    def create_transaction_fields(self):
        ttk.Label(self.transaction_frame, text="Date (YYYY-MM-DD):").grid(row=0, column=0, padx=5, pady=5)
        self.date_entry = ttk.Entry(self.transaction_frame)
        self.date_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.transaction_frame, text="Description:").grid(row=1, column=0, padx=5, pady=5)
        self.description_entry = ttk.Entry(self.transaction_frame)
        self.description_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(self.transaction_frame, text="Amount:").grid(row=2, column=0, padx=5, pady=5)
        self.amount_entry = ttk.Entry(self.transaction_frame)
        self.amount_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(self.transaction_frame, text="Type:").grid(row=3, column=0, padx=5, pady=5)
        self.type_combobox = ttk.Combobox(self.transaction_frame, values=["Income", "Expense"])
        self.type_combobox.grid(row=3, column=1, padx=5, pady=5)

        add_button = ttk.Button(self.transaction_frame, text="Add Transaction", command=self.add_transaction)
        add_button.grid(row=4, columnspan=2, pady=10)

        export_button = ttk.Button(self.transaction_frame, text="Export to CSV", command=self.export_to_csv)
        export_button.grid(row=5, columnspan=2, pady=10)

    def create_transaction_history(self):
        self.history_tree = ttk.Treeview(self.history_frame, columns=("Date", "Description", "Amount", "Type"), show="headings")
        self.history_tree.heading("Date", text="Date")
        self.history_tree.heading("Description", text="Description")
        self.history_tree.heading("Amount", text="Amount")
        self.history_tree.heading("Type", text="Type")
        self.history_tree.pack(padx=10, pady=10, fill="both", expand="yes")

        scrollbar = ttk.Scrollbar(self.history_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

    def create_balance_summary(self):
        self.balance_label = ttk.Label(self.balance_frame, text="Current Balance: $0.00", font=("Helvetica", 14))
        self.balance_label.pack(padx=10, pady=10)

    def create_income_expense_summary(self):
        self.income_expense_label = ttk.Label(self.summary_frame, text="Income: $0.00 | Expenses: $0.00", font=("Helvetica", 14))
        self.income_expense_label.pack(padx=10, pady=10)

    def add_transaction(self):
        date = self.date_entry.get()
        description = self.description_entry.get()
        amount = self.amount_entry.get()
        transaction_type = self.type_combobox.get()

        if not date or not description or not amount or not transaction_type:
            messagebox.showerror("Input Error", "All fields are required.")
            return

        try:
            datetime.datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Input Error", "Date must be in YYYY-MM-DD format.")
            return

        try:
            amount = float(amount)
        except ValueError:
            messagebox.showerror("Input Error", "Amount must be a number.")
            return

        self.cursor.execute("""
            INSERT INTO transactions (user_id, date, description, amount, type) VALUES (?, ?, ?, ?, ?)
        """, (self.current_user, date, description, amount, transaction_type))
        self.connection.commit()

        self.history_tree.insert("", "end", values=(date, description, amount, transaction_type))
        self.update_balance()
        self.update_income_expense_summary()

        self.date_entry.delete(0, tk.END)
        self.description_entry.delete(0, tk.END)
        self.amount_entry.delete(0, tk.END)
        self.type_combobox.set("")

    def load_transactions(self):
        self.history_tree.delete(*self.history_tree.get_children())

        self.cursor.execute("SELECT date, description, amount, type FROM transactions WHERE user_id = ?", (self.current_user,))
        for row in self.cursor.fetchall():
            self.history_tree.insert("", "end", values=row)
        
        self.update_balance()
        self.update_income_expense_summary()

    def update_balance(self):
        self.cursor.execute("SELECT amount, type FROM transactions WHERE user_id = ?", (self.current_user,))
        balance = 0
        for amount, transaction_type in self.cursor.fetchall():
            if transaction_type == "Income":
                balance += amount
            else:
                balance -= amount

        self.balance_label.config(text=f"Current Balance: ${balance:.2f}")

    def update_income_expense_summary(self):
        self.cursor.execute("SELECT type, SUM(amount) FROM transactions WHERE user_id = ? GROUP BY type", (self.current_user,))
        income = 0
        expenses = 0
        for transaction_type, total_amount in self.cursor.fetchall():
            if transaction_type == "Income":
                income = total_amount
            else:
                expenses = total_amount

        self.income_expense_label.config(text=f"Income: ${income:.2f} | Expenses: ${expenses:.2f}")

    def export_to_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.cursor.execute("SELECT date, description, amount, type FROM transactions WHERE user_id = ?", (self.current_user,))
            rows = self.cursor.fetchall()
            with open(file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Date", "Description", "Amount", "Type"])
                writer.writerows(rows)
            messagebox.showinfo("Export Success", f"Transactions exported to {file_path}")

    def clear_widgets(self):
        for widget in self.root.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PersonalFinanceManager(root)
    root.mainloop()
