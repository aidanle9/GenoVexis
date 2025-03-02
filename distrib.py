import sys
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Sample database stored as a dictionary (no access to clinvar without approval)
data = {
    "MYO7A": (90, 676, 755, 254, 167),
    "USH2A": (160, 1184, 1377, 422, 454)
}

class GeneScoreApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Set window title and size
        self.setWindowTitle("Gene Pathogenicity Score Calculator")
        self.setGeometry(100, 100, 800, 600)

        # Create input fields
        self.gene_label = QLabel("Enter gene names separated by commas (e.g., MYO7A,USH2A):")
        self.gene_entry = QLineEdit(self)

        # Create a button to run the analysis
        self.run_button = QPushButton("Calculate", self)
        self.run_button.clicked.connect(self.run_analysis)

        # Create a matplotlib figure and canvas for the plot
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)

        # Create a label to display the final score and interpretation
        self.result_label = QLabel(self)
        self.result_label.setAlignment(Qt.AlignCenter)

        # Set up the layout
        layout = QVBoxLayout()

        # Add input fields
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.gene_label)
        input_layout.addWidget(self.gene_entry)
        layout.addLayout(input_layout)

        # Add the button
        layout.addWidget(self.run_button)

        # Add the result label
        layout.addWidget(self.result_label)

        # Add the matplotlib canvas
        layout.addWidget(self.canvas)

        # Set the layout for the window
        self.setLayout(layout)

    def calculate_gene_score(self, gene_data):
        """
        Calculate relative densities and score for a gene.
        """
        benign, likely_benign, uncertain, likely_pathogenic, pathogenic = gene_data
        values = np.array([benign, likely_benign, uncertain, likely_pathogenic, pathogenic], dtype=float)
        total = np.sum(values)

        # Avoid division by zero
        if total == 0:
            return np.zeros(5), 5.0

        # Normalize to relative densities
        relative_density = values / total

        # Calculate weighted average score
        weights = np.array([1, 2, 5, 8, 10])
        avg_score = np.sum(relative_density * weights)

        return relative_density, avg_score

    def interpret_score(self, avg_score):
        """
        Interpret the average score.
        """
        if 8.5 <= avg_score <= 10:
            return "Pathogenic"
        elif 6.5 <= avg_score < 8.5:
            return "Likely Pathogenic"
        elif 4.5 <= avg_score < 6.5:
            return "Uncertain/Conflicting"
        elif 2.5 <= avg_score < 4.5:
            return "Likely Benign"
        else:
            return "Benign"

    def run_analysis(self):
        """
        Run the analysis based on user input.
        """
        # Get user input
        selected_genes = self.gene_entry.text().strip().split(",")

        # Initialize cumulative densities and score tracking
        combined_relative_densities = np.zeros(5)
        all_scores = []
        valid_genes = []

        # Process only selected genes
        for gene in selected_genes:
            gene = gene.strip()  # Remove extra spaces
            if gene in data:  # Ensure the gene exists in the dataset
                valid_genes.append(gene)
                relative_density, avg_score = self.calculate_gene_score(data[gene])
                combined_relative_densities += relative_density  # Sum densities across genes
                all_scores.append(avg_score)

        # Check if no valid genes were selected
        if not valid_genes:
            QMessageBox.critical(self, "Error", "No valid genes selected. Please check your input.")
            return

        # Compute overall average score
        overall_avg_score = np.mean(all_scores)

        # Interpretation of final score
        final_category = self.interpret_score(overall_avg_score)

        # Display final results
        self.result_label.setText(
            f"Final Composite Score: {overall_avg_score:.2f}\nFinal Interpretation: {final_category}"
        )

        # Plot bar chart with annotations
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        categories = ["Benign", "Likely Benign", "Uncertain", "Likely Pathogenic", "Pathogenic"]
        bars = ax.bar(categories, combined_relative_densities, color="skyblue", alpha=0.6, label="Relative Density")

        # Add annotations to the bars
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height,
                f"{height:.2f}",
                ha="center",
                va="bottom",
            )

        # Add final score and interpretation to the top-left corner of the graph
        ax.text(
            0.007,
            0.985,
            f"Final Composite Score: {overall_avg_score:.2f}\nFinal Interpretation: {final_category}",
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment="top",
            bbox=dict(facecolor="white", alpha=0.6),
        )

        ax.set_title(f"Pathogenicity Score Distribution for {', '.join(valid_genes)}", fontweight="bold")
        ax.set_xlabel("Categories", fontweight="bold")
        ax.set_ylabel("Relative Density", fontweight="bold")
        ax.set_ylim(0, max(combined_relative_densities) * 1.2)  # Add some padding at the top
        ax.legend()

        # Refresh the canvas
        self.canvas.draw()

# Run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GeneScoreApp()
    window.show()
    sys.exit(app.exec_())