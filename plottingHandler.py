"""
This is where plotting functions go. Not much to say beyond they shouldn't do any math or processing.
"""
import numpy as np
from scipy import signal
from scipy import signal
import constants as CONSTANT
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use('Agg') # Uninteractive backend

class PlottingHandler:
    @staticmethod
    def plotBasicSpectrogram(data, fs, customTitle="Spectrogram of Input Data", directory = CONSTANT.PLOTDIRECTORY):
        """
        Creates and plots a spectrogram for the given input data.
        """
        print(f"Plotting {customTitle}")
        # Spectrogram Parameters
        windowLength = 256
        overlapLength = int(np.round(windowLength * 0.5))
        nfft = windowLength

        # Generate Spectrogram
        # nperseg is window length, noverlap is overlap length
        f, t, Sxx = signal.spectrogram(
            data, 
            fs=fs, 
            window='hann', 
            nperseg=windowLength, 
            noverlap=overlapLength, 
            nfft=nfft,
            detrend=False,
            return_onesided=not np.iscomplexobj(data)
        )

        # Display Plot
        plt.figure(figsize=(10, 6))
        # use pcolormesh for the heatmap; shading='gouraud' approximates MATLAB's look
        plt.pcolormesh(t, f, 10 * np.log10(Sxx + 1e-20), shading='gouraud', cmap='viridis')
        
        plt.title(customTitle)
        plt.ylabel('Frequency [Hz]')
        plt.xlabel('Time [sec]')
        plt.colorbar(label='Intensity [dB]')
        plt.tight_layout()
        
        plt.savefig(str(directory / (f"{customTitle}.png")), dpi=300)
        plt.close()
        
    @staticmethod
    def plot_line(x, y, x_label="Time", y_label="Amplitude", title="Signal Plot", filename="linear_plot.png"):
        """
        Plots a simple linear line and saves it to disk.
        """
        plt.figure(figsize=(10, 6))
        
        # Create the plot
        plt.plot(x, y, color='blue', linewidth=1.5, label='Signal')
        
        # Custom Labels and Title
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.title(title)
        
        # Add a grid - helpful for checking pulse alignment
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # Save the figure
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close() # Close to free up memory during large analysis loops
        print(f"Plot saved as {filename}")