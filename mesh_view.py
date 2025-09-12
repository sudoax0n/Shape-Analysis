import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog,
    QLabel, QProgressBar
)
import pyvista as pv
from pyvistaqt import BackgroundPlotter
import time  # simulate loading

class PlyViewerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SMBL - Shape analysis Ply viewer")
        self.setGeometry(100, 100, 400, 150)

        self.layout = QVBoxLayout()
        self.label = QLabel("Select a .ply file to view", self)
        self.layout.addWidget(self.label)

        self.progress = QProgressBar(self)
        self.progress.setMaximum(100)
        self.progress.setValue(0)
        self.progress.setVisible(False)
        self.layout.addWidget(self.progress)

        self.btn_open = QPushButton("Open PLY File", self)
        self.btn_open.clicked.connect(self.open_ply_file)
        self.layout.addWidget(self.btn_open)

        self.setLayout(self.layout)
        self.plotter = None

    def open_ply_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open PLY File", "", "PLY Files (*.ply)"
        )
        if file_path:
            # Hide button and show progress bar
            self.btn_open.setVisible(False)
            self.progress.setVisible(True)
            self.label.setText(f"Loading: {file_path}")

            QApplication.processEvents()  # update GUI

            # Simulate loading with progress bar
            for i in range(0, 101, 10):
                time.sleep(0.05)  # remove if actual load is slow
                self.progress.setValue(i)
                QApplication.processEvents()

            # Load the mesh
            mesh = pv.read(file_path)

            # Close this popup after loading
            self.close()

            # Show the mesh in PyVista interactive window
            self.plotter = BackgroundPlotter()
            self.plotter.add_mesh(mesh)
            self.plotter.show()

def run_app():
    app = QApplication(sys.argv)
    viewer = PlyViewerApp()
    viewer.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run_app()

def nothing():
    return None