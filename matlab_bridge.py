# AI Generated with tweeks.
# Overall. This file is pretty simple.
# This is here to make sure I open the MATLAB engine once and then reuse it
# as needed.. 
import matlab.engine

_engine = None

def getEngine():
    """Returns the active MATLAB engine, starting it if necessary."""
    global _engine
    if _engine is None:
        print("Starting MATLAB engine (this may take a few seconds)...")
        _engine = matlab.engine.start_matlab()
    return _engine

def stopEngine():
    """Cleanly shuts down the engine."""
    global _engine
    if _engine is not None:
        _engine.quit()
        _engine = None