# This app helps is keeping track of monthly expenses

import sys
from PyQt5.QtWidgets import QApplication
from ui import ExpenseTrackerApp

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ExpenseTrackerApp()
    window.show()
    sys.exit(app.exec_())
