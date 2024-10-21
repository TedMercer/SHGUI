'''
Created by Teddy Mercer
Date: 2021-07-07
Description: This class is designed to handle the analysis of Second Harmonic Generation (SHG) data.

The class DataPlotter is designed to load and plot data from various file formats (e.g., .tiff, .txt, .csv).
It provides methods to plot the data, zoom in on a region of interest, and select circular regions for analysis.
The calculate_average_intensity method calculates the average intensity along a circular path defined by two radii.
'''
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector
from skimage.draw import circle_perimeter
from scipy.ndimage import zoom
from skimage.io import imread
import pandas as pd 
import os

class DataPlotter:
    def __init__(self):
        '''
        Class Attributes:

        data: The data to be analyzed
        circle_coords: The coordinates of the center of the circle
        radius_list: A list of radii for the circles
        radius: The current radius of the circle
        zoom_size: The size of the zoomed-in region
        circle_artist: The artist object for the circle
        zoom_circle_artist: The artist object for the zoomed-in circle
        stage: The current stage of the circle selection process
        vmin: The minimum intensity value for plotting
        vmax: The maximum intensity value for plotting
        cmap: The color map for plotting
        average_intensities: The average intensities along the
        circular path defined by the radii

        '''
        self.data = None
        self.circle_coords = None  
        self.radius_list = []  
        self.radius = 1  
        self.zoom_size = 50 
        self.circle_artist = None  
        self.zoom_circle_artist = None  
        self.stage = 0  
        self.vmin = None
        self.vmax = None
        self.cmap = None
        self.average_intensities_raw = []
        self.average_intensities_sub = []
        self.background_values = []
        self.num_regions = 0  
        self.current_rectangle = None  
        self.bin = 0

    def load_data(self, file_path: str):
        """Load data from .tiff, .txt, or .csv files."""
        if file_path.endswith('.tiff'):
            self.data = imread(file_path)
        elif file_path.endswith('.txt'):
            self.data = np.loadtxt(file_path)
        elif file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
            self.data = df.to_numpy()
            self.data = np.nan_to_num(self.data.astype(np.float64), nan=0)
        else:
            raise ValueError("Unsupported file type. Use .tiff, .txt, or .csv")

    def plot_data(self, vmin=None, vmax=None, cmap = None):
        """Plot the data with an optional color map and intensity range."""
        if vmin is not None:
            self.vmin = vmin
        if vmax is not None:
            self.vmax = vmax
        if cmap is not None: 
            self.cmap = cmap

        plt.figure(figsize=(6, 6))
        plt.imshow(self.data, cmap=self.cmap, vmin=self.vmin, vmax=self.vmax)
        plt.title('Data Plot')
        plt.colorbar()
        plt.show()

    def background(self):
        """Interactively select regions to calculate and update the average background continuously."""
        fig, ax = plt.subplots()
        ax.imshow(self.data, cmap=self.cmap, vmin=self.vmin, vmax=self.vmax)
        plt.title(r'Select regions for background calculation.' '\n' 'Press Enter to confirm, press "e" to confirm.')

        def onselect(eclick, erelease):
            """Handler to draw a rectangle and calculate background on confirmation."""
            x1, y1 = int(min(eclick.xdata, erelease.xdata)), int(min(eclick.ydata, erelease.ydata))
            x2, y2 = int(max(eclick.xdata, erelease.xdata)), int(max(eclick.ydata, erelease.ydata))
            rect = plt.Rectangle((x1, y1), x2-x1, y2-y1, edgecolor='red', facecolor='none', linewidth=2)
            ax.add_patch(rect)
            plt.draw()

        def on_key(event):
            """Handle key presses to confirm selection or exit."""
            if event.key == 'enter':
                rect = ax.patches[-1]  
                extent = rect.get_bbox().extents
                x1, y1, x2, y2 = map(int, extent)
                selected_region = self.data[y1:y2, x1:x2]
                background_intensity = np.mean(selected_region)
                self.background_values.append(background_intensity)

                if len(self.background_values) > 1:  
                    updated_average = np.mean(self.background_values)
                else:
                    updated_average = background_intensity

                rect.set_edgecolor('green')  
                plt.title(f"Average Background: {updated_average:.2f}. Continue selecting or press 'e' to exit.")
                plt.draw()

            elif event.key == 'e':  
                if self.background_values:
                    self.bkg = np.mean(self.background_values)  
                else:
                    self.bkg = 0
                print(f"Final Average Background: {self.bkg:.2f}")

                selector.disconnect_events()
                fig.canvas.mpl_disconnect(key_event_id)

                selector.set_active(False)

                plt.title(f"Final Average Background: {self.bkg:.2f} (Static)")
                plt.draw()

        selector = RectangleSelector(ax, onselect, useblit=True, button=[1],
                                    minspanx=5, minspany=5, spancoords='pixels', interactive=True)

        key_event_id = fig.canvas.mpl_connect('key_press_event', on_key)

        plt.show()

    def interactive_circle_selection(self, zoom_size=50, vmin=None, vmax=None):
        """
        Interactive method for the user to click once to define the center,
        click again to define the radius, and right-click to confirm the selection.
        Shows the center and radius on the zoomed-in plot.
        """
        if vmin is not None:
            self.vmin = vmin
        if vmax is not None:
            self.vmax = vmax

        self.zoom_size = zoom_size  

        
        fig, (ax_main, ax_zoom) = plt.subplots(1, 2, figsize=(12, 6))

        
        ax_main.imshow(self.data, cmap=self.cmap, vmin=self.vmin, vmax=self.vmax)
        ax_main.set_title('Left-click to set center, right-click to confirm')

        
        ax_zoom.set_title(f'Static Zoomed View (Zoom Size: {self.zoom_size})')

        
        def on_click(event):
            if event.inaxes == ax_main:
                if event.button == 1:  
                    if self.stage == 0:  
                        self.circle_coords = (event.xdata, event.ydata)
                        self.radius = 1  
                        if self.circle_artist is not None:
                            self.circle_artist.remove()  
                        self.circle_artist = plt.Circle(self.circle_coords, self.radius, color='r', fill=False)
                        ax_main.add_artist(self.circle_artist)

                        
                        x0, y0 = int(event.xdata), int(event.ydata)
                        ax_zoom.imshow(self.data, cmap=self.cmap, vmin=self.vmin, vmax=self.vmax)
                        ax_zoom.set_xlim(x0 - self.zoom_size // 2, x0 + self.zoom_size // 2)
                        ax_zoom.set_ylim(y0 + self.zoom_size // 2, y0 - self.zoom_size // 2) 

                        
                        ax_zoom.annotate(f"Center: ({x0:.0f}, {y0:.0f})", (x0, y0), color='white', fontsize=10)
                        self.zoom_circle_artist = plt.Circle((x0, y0), self.radius, color='r', fill=False)
                        ax_zoom.add_artist(self.zoom_circle_artist)

                        fig.canvas.draw()
                        ax_main.set_title('Right-click to confirm center and set first radius')

                    elif self.stage == 1:  
                        
                        radius = np.sqrt((event.xdata - self.circle_coords[0])**2 +
                                         (event.ydata - self.circle_coords[1])**2)
                        self.circle_artist.set_radius(radius)  
                        self.radius = radius  

                        
                        x0, y0 = int(self.circle_coords[0]), int(self.circle_coords[1])
                        self.zoom_circle_artist.set_radius(self.radius)
                        fig.canvas.draw()

                        ax_main.set_title('Right-click to confirm the first radius and start second circle')

                    elif self.stage == 2:  
                        
                        radius = np.sqrt((event.xdata - self.circle_coords[0])**2 +
                                         (event.ydata - self.circle_coords[1])**2)
                        self.circle_artist.set_radius(radius)  
                        self.radius = radius  
                        
                        self.zoom_circle_artist.set_radius(self.radius)
                        fig.canvas.draw()

                        ax_main.set_title('Right-click to confirm the second radius')

                elif event.button == 3:  
                    if self.stage == 0 and self.circle_coords is not None:
                        
                        self.circle_artist.set_edgecolor('g')  
                        fig.canvas.draw()
                        ax_main.set_title('Left-click to set first radius')
                        self.stage = 1
                    elif self.stage == 1 and self.radius > 0:
                        
                        self.circle_artist.set_edgecolor('b')  
                        self.radius_list.append(self.radius) 
                        fig.canvas.draw()
                        ax_main.set_title('Left-click to set second radius')
                        self.stage = 2
                    elif self.stage == 2 and self.radius > 0:
 
                        self.circle_artist.set_edgecolor('black')  
                        self.radius_list.append(self.radius) 
                        fig.canvas.draw()

                        fig.canvas.mpl_disconnect(cid_click)
                        plt.close(fig)  
                        print(f"Center: {self.circle_coords}, Radii: {self.radius_list}")
                        print("Use the `plot_final_result()` method to plot the static result.")


        cid_click = fig.canvas.mpl_connect('button_press_event', on_click)

        plt.show()

    def plot_final_result(self):
        """Plot the static result with both circles."""
        if not self.circle_coords or len(self.radius_list) < 2:
            raise ValueError("Circle center and two radii must be selected using `interactive_circle_selection()` first.")

        fig_final, ax_final = plt.subplots(figsize=(6, 6))
        ax_final.imshow(self.data, cmap=self.cmap, vmin=self.vmin, vmax=self.vmax)


        first_radius = self.radius_list[0]
        first_circle = plt.Circle(self.circle_coords, first_radius, color='r', fill=False, lw=2)
        first_radius = np.round(self.radius_list[0],5)
        ax_final.add_artist(first_circle)


        second_radius = self.radius_list[1]
        second_circle = plt.Circle(self.circle_coords, second_radius, color='b', fill=False, lw=2)
        second_radius = np.round(self.radius_list[1], 5)
        ax_final.add_artist(second_circle)

        ax_final.set_title(f"Center: {np.round(self.circle_coords, 2)}\n"
                           f"Radius 1: {first_radius:.2f}, Radius 2: {second_radius:.2f}")

        plt.show()

    def calculate_average_intensity(self, bin_size=10, background = 0, plot = True):
        """Calculate the average intensity between two selected radii, binned by a specified number of degrees."""
        if len(self.radius_list) < 2:
            raise ValueError("Two radii must be defined before averaging intensities.")
        background = self.bkg
        self.bin = bin_size
        x0, y0 = self.circle_coords
        r_initial, r_final = sorted(self.radius_list)  
        num_bins = int(360 / self.bin)  
        angles = np.linspace(0, 2 * np.pi, num_bins + 1)
        angletotal = np.linspace(0, 2 * np.pi, 360)
        int_total = []
        for angle in angletotal:
            r_values = np.linspace(r_initial, r_final, 100)
            for r in r_values:
                x = int(x0 + r * np.cos(angle))
                y = int(y0 + r * np.sin(angle))
                if 0 <= x < self.data.shape[1] and 0 <= y < self.data.shape[0]:
                    int_total.append(self.data[y, x])
        if int_total:
            self.avg_int_total = np.mean(int_total)
        else:
            self.avg_int_total = 0

        intensities = []
        for i in range(num_bins):
            angle_start = angles[i]
            angle_end = angles[i + 1]
            intensity_at_bin = []

            for angle in np.linspace(angle_start, angle_end, 10):  
                r_values = np.linspace(r_initial, r_final, 100)
                for r in r_values:
                    x = int(x0 + r * np.cos(angle))
                    y = int(y0 + r * np.sin(angle))
                    if 0 <= x < self.data.shape[1] and 0 <= y < self.data.shape[0]:
                        intensity_at_bin.append(self.data[y, x])

            
            if intensity_at_bin:
                intensities.append(np.mean(intensity_at_bin))
            else:
                intensities.append(0)  

        self.avg_int_total = int_total
        self.avg_intensities_raw = intensities
        self.avg_intensities_sub = np.array(intensities) - background
        if plot == True:
            self.plot_intensities(angles[:-1], self.avg_intensities_sub, title = f"Integrated Intensity, ({self.bin} bins) \n Background Subtracted")  

    def plot_intensities(self, angles, intensities, title = "Averaged Intensity Over Circle Radii with Binning"):
        """Plot the average intensities over the circle radii."""
        plt.figure(figsize=(6, 4))
        plt.plot(np.degrees(angles), intensities)
        plt.title(title)
        plt.xlabel("Angle (degrees)")
        plt.ylabel("Intensity")
        plt.grid(True)
        plt.show()

    def polar_plot(self, norm = False, **kwargs):
        """Plot the data in polar coordinates."""
        if self.average_intensities_raw is None:
            raise ValueError("Two circles must be defined before plotting in polar coordinates. AND calculate average intensity.")
        num_bins = int(360 / self.bin)
        angles = np.linspace(0, 2 * np.pi, num_bins)
        fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
        num_bins = int(360 / self.bin)
        angles = np.linspace(0, 2 * np.pi, num_bins)
        ax.set_title("Averaged Intensity Over Circle Radii with Binning \n Background Subtracted")
        if norm == True:
            ax.plot(angles, self.avg_intensities_sub/np.max(self.avg_intensities_sub), **kwargs)
        else:
            ax.plot(angles, self.avg_intensities_sub, **kwargs)
        plt.show()

    def save_txt(self, folder_path: str, description: str):
        """
        Save data to a .txt file with the next available file number in the folder.
        
        The file will contain:
        1. A description provided by the user.
        2. Angular data (unbinned), raw intensity (unbinned),
        angular data (binned), intensity (binned and background-subtracted),
        raw intensity (binned, no background subtraction).
        
        Args:
            folder_path (str): Path to the folder where the .txt file will be saved.
            description (str): The description to include in the header of the .txt file.
        """
        # Create folder if it doesn't exist
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # Find the next available file number
        existing_files = [f for f in os.listdir(folder_path) if f.startswith('data') and f.endswith('.txt')]
        if existing_files:
            file_numbers = [int(f[4:-4]) for f in existing_files if f[4:-4].isdigit()]
            next_file_number = max(file_numbers) + 1
        else:
            next_file_number = 1
        
        # File name will be data#.txt
        file_name = f"data{next_file_number}.txt"
        file_path = os.path.join(folder_path, file_name)

        # Ensure the necessary data is available
        if len(self.avg_intensities_raw) == 0 or len(self.avg_intensities_sub) == 0:
            raise ValueError("No intensity data available. Run the intensity calculation method first.")
        
        # Generate the data for the file
        num_bins = int(360 / self.bin)
        binned_angles = np.linspace(0, 360, num_bins)
        unbinned_angles = np.linspace(0, 360, len(self.avg_int_total))
        
        with open(file_path, 'w') as f:
            # Write header
            f.write(f"Description: {description}\n")
            f.write("Unbinned Angle (degrees)\tRaw Intensity (Unbinned)\t"
                    "Binned Angle (degrees)\tBinned Intensity (Background Subtracted)\t"
                    "Binned Raw Intensity\n")
            
            # Write data
            for i in range(len(binned_angles)):
                unbinned_angle = unbinned_angles[i] if i < len(unbinned_angles) else ''
                raw_intensity_unbinned = self.avg_int_total[i] if i < len(self.avg_int_total) else ''
                binned_angle = binned_angles[i]
                binned_intensity_sub = self.avg_intensities_sub[i]
                binned_intensity_raw = self.avg_intensities_raw[i]

                f.write(f"{unbinned_angle}\t{raw_intensity_unbinned}\t{binned_angle}\t"
                        f"{binned_intensity_sub}\t{binned_intensity_raw}\n")

        print(f"Data saved to {file_path}")
