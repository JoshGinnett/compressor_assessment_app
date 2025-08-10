import pyautogui

class Exporter:
    """
    Contains methods for exporting data and results
    """
    def __init__(self, simulation):
        self.sim = simulation

    def export_to_measur(self, day, export_compressors):
        """
        Exports a data for a given day and order of compressors to MEASUR using
        pyautogui to take over keyboard control.
        day = string for the day to export
        export_compressors = list of compressor objects to be exported
        """

        for compressor in export_compressors:
            data = compressor.get_data() # current compressors data
            if day not in data:
                continue
            for value in data[day].values():
                pyautogui.typewrite(str(value))
                pyautogui.press('tab')

    def print_all_results(self):
        """
        Prints all compressor results to out.txt
        """
        open("out.txt", 'w').close()    # clear the file
        with open("out.txt", 'a') as f:
            for compressor in self.sim.get_compressors():
                compressor.print_data_all_days(f)

    def get_all_results_text(self):
        output = []
        for compressor in self.sim.get_compressors():
            # Assuming print_data_all_days writes to a file-like object,
            # modify or add a version that returns string or write to StringIO
            from io import StringIO
            sio = StringIO()
            compressor.print_data_all_days(sio)
            output.append(sio.getvalue())
        return "\n".join(output)
    
    ### TODO : function that prints data to a different out.txt for data by day_types