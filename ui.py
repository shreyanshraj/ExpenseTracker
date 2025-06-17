from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
                             QLabel, QLineEdit, QHBoxLayout, QComboBox, QDateEdit, QMessageBox, 
                             QProgressBar)

from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QIcon as QI
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd

class ExpenseTrackerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Expense Tracker")
        self.setGeometry(100, 100, 800, 550)
        self.setWindowIcon(QI('vecteezy_sr-logo-monogram-emblem-style-with-crown-shape-design-template_.jpg'))

        self.monthly_budget = 800  # fixed monthly budget

        self.layout = QVBoxLayout() # type: ignore
        self.setLayout(self.layout) # type: ignore

        self.init_ui()
        self.init_db()
        self.load_expenses()

    def init_ui(self):
        # Input form
        form_layout = QHBoxLayout()
        self.date_input = QDateEdit(calendarPopup=True) # type: ignore
        self.date_input.setDate(QDate.currentDate())
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Amount")
        self.category_input = QComboBox()
        self.category_input.addItems(["Food", "Transport", "Rent", "Utilities", "Other"])
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Description")
        add_btn = QPushButton("Add Expense")
        add_btn.clicked.connect(self.add_expense)

        form_layout.addWidget(self.date_input)
        form_layout.addWidget(self.amount_input)
        form_layout.addWidget(self.category_input)
        form_layout.addWidget(self.desc_input)
        form_layout.addWidget(add_btn)

        self.layout.addLayout(form_layout)

        # Progress bar
        self.progress_label = QLabel("Monthly Budget Progress:")
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.layout.addWidget(self.progress_label)
        self.layout.addWidget(self.progress_bar)

        # Table and buttons
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Date", "Amount", "Category", "Description"])
        self.layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self.delete_expense)
        edit_btn = QPushButton("Edit Selected")
        edit_btn.clicked.connect(self.edit_expense)
        chart_btn = QPushButton("Show Monthly Chart")
        chart_btn.clicked.connect(self.show_monthly_chart)

        button_layout.addWidget(delete_btn)
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(chart_btn)

        self.layout.addLayout(button_layout)

    def init_db(self):
        self.conn = sqlite3.connect("expenses.db")
        self.cursor = self.conn.cursor() # type: ignore
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                amount REAL,
                category TEXT,
                description TEXT
            )
        ''')
        self.conn.commit()

    def add_expense(self):
        date = self.date_input.date().toString("yyyy-MM-dd")
        try:
            amount = float(self.amount_input.text())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter a valid amount.")
            return
        category = self.category_input.currentText()
        description = self.desc_input.text()

        self.cursor.execute("INSERT INTO expenses (date, amount, category, description) VALUES (?, ?, ?, ?)",
                            (date, amount, category, description))
        self.conn.commit()
        self.load_expenses()
        self.amount_input.clear()
        self.desc_input.clear()

    def load_expenses(self):
        self.cursor.execute("SELECT id, date, amount, category, description FROM expenses ORDER BY date DESC")
        rows = self.cursor.fetchall()

        self.table.setRowCount(len(rows))
        for row_idx, row_data in enumerate(rows):
            for col_idx, item in enumerate(row_data):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(item)))

        self.update_progress_bar()

    def update_progress_bar(self):
        current_month = QDate.currentDate().toString("yyyy-MM")
        self.cursor.execute("SELECT SUM(amount) FROM expenses WHERE date LIKE ?", (current_month + '%',))
        total = self.cursor.fetchone()[0]
        total = total if total else 0

        # Color logic
        if total <= self.monthly_budget:
            percentage = (total / self.monthly_budget) * 100
            self.progress_bar.setMaximum(self.monthly_budget)
            self.progress_bar.setValue(int(total))
            self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #00cc66; }")
            self.progress_label.setText(f"Monthly Budget Progress: ${int(total)} / ${self.monthly_budget}")
        else:
            percentage_over = (total - self.monthly_budget) / self.monthly_budget * 100
            self.progress_bar.setMaximum(total)  # dynamically increase max
            self.progress_bar.setValue(int(total))
            self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: red; }")
            self.progress_label.setText(
                f"Monthly Budget Exceeded: ${int(total)} / ${self.monthly_budget} ({percentage_over:.1f}% over)"
            )

    def delete_expense(self):
        selected = self.table.currentRow()
        if selected >= 0:
            expense_id = int(self.table.item(selected, 0).text())# type: ignore
            self.cursor.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
            self.conn.commit()
            self.load_expenses()

    def edit_expense(self):
        selected = self.table.currentRow()
        if selected >= 0:
            expense_id = int(self.table.item(selected, 0).text()) # type: ignore
            date = self.date_input.date().toString("yyyy-MM-dd")
            try:
                amount = float(self.amount_input.text())
            except ValueError:
                QMessageBox.warning(self, "Input Error", "Please enter a valid amount.")
                return
            category = self.category_input.currentText()
            description = self.desc_input.text()

            self.cursor.execute("UPDATE expenses SET date=?, amount=?, category=?, description=? WHERE id=?",
                                (date, amount, category, description, expense_id))
            self.conn.commit()
            self.load_expenses()

    def show_monthly_chart(self):
        self.cursor.execute("SELECT date, amount FROM expenses")
        data = self.cursor.fetchall()

        if not data:
            QMessageBox.information(self, "No Data", "No expenses available to plot.")
            return

        df = pd.DataFrame(data, columns=["date", "amount"])
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.to_period('M')
        monthly_totals = df.groupby('month')['amount'].sum()

        plt.figure(figsize=(8, 4))
        monthly_totals.plot(kind='bar', color='skyblue')
        plt.title("Monthly Expenses")
        plt.xlabel("Month")
        plt.ylabel("Total Spent")
        plt.tight_layout()
        plt.show()