import warnings
import pandas as pd
from pandas.errors import DtypeWarning


# CONSTANTS
SQRT_3 = 1.732050808

class Compressor:
    """
    Compressor class stores data for each compressor in the system including
    the compressor name, voltage, and it's power values.
    """
    def __init__(self, name, simulation, voltage, file_path):
        self.name = name        # name of the compressor    
        self.voltage = voltage  # voltage for compressor
        self.file_path = file_path     # file path for compressor data
        self.current_column = ""                # stores the name of the current column as a string
        self.sim = simulation           # reference to the simulation this compressor belongs to

        """
        {
        "Day 1" : {
                '00:00' : XX.XX     # interval 0
                '01:00' : XX.XX     # interval 1
                ...
                'n:00'  : XX.XX     # interval n
            },
        # ... Other Days
        
        """
        self.data = dict(dict())    # compressor power data
        self.df = pd.DataFrame()    # compressor pandas data frame

    def get_name(self):
        """
        Returns compressor name
        """
        return self.name

    def get_data(self):
        return self.data

    def set_file_path(self, path):
        """
        Sets the file path for this compressor.
        """
        self.file_path = path

    def construct_data(self):
        """
        Constructs the compressors power dicitonary given an interval.
        """
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        intervals = [f"{h:02d}:{m:02d}" for h in range(24) for m in range(0, 60, self.sim.get_interval())]
        self.data = {day: dict.fromkeys(intervals, 0.0) for day in weekdays}

    def build_df(self):
        """
        Builds the dataframe for this compressor and trims it.
        """
        cols = ['Date-Time (EDT)']  # columns to read

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DtypeWarning)
            df_sample = pd.read_csv(self.file_path, nrows=1)  # peek to get full column names
            amp_col = next((col for col in df_sample.columns if "amp" in col.lower()), None)
            # find amp columns
            if amp_col:
                self.current_column = amp_col
                cols.append(amp_col)
            # read csv (only necessary columns)
            self.df = pd.read_csv(self.file_path, usecols=cols, parse_dates=['Date-Time (EDT)'])
        
        # add DateTime column to data frame and drop rows missing date time info
        self.df['DateTime'] = pd.to_datetime(self.df['Date-Time (EDT)'], format='%m/%d/%Y %H:%M:%S')
        self.df.dropna(subset=['DateTime'], inplace=True)   # drop invalid date-time columns

        # check that df is valid
        if self.df.empty:
            raise ValueError("DataFrame is empty after dropping rows with invalid dates.")

        # trim df for deploy date, collected date
        deployed_dt = pd.to_datetime(self.sim.get_deployed_date()).date()
        collected_dt = pd.to_datetime(self.sim.get_collected_date()).date()
        mask = (self.df['DateTime'].dt.date > deployed_dt) & (self.df['DateTime'].dt.date < collected_dt)
        self.df = self.df.loc[mask]
    
    def destroy_df(self):
        """
        Destroys the data frame for this compressor to free memory.
        """
        try:
            del self.df
        except AttributeError:
            raise RuntimeError("Data Frame Does Not Exist")

    def compute_power(self):
        """
        Computes the power buckets and fills data dictionary.
        """
        # build the data frame and add columns needed for power computations
        self.build_df()
        self.df['WeekdayName'] = self.df['DateTime'].dt.day_name()
        floor_str = f"{self.sim.get_interval()}min"  # for df interval building
        self.df['Interval'] = self.df['DateTime'].dt.floor(floor_str).dt.strftime('%H:%M')

        # compute and fill dict
        self.construct_data()  # initialize data dictionary

        # group by weekday and interval, then compute the mean current
        grouped = self.df.groupby(['WeekdayName', 'Interval'])[self.current_column].mean().reset_index()

        # convert average current to power in kW
        grouped['Power_kW'] = (grouped[self.current_column] * self.voltage * SQRT_3 / 1000).round(2)

        # convert grouped data to nested dictionary (day -> interval -> power_kw)
        nested_dict = (
            grouped
            .set_index(['WeekdayName', 'Interval'])['Power_kW']
            .unstack(fill_value=0)  # missing intervals will get 0
            .to_dict(orient='index')
        )

        # update self.data with calculated power values
        for day, interval_dict in nested_dict.items():
            if day in self.data:
                self.data[day].update(interval_dict)

        # free memory 
        self.destroy_df()
        del grouped

    def print_data_all_days(self, file):
        """
        Prints data dictionary neatly to output file
        """
        file.write(f"{self.name}:\n") # write the compressor name

        # write the compressor data
        for day in self.data:
            file.write(f"   {day}:\n")
            for interval in self.data[day]:
                value = self.data[day][interval]
                file.write(f"       {interval}: {value:.2f} kW\n")
            file.write("\n")
        file.write('-'*160)
        file.write("\n")  # space between compressors
