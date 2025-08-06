import pyautogui
import keyboard
import time

class Exporter:
    """
    Contains methods for exporting data and results
    """
    def __init__(self, simulation):
        self.sim = simulation

    # def export_to_measur(self):
    #     """
    #     Exports system profile data to MEASUR using pyautogui and user input.
    #     """
    #     print("Export Process Starting...")
    #     print("TO EXIT PROGRAM WHILE WRITING, MOVE MOUSE TO TOP LEFT CORNER")
    #     time.sleep(1)

    #     for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
    #         print('-'*80)
    #         print(f"\033[91mPLEASE ENSURE:\033[0m")
    #         print(f"\033[93mSelect Day Type\033[0m is set to \033[93m{day.upper()}\033[0m")
    #         print(f"\033[93mProfile Data Type\033[0m is set to \033[93mPower, kW\033[0m")
    #         print(f"\033[94mPress 'y' to continue...\033[0m")
    #         keyboard.wait('y')

    #         for comp in self.sim.get_compressors():
    #             if day not in comp.data:
    #                 continue  # skip this compressor for this day

    #             print(f"\033[91mPLEASE ENSURE:\033[0m The \033[93m0:00\033[0m field for \033[93m{comp.name}\033[0m is selected")
    #             print(f"\033[94mPress 'y' to continue...\033[0m")
    #             keyboard.wait('y')

    #             for value in comp.data[day].values():
    #                 pyautogui.typewrite(str(value))
    #                 pyautogui.press('tab')

    #     print(f"\033[92mEXPORT SUCCESSFUL\033[0m")

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