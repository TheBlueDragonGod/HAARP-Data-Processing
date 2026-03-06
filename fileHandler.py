"""  
Handles files! Any and all! Saves them! Opens them! And deals with the
WONDERFUL WORLD OF MATLAB!!! HORRAY!!!
"""

import numpy as np
import pandas as pd
import scipy.io
from pathlib import Path
from datetime import datetime, timedelta
import h5py
from matlab_bridge import getEngine

class FileHandler:
    # ==============================================================================================
    @staticmethod
    def loadMatFile(filePath: Path) -> dict:
        # Takes a file path and returns two variables
        # fileContents (dict): All file data.
        
        # Checks if the file path is valid
        if not FileHandler.validFilePath(filePath):
            print(f"WARNING: Path is not a valid file: {filePath}")
            return None
        
        # Attempt to load the file
        try:
            fileContents = scipy.io.loadmat(str(filePath)) 
            
            # Check if file has information in it
            if not fileContents:
                print(f"WARNING: MAT file appears to be empty: {filePath.name}")
                return None
            
            # Clean, squeeze, and place the data into a dict
            cleanedData = {}
            for key, val in fileContents.items():
                if key.startswith('__'): continue # Skip internal MATLAB headers
                
                # Flatten (N, 1) arrays to (N,)
                if isinstance(val, np.ndarray):
                    val = np.squeeze(val)
                    
                    # Handle 0-d arrays (scalars wrapped in arrays)
                    if val.ndim == 0:
                        cleanedData[key] = val.item()
                    else:
                        cleanedData[key] = val
                else:
                    cleanedData[key] = val
    
            return cleanedData
        
        # Catch all other errors
        except (OSError, ValueError, KeyError) as e:  # Catch common loadmat exceptions
            print(f"ERROR: Failed to load MAT file '{filePath.name}': {e}")
            return None
        except Exception as e:  # Fallback for unexpected errors
            print(f"ERROR: Unexpected error loading MAT file '{filePath.name}': {e}")
            return None
    # ==============================================================================================
    @staticmethod
    def loadSpecificMatFileVariable(filePath: Path, variableName: str):
        # Checks if the file path is valid
        if not FileHandler.validFilePath(filePath):
            print(f"WARNING: Path is not a valid file: {filePath}")
            return None
        
        # Attempt to load only the specific variable
        try:
            fileContents = scipy.io.loadmat(str(filePath), variable_names=[variableName])  # Load only this variable
            
            if not fileContents:
                print(f"WARNING: MAT file appears to be empty or variable '{variableName}' not found: {filePath.name}")
                return None
            
            # Clean, squeeze, and place the data into a dict
            # Flatten (N, 1) arrays to (N,)
            if isinstance(fileContents[variableName], np.ndarray):
                val = np.squeeze(fileContents[variableName])
                
                # Handle 0-d arrays (scalars wrapped in arrays)
                if val.ndim == 0:
                    val = val.item()
    
            return val
        
        except (OSError, ValueError, KeyError) as e:  # Catch common loadmat exceptions
            print(f"ERROR: Failed to load variable '{variableName}' from MAT file '{filePath.name}': {e}")
            return None
        except Exception as e:  # Fallback for unexpected errors
            print(f"ERROR: Unexpected error loading variable '{variableName}' from MAT file '{filePath.name}': {e}")
            return None
    # ==============================================================================================
    @staticmethod
    def saveDataToMatFile(data:dict, saveDirectory:Path) -> None:        
        try:
            # This skips all the Python internal junk that can come up when
            # loading a .mat file.
            dataToSave = {}
            for key, val in data.items():
                if key.startswith('__'): continue # Skip internal attributes
                dataToSave[key] = val
        
            # Actually save the data
            scipy.io.savemat(saveDirectory, dataToSave, do_compression=True)
            
        except Exception as e:
            print(f"ERROR: Failed to save .mat file: {e}")
            return None
            
    # ==============================================================================================
    @staticmethod
    def saveToH5(data_:dict, startTime, scheduleType, fileName = "RESULTS.h5", compression_ = "gzip"):
        # Assumes data to be of form of (not exactly, the following is an example):
        # ORIGINAL DATA DICTIONARY (data_)
        #     │
        #     ├─── Key: "Frequencies" 
        #     │    └─── Value: { 
        #     │           "Data": np.array([...]), 
        #     │           "Unit": "Hz", 
        #     │           "Description": "FFT Bins" 
        #     │         }
        #     │
        #     └─── Key: "Amplitudes"
        #         └─── Value: { 
        #                 "Data": np.array([...]), 
        #                 "Unit": "V/m", 
        #                 "Scaling": "Linear" 
        #             }
        #
        # Saves the file as
        
        
        groupName = f"{scheduleType}_{startTime.strftime('%Y-%m-%d_%H-%M-%S')}"
        
        with h5py.File(fileName, "a") as f:
            
            if groupName in f:
                del f[groupName] # Overwrite existing data
                
            group = f.create_group(groupName)
            
            names = list(data_.keys())
            for name, content in data_.items():
                
                if content.get("Data") is None: continue # Skip empty data
                
                group.create_dataset(str(name), data=content.get("Data"), compression = compression_)
                
                for attrName, attrValue in data_.items():
                    if attrName != "Data":
                        group.attrs[f"{name}_{attrName}"] = str(attrValue)
    # ==============================================================================================
    def loadH5(fileName):
        # Should load the files saved with the save function. We will see
        fullResults = {}
        
        with h5py.File(fileName, "r") as f:
            for groupName in f.keys():
                group = f[groupName]
                data = {}
                
                for dsName in group.keys():
                    data[dsName] = {"Data": group[dsName][:]}
                    
                for attrName, attrValue in group.attr.items():
                    parts = attrName.split("_", 1)
                    if len(parts) == 2:
                        name, attrKey = parts
                        if name in data:
                            data[name][attrKey] = attrValue
                            
                fullResults[groupName] = data
                
            return fullResults
    # ==============================================================================================
    
    # ==============================================================================================
    
    # ==============================================================================================
    @staticmethod
    def validFilePath(filePath: Path) -> bool:
        # Check if it's actually a file (not a directory)
        if not filePath.is_file():
            return False
        
        # Check if the path exists
        if not filePath.exists():
            return False
        
        return True
    # ==============================================================================================
    @staticmethod
    def getVariableInfo(filePath: Path) -> pd.DataFrame:
        info = {}
        # First, try using scipy. Only works on older formatted files.
        try:
            rawInfo = scipy.io.whosmat(filePath)
            for name, shape, dtype in rawInfo:
                info[name] = [shape, dtype]
        # Next, try using h5py as it works with newer file formats.
        except:
            try:
                with h5py.File(filePath) as f:
                    for name in f.keys():
                        obj = f[name]
                        if isinstance(obj, h5py.Dataset):
                            info[name] = [obj.shape, str(obj.dtype)]
            except:
                eng = getEngine()
                eng.eval(f"info = whos('-file', '{str(filePath)}');", nargout=0)
                names = eng.eval("{info.name}")
                types = eng.eval("{info.class}")
                sizes = eng.eval("{info.size}")
                
                # Convert sizes into proper formatting. It gets returned in a really weird
                # Format.
                # It is essentially a list of matlab.double objects inside matlab.double objects.
                # Which can be treated as lists.
                # I am trying to convert them to ints before passing back.
                # However, some items have zero length. Currently, those are just empty.
                # I wonder if that will bite me in the ass?
                newSizes = []
                for size in sizes:
                    try:
                        newSizes.append([int(item) for item in size[0]])
                    except:
                        newSizes.append(None)  
                
                for name, dtype, shape in zip(names, types, sizes):
                    info[name] = [shape, dtype]
        
        return pd.DataFrame(info, index = ["Shape", "Data Type"]).transpose()
        
    # ==============================================================================================
    @staticmethod
    def getSizeOfVariable(filePath: Path, variable: str) -> tuple:
        fs = FileHandler.loadSpecificMatFileVariable(filePath, "Fs")
        info = FileHandler.getVariableInfo(filePath) # This grabs the information about the file variables.
        # I have to check the type of the variable depending on how the file gets opened.
        # WE LOVE MATLAB!!!!!!!! WHOOOOOOOOOOOOOOOOOOOOOO
        if type(info.loc[variable, "Shape"]) == list:
            return info.loc[variable, "Shape"]
        else:
            return info.loc[variable, "Shape"][0]
    # ==============================================================================================
    @staticmethod
    def grabAllFilePairs(dataFilePath:Path) -> list:
        
        # MAKING THE GOD AUFUL ASSUMPTION THAT EACH FILE ACTUALLY HAS A PAIR!
        files = sorted([item for item in dataFilePath.glob('*.mat') if item.is_file()])
        
        # Pretty sure this wont work I need to check this later.
        # TODO Actually check if the files each have a pair.
        # NSFiles = files[::2]
        # EWFiles = files[1::2]
        
        # files = []
        # for i in range(len(NSFiles)):
        #     NSFileName = NSFiles[i].name
        #     EWFileName = EWFiles[i].name
            
        #     # Check if the file names match excluding the 
        #     if NSFileName[-6:-len(NSFileName):-1] == EWFileName[-6:-len(EWFileName):-1]:
        #         files.append(NSFileName)
        #         files.append(EWFileName)
        
        return files
            
            
        
    # ==============================================================================================
    def getFileStartAndStop(file: Path) -> dict:
        fileName = file.name
        year       = int(fileName[2:4]) + 2000
        month      = int(fileName[4:6])
        day        = int(fileName[6:8])
        hour       = int(fileName[8:10])
        minute     = int(fileName[10:12])
        second     = int(fileName[12:14])
        
        fileStartDate = datetime(year, month, day, hour, minute, second)
        
        fs = FileHandler.loadSpecificMatFileVariable(file, "Fs")
        numberOfSamples = FileHandler.getSizeOfVariable(file, "data")[0]
        secondsOfData = timedelta(seconds = numberOfSamples / fs)
        
        fileStopDate = fileStartDate + secondsOfData
        
        return {"Start Time":fileStartDate, "Stop Time":fileStopDate}
        
# ==============================================================================================
    
    
# STRICTLY FOR TESTING
if __name__ == "__main__":
    filePath = r"A:\OneDrive - The University of Colorado Denver\Work\RA Position Stuff\HAARP Analysis\2025 PAARS Analysis\Data\DregionVLF\AK250813014500_000.mat"
    filePath = Path(filePath)
    fileData = FileHandler.loadMatFile(filePath)
    for key in fileData:
        print(f"- {key}")
    
    exampleFilePath = Path.cwd() / "Sample.mat"
    FileHandler.saveDataToMatFile(fileData, exampleFilePath)
    
    fileDataToCompare = FileHandler.loadMatFile(exampleFilePath)
    
    originalKeys = fileData.keys()
    keysToCompare = fileDataToCompare.keys()
    for key in keysToCompare:
        if key not in originalKeys:
            print(f"Missing key: {key}")
        else: 
            print(f"Located key: {key}", end=", ")
            
            if fileData[key].all() == fileDataToCompare[key].all():
                print("Internal Data Matches!")
            else:
                print("Internal Data Mismatched!")
            
    
    