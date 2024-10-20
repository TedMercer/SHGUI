from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, QFileDialog, QVBoxLayout, 
                             QWidget, QHBoxLayout, QLineEdit, QMessageBox, QListWidget, QInputDialog, QComboBox, QSlider, QToolBar)
from PyQt5.QtCore import Qt
import sys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np
import os

from SHG_Analysis_class import DataPlotter

class SHGAnalysisGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SHGUI")
        self.setGeometry(100, 100, 800, 600)
        
        self.data_plotter = DataPlotter()  
        self.folder_path = ""
        self.vmin = 400
        self.vmax = 1000
        self.cmap = 'viridis'
        self.zoom_size = 150
        self.background_selected = False
        self.roi_selected = False
        self.bin_values = [] 
        self.is_dark_mode = False  
        
        self.initUI()

    def initUI(self):
        # Main widget and layout
        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        # Add Toolbar for Dark/Light Mode Toggle
        toolbar = QToolBar("Toolbar", self)
        self.addToolBar(toolbar)
        toggle_mode_btn = QPushButton("Toggle Dark Mode", self)
        toggle_mode_btn.clicked.connect(self.toggle_mode)
        toolbar.addWidget(toggle_mode_btn)

        # Select Folder Button
        select_folder_btn = QPushButton("Select Working Folder", self)
        select_folder_btn.clicked.connect(self.select_folder)
        main_layout.addWidget(select_folder_btn)

        # Refresh Folder Button
        refresh_folder_btn = QPushButton("Refresh Folder Contents", self)
        refresh_folder_btn.clicked.connect(self.refresh_folder)
        main_layout.addWidget(refresh_folder_btn)

        # File List Widget
        self.file_list_widget = QListWidget(self)
        main_layout.addWidget(self.file_list_widget)

        # Load Data Button
        load_data_btn = QPushButton("Load Data", self)
        load_data_btn.clicked.connect(self.load_data)
        main_layout.addWidget(load_data_btn)

        # Plot Data Button
        plot_data_btn = QPushButton("Plot Data", self)
        plot_data_btn.clicked.connect(self.plot_data)
        main_layout.addWidget(plot_data_btn)

        # vmax and vmin adjustment widgets
        vmin_layout = QHBoxLayout()
        vmin_label = QLabel("vmin:")
        vmin_layout.addWidget(vmin_label)
        vmin_slider = QSlider(Qt.Horizontal)
        vmin_slider.setRange(-1000, 1000)
        vmin_slider.setValue(self.vmin)
        vmin_slider.valueChanged.connect(self.update_vmin)
        vmin_layout.addWidget(vmin_slider)
        self.vmin_input = QLineEdit(str(self.vmin))
        self.vmin_input.setFixedWidth(60)
        self.vmin_input.editingFinished.connect(self.vmin_input_changed)
        vmin_layout.addWidget(self.vmin_input)
        main_layout.addLayout(vmin_layout)

        vmax_layout = QHBoxLayout()
        vmax_label = QLabel("vmax:")
        vmax_layout.addWidget(vmax_label)
        vmax_slider = QSlider(Qt.Horizontal)
        vmax_slider.setRange(-1000, 1000)
        vmax_slider.setValue(self.vmax)
        vmax_slider.valueChanged.connect(self.update_vmax)
        vmax_layout.addWidget(vmax_slider)
        self.vmax_input = QLineEdit(str(self.vmax))
        self.vmax_input.setFixedWidth(60)
        self.vmax_input.editingFinished.connect(self.vmax_input_changed)
        vmax_layout.addWidget(self.vmax_input)
        main_layout.addLayout(vmax_layout)

        # Colormap selection dropdown
        cmap_layout = QHBoxLayout()
        cmap_label = QLabel("Colormap:")
        cmap_layout.addWidget(cmap_label)
        self.cmap_combo = QComboBox(self)
        self.cmap_combo.addItems(plt.colormaps())
        self.cmap_combo.setCurrentText(self.cmap)
        self.cmap_combo.currentIndexChanged.connect(self.update_cmap)
        cmap_layout.addWidget(self.cmap_combo)
        main_layout.addLayout(cmap_layout)

        # Zoom Size Input for ROI Selection
        zoom_layout = QHBoxLayout()
        zoom_label = QLabel("Zoom Size:")
        zoom_layout.addWidget(zoom_label)
        self.zoom_input = QLineEdit(str(self.zoom_size))
        self.zoom_input.setFixedWidth(60)
        self.zoom_input.editingFinished.connect(self.update_zoom_size)
        zoom_layout.addWidget(self.zoom_input)
        main_layout.addLayout(zoom_layout)

        # Background Selection Button
        background_btn = QPushButton("Select Background", self)
        background_btn.clicked.connect(self.select_background)
        main_layout.addWidget(background_btn)

        # ROI Selection Button
        roi_btn = QPushButton("Select ROI (Interactive Circle)", self)
        roi_btn.clicked.connect(self.select_roi)
        main_layout.addWidget(roi_btn)

        # Calculate Average Intensity Button
        calc_intensity_btn = QPushButton("Calculate Average Intensity", self)
        calc_intensity_btn.clicked.connect(self.calculate_intensity)
        main_layout.addWidget(calc_intensity_btn)

        # Plot Polar Button
        plot_polar_btn = QPushButton("Plot Polar", self)
        plot_polar_btn.clicked.connect(self.plot_polar)
        main_layout.addWidget(plot_polar_btn)

        # Save Results Button
        save_btn = QPushButton("Save Results", self)
        save_btn.clicked.connect(self.save_results)
        main_layout.addWidget(save_btn)

        # Status Label
        self.status_label = QLabel("Status: Ready", self)
        main_layout.addWidget(self.status_label)

    def toggle_mode(self):
        if self.is_dark_mode:
            self.setStyleSheet("")
            self.is_dark_mode = False
            self.status_label.setText("Status: Switched to Light Mode")
        else:
            self.setStyleSheet("QMainWindow { background-color: #2E2E2E; color: white; } QPushButton { background-color: #4F4F4F; color: white; } QLabel { color: white; } QLineEdit { background-color: #4F4F4F; color: white; } QListWidget { background-color: #4F4F4F; color: white; }")
            self.is_dark_mode = True
            self.status_label.setText("Status: Switched to Dark Mode")

    def select_folder(self):
        try:
            options = QFileDialog.Options()
            folder_path = QFileDialog.getExistingDirectory(self, "Select Working Folder", options=options)
            if folder_path:
                self.folder_path = folder_path
                self.refresh_folder()
                self.status_label.setText(f"Status: Selected folder {folder_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")

    def refresh_folder(self):
        try:
            if self.folder_path:
                self.file_list_widget.clear()
                files = [f for f in os.listdir(self.folder_path) if f.endswith(('.tiff', '.txt', '.csv'))]
                self.file_list_widget.addItems(files)
                self.status_label.setText("Status: Folder contents refreshed")
            else:
                QMessageBox.warning(self, "Warning", "Please select a folder first.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")

    def load_data(self):
        try:
            selected_item = self.file_list_widget.currentItem()
            if selected_item:
                file_name = selected_item.text()
                file_path = os.path.join(self.folder_path, file_name)
                self.data_plotter.load_data(file_path)
                self.status_label.setText(f"Status: Loaded data from {file_path}")
            else:
                QMessageBox.warning(self, "Warning", "Please select a file from the list.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while loading data: {e}")

    def plot_data(self):
        try:
            self.data_plotter.plot_data(vmin=self.vmin, vmax=self.vmax, cmap=self.cmap)
            self.status_label.setText(f"Status: Data plotted with vmin={self.vmin}, vmax={self.vmax}, cmap={self.cmap}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while plotting data: {e}")

    def update_vmin(self, value):
        try:
            self.vmin = value
            self.vmin_input.setText(str(value))
            self.status_label.setText(f"Status: vmin updated to {self.vmin}")
        except ValueError:
            QMessageBox.warning(self, "Warning", "Please enter a valid integer for vmin.")

    def vmin_input_changed(self):
        try:
            value = int(self.vmin_input.text())
            self.vmin = value
            self.status_label.setText(f"Status: vmin updated to {self.vmin}")
        except ValueError:
            QMessageBox.warning(self, "Warning", "Please enter a valid integer for vmin.")

    def update_vmax(self, value):
        try:
            self.vmax = value
            self.vmax_input.setText(str(value))
            self.status_label.setText(f"Status: vmax updated to {self.vmax}")
        except ValueError:
            QMessageBox.warning(self, "Warning", "Please enter a valid integer for vmax.")

    def vmax_input_changed(self):
        try:
            value = int(self.vmax_input.text())
            self.vmax = value
            self.status_label.setText(f"Status: vmax updated to {self.vmax}")
        except ValueError:
            QMessageBox.warning(self, "Warning", "Please enter a valid integer for vmax.")

    def update_cmap(self):
        try:
            self.cmap = self.cmap_combo.currentText()
            self.status_label.setText(f"Status: Colormap updated to {self.cmap}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while updating colormap: {e}")

    def update_zoom_size(self):
        try:
            value = int(self.zoom_input.text())
            self.zoom_size = value
            self.status_label.setText(f"Status: Zoom size updated to {self.zoom_size}")
        except ValueError:
            QMessageBox.warning(self, "Warning", "Please enter a valid integer for zoom size.")

    def select_background(self):
        try:
            if self.background_selected:
                reply = QMessageBox.question(self, 'Overwrite Background', "A background is already selected. Do you want to overwrite it?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    self.status_label.setText("Status: Background selection cancelled")
                    return
            self.status_label.setText("Status: Selecting background - Use Enter to confirm, 'e' to stop")
            self.data_plotter.background()
            self.background_selected = True
            self.status_label.setText("Status: Background selected")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while selecting background: {e}")

    def select_roi(self):
        try:
            if self.roi_selected:
                reply = QMessageBox.question(self, 'Overwrite ROI', "An ROI is already selected. Do you want to overwrite it?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    self.status_label.setText("Status: ROI selection cancelled")
                    return
                # Reset ROI attributes to default before overwriting
                self.data_plotter.circle_coords = None
                self.data_plotter.radius_list = []
                self.data_plotter.radius = 1
                self.data_plotter.zoom_size = self.zoom_size
                self.data_plotter.circle_artist = None
                self.data_plotter.zoom_circle_artist = None
                self.data_plotter.stage = 0
            self.status_label.setText("Status: Selecting ROI interactively with zoom size = {}".format(self.zoom_size))
            self.data_plotter.interactive_circle_selection(zoom_size=self.zoom_size)
            self.roi_selected = True
            self.status_label.setText("Status: ROI selected")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while selecting ROI: {e}")

    def calculate_intensity(self):
        try:
            bin_size, ok = QInputDialog.getInt(self, "Bin Size", "Enter bin size:")
            if ok:
                self.bin_values.append(bin_size)  # Store the selected bin value
                self.data_plotter.calculate_average_intensity(bin_size)
                self.status_label.setText(f"Status: Average intensity calculated with bin size {bin_size}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while calculating intensity: {e}")

    def plot_polar(self):
        try:
            self.data_plotter.polar_plot()
            self.status_label.setText("Status: Polar plot generated")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while plotting polar data: {e}")

    def save_results(self):
        try:
            options = QFileDialog.Options()
            folder_name = QFileDialog.getExistingDirectory(self, "Select Folder to Save Results", options=options)
            if folder_name:
                description, ok = QInputDialog.getText(self, "Description", "Enter a description for the saved data:")
                if ok:
                    
                    for bin_value in self.bin_values:
                        self.data_plotter.calculate_average_intensity(bin_value, plot = False)
                        self.data_plotter.save_txt(folder_name, f"{description}_bin{bin_value}")
                    self.status_label.setText(f"Status: Results saved in {folder_name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while saving results: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = SHGAnalysisGUI()
    main_window.show()
    sys.exit(app.exec_())
