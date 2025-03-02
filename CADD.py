import sys
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
)
from PyQt5.QtCore import Qt

class CADDScoreApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Set window title and size
        self.setWindowTitle("CADD Score Aggregation Tool")
        self.setGeometry(100, 100, 600, 400)

        # Create input fields
        self.chrom_label = QLabel("Chromosome (e.g., 22):")
        self.chrom_entry = QLineEdit(self)

        self.start_label = QLabel("Start Position (e.g., 44044001):")
        self.start_entry = QLineEdit(self)

        self.end_label = QLabel("End Position (e.g., 44044002):")
        self.end_entry = QLineEdit(self)

        # Create a button to run the analysis
        self.run_button = QPushButton("Run Analysis", self)
        self.run_button.clicked.connect(self.run_analysis)

        # Create a text box to display results
        self.result_text = QTextEdit(self)
        self.result_text.setReadOnly(True)

        # Set up the layout
        layout = QVBoxLayout()

        # Add input fields
        input_layout = QVBoxLayout()
        input_layout.addWidget(self.chrom_label)
        input_layout.addWidget(self.chrom_entry)
        input_layout.addWidget(self.start_label)
        input_layout.addWidget(self.start_entry)
        input_layout.addWidget(self.end_label)
        input_layout.addWidget(self.end_entry)
        layout.addLayout(input_layout)

        # Add the button
        layout.addWidget(self.run_button)

        # Add the result text box
        layout.addWidget(self.result_text)

        # Set the layout for the window
        self.setLayout(layout)

    def query_cadd_range(self, chrom, start, end):
        """
        Query the CADD API for a specific genomic range.
        """
        api_url = f"https://cadd.gs.washington.edu/api/v1.0/GRCh38-v1.4/{chrom}:{start}-{end}"
        response = requests.get(api_url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: Unable to retrieve data for {chrom}:{start}-{end} (HTTP {response.status_code})")
            return None

    def query_large_range(self, chrom, start, end, chunk_size=10000):
        """
        Query a large range by splitting it into smaller chunks.
        Uses multithreading to query chunks in parallel.
        Returns two lists: one for RawScores and one for PHRED scores.
        """
        raw_scores = []
        phred_scores = []

        # Create a list of chunk ranges
        chunks = [(chrom, chunk_start, min(chunk_start + chunk_size, end))
                  for chunk_start in range(start, end, chunk_size)]

        # Use ThreadPoolExecutor to query chunks in parallel
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self.query_cadd_range, *chunk) for chunk in chunks]
            for future in as_completed(futures):
                data = future.result()
                if data:
                    # Extract RawScores (column index 4) and PHRED scores (column index 5)
                    raw_scores.extend(float(variant[4]) for variant in data[1:])
                    phred_scores.extend(float(variant[5]) for variant in data[1:])

        return raw_scores, phred_scores

    def calculate_average_score(self, scores):
        """
        Calculate the average score from a list of scores.
        """
        if not scores:
            return None
        return sum(scores) / len(scores)

    def interpret_scores(self, average_raw_score, average_phred_score):
        """
        Interpret the average CADD RawScore and PHRED score.
        """
        interpretation = "Interpretation of Scores:\n------------------------\n"

        # Interpret RawScore
        if average_raw_score is not None:
            if average_raw_score > 0:
                interpretation += f"- The average CADD RawScore of {average_raw_score:.4f} suggests that the variants are somewhat deleterious.\n"
            else:
                interpretation += f"- The average CADD RawScore of {average_raw_score:.4f} suggests that the variants are likely benign.\n"
        else:
            interpretation += "- No RawScore data available.\n"

        # Interpret PHRED score
        if average_phred_score is not None:
            if average_phred_score >= 30:
                interpretation += f"- The average CADD PHRED score of {average_phred_score:.4f} indicates that the variants are highly deleterious (top 0.1% of most deleterious substitutions).\n"
            elif average_phred_score >= 20:
                interpretation += f"- The average CADD PHRED score of {average_phred_score:.4f} indicates that the variants are likely deleterious (top 1% of most deleterious substitutions).\n"
            elif average_phred_score >= 10:
                interpretation += f"- The average CADD PHRED score of {average_phred_score:.4f} indicates that the variants are potentially deleterious (top 10% of most deleterious substitutions).\n"
            else:
                interpretation += f"- The average CADD PHRED score of {average_phred_score:.4f} suggests that the variants are likely benign.\n"
        else:
            interpretation += "- No PHRED score data available.\n"

        return interpretation

    def run_analysis(self):
        """
        Run the CADD score analysis based on user input.
        """
        # Get user input
        chrom = self.chrom_entry.text().strip()
        start = self.start_entry.text().strip()
        end = self.end_entry.text().strip()

        # Validate input
        if not chrom or not start or not end:
            QMessageBox.critical(self, "Error", "Please fill in all fields.")
            return

        try:
            start = int(start)
            end = int(end)
        except ValueError:
            QMessageBox.critical(self, "Error", "Start and end positions must be integers.")
            return

        # Query the CADD API
        self.result_text.clear()
        self.result_text.insertPlainText("Querying CADD API (this may take a while)...\n")
        QApplication.processEvents()  # Update the UI to show the message

        raw_scores, phred_scores = self.query_large_range(chrom, start, end)

        # Calculate and display the average scores
        if raw_scores and phred_scores:
            average_raw_score = self.calculate_average_score(raw_scores)
            average_phred_score = self.calculate_average_score(phred_scores)
            self.result_text.insertPlainText(f"\nAverage CADD RawScore for {chrom}:{start}-{end}: {average_raw_score:.4f}\n")
            self.result_text.insertPlainText(f"Average CADD PHRED score for {chrom}:{start}-{end}: {average_phred_score:.4f}\n")

            # Interpret the scores
            interpretation = self.interpret_scores(average_raw_score, average_phred_score)
            self.result_text.insertPlainText(interpretation)
        else:
            self.result_text.insertPlainText("No variants found in the specified range.\n")

# Run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CADDScoreApp()
    window.show()
    sys.exit(app.exec_())