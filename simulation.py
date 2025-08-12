class Simulation:
    """
    Stores general simulation information, such as kWh rate, main compressor
    list.
    """
    def __init__(self):
        self.interval = int()       # the interval for the simulation
        self._compressors = []      # master compressor object list
        self.kwh_rate = 0.0         # simulation kWh rate
        self._day_types = []        # the list of day types
        self.deployed_date= ""      # date the sensors were deployed
        self.collected_date = ""    # date the sensors were collected
        self.day_types = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']     # for future daytype support

    #### GET METHODS ####     
    def get_compressors(self):
        """
        Returns a reference to the list of compressor objects for this simulation.
        """
        return self._compressors

    def get_day_types(self):
        """
        Returns a reference to the list of day types.
        """
        return self._day_types

    def get_interval(self):
        return int(self.interval)

    def get_deployed_date(self):
        return str(self.deployed_date)

    def get_collected_date(self):
        return str(self.collected_date)
    
    def get_kwh_rate(self):
        return float(self.kwh_rate)

    def get_daytypes(self):
        return self.day_types

    #### SET METHODS ####
    def set_kwh_rate(self, rate):
        self.kwh_rate = float(rate)
        print(f"Set kWh rate to: {self.kwh_rate}")
    
    def set_interval(self, interval):
        self.interval = int(interval)
        print(f"Set interval to: {self.interval}")

    def set_deployed_date(self, deployed):
        self.deployed_date = str(deployed)
        print(f"Set deployed date to: {self.deployed_date}")

    def set_collected_date(self, collected):
        self.collected_date = str(collected)
        print(f"Set collected date to: {self.collected_date}")

    def set_compressors(self, compressors):
        self._compressors = compressors
        print(f"Set compressor list")

    def compute_power_buckets(self):
        """
        Computes the power buckets / fills data dictionaries for each compressor.
        """
        print("Processing Data...")
        try:
            for compressor in self._compressors:
                compressor.compute_power()
        except Exception as e:
            print(f"Error Processing Data for {compressor.get_name()}: {e}")
        else:
            print("Data Processed Successfully")

