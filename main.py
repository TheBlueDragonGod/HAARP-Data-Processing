# Author Gabriel da Silva
# Purpose: Code to analyze ELF and VLF data generated using HAARP.
'''
The code takes a folder directory containing data 
The data files can be either collected matlab scripts (.mat) created following the
WALDO format described here: https://waldo.world/description-of-data/

The code then analyzes the data based on some defined schedule
The output is general plots along with data files and numbers

NOTE: Most of my logic relies on using the date time objects as index values.
Calculate time stamps for every action
Sort based on these timestamps
Then begin processing based on these timestamps
'''
# Import my custom files
import constants as CONSTANT
from scheduleHandler import ScheduleHandler
from dataHandler import DataHandler
from plottingHandler import PlottingHandler
from TimeArray import TimeArray
from DSP import DSP

# Import general libraries
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
import traceback

import matlab_bridge as mb


# FORMAT DATA
# Taking the data I do have in combination with the information I already know to put the data
# in an easier to process format.
# Locate Files
# I will use the constants for this for now. I would 
# like to implement a directory searcher or something like that
# eventually.

# Select Schedule to Process the Files
# this will be a processed list of data frames. Each data frame will be
CONSTANT.mainSchedule = ScheduleHandler.defineNovember2025HAARPSchedule()
subScheduleStartTimes = list(CONSTANT.mainSchedule.keys())
print("Schedule defined.")

# Grab Relevant Data corresponding to the schedule
data, globalStartTime, globalStopTime = DataHandler.grabRelevantData(CONSTANT.scheduleStartTime, CONSTANT.scheduleStopTime, CONSTANT.DATAFILEPATH)
# Convert into my custom Time Array to allow for time indexing.
data = TimeArray(data, globalStartTime, CONSTANT.fs)

# Plot the Initial Data
# if CONSTANT.DEBUG: PlottingHandler.plotBasicSpectrogram(data, CONSTANT.fs, "Full November Data Initial Plot Python")
print("Relevant Data Collected...")

# Check for missing data. Mark them as incomplete. Incomplete sections will be skipped in future sections as
# Missing data will cause significant issues.
validStartTimes, invalidStartTimes = DataHandler.validateEachSubSchedule(CONSTANT.mainSchedule, data)
print("Validated each subschedule. Processing only valid data...")

# For expirementing: datetime.datetime(2025, 11, 20, 3, 12, 53) is the start of invalid data
#                    datetime.datetime(2025, 11, 20, 3, 12, 54, 999990) is the end.

# I can't deal with invalid data right now
# I'm still saving the invalid subschedule information in case I decide to address it later
# TODO: Deal with the invalid schedules in a more elegant way.

# DONE FORMATTING
# I now have a data variable that correspponds to my requested time window. I have a schedule variable that contains the
# format of the expirement. And finally I have a list of the valid and invalid sub schedules. TIME TO PROCESS!

# PreProcess Data
# Only processing the valid data for now.
for startTime in validStartTimes:
    try:
        subSchedule = CONSTANT.mainSchedule[startTime]
        stopTime = ScheduleHandler.subScheduleStopTime(subSchedule, startTime)
        
        
        basePlotName = f"{startTime.strftime('%Y-%m-%d_%H-%M-%S')}_{subSchedule.at[0, 'Type']}"
        
        # Extract the subschedule and normalize
        subScheduleData = DSP.normalize(data[startTime:stopTime])
        print("Normalized.")
        
        # Humstractor. Extract noise.
        subScheduleData = DSP.extractHum(subScheduleData, CONSTANT.fs)
        if CONSTANT.DEBUG: PlottingHandler.plotBasicSpectrogram(subScheduleData, CONSTANT.fs, f"{basePlotName}_Humstracted", False)
        print("Hum extracted from data.")

        # Resample.
        subScheduleData = DSP.resample(subScheduleData, CONSTANT.fs, CONSTANT.resampleFrequency)
        if CONSTANT.DEBUG: PlottingHandler.plotBasicSpectrogram(subScheduleData, CONSTANT.resampleFrequency, f"{basePlotName}_Resampled", False)
        print("Data Resampled.")

        # Process
        # Pull Frequency Data out based on Schedule
        # Raw Data, Main Schedule -> Frequency and Amplitude Over Time
        freqs, amps = DataHandler.extractAmpsAndFreqsBasedOnSchedule(subScheduleData, globalStartTime, subSchedule, CONSTANT.resampleFrequency)
        print("Amplitude and Frequencies extracted.")
        
        # Plotting
        print("Plotting...")
        PlottingHandler.plotBasicSpectrogram(subScheduleData, CONSTANT.resampleFrequency, basePlotName)
        PlottingHandler.plot_line(freqs, amps, x_label = "Freqs (Hz)", title = basePlotName, filename = str(CONSTANT.PLOTDIRECTORY / (basePlotName + "_Freqs_vs_Amps" + ".png")))
        print("Plotted.")
    except KeyboardInterrupt:
        print("\nManual stop detected. Exiting loop...")
        break
        
    except Exception as e:
        print(f"\n[!] ERROR processing schedule at {startTime}:")
        print(f"Details: {e}")
        # Optional: use traceback to see exactly which line failed
        traceback.print_exc()
        continue

mb.stopEngine()
