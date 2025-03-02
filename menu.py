import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QMessageBox

class ScriptRunnerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Main Menu")
        self.setGeometry(100, 100, 400, 300)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        layout.addWidget(QLabel("Select a Program to run:"))

        # Define your scripts here with their paths
        script_buttons = [
            ("Run Clinvar ", "/Users/aidanle/Downloads/Rare Diseases/distrib.py"),
            ("Run CADD ", "/Users/aidanle/Downloads/Rare Diseases/CADD.py"),
            
        ]

        for label, script_path in script_buttons:
            btn = QPushButton(label, self)
            btn.clicked.connect(lambda checked, path=script_path: self.run_script(path))
            layout.addWidget(btn)

        layout.addStretch()

    def run_script(self, script_path):
        """Run the specified Python script."""
        # Specify the exact Python interpreter if needed
        python_interpreter = sys.executable  # Uses the same Python running this GUI
        # Or hardcode it: python_interpreter = "/usr/local/bin/python3"

        try:
            result = subprocess.run([python_interpreter, script_path], 
                                  capture_output=True, 
                                  text=True)
            
            if result.returncode == 0:
                QMessageBox.information(self, "Success", 
                                      f"Script '{script_path}' executed successfully!\nOutput:\n{result.stdout}")
            else:
                QMessageBox.warning(self, "Error", 
                                  f"Script '{script_path}' failed!\nError:\n{result.stderr}")
                
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", 
                               f"Script '{script_path}' not found!\nMake sure the file exists.")
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                               f"An error occurred while running '{script_path}':\n{str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScriptRunnerGUI()
    window.show()
    sys.exit(app.exec_())