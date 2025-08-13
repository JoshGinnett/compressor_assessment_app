from matplotlib.figure import Figure

class Analyzer:
    """
    Holds all analysis functions, such as plotting, savings computations,  etc. 
    Needs a Simulation object to be initialized
    """
    def __init__(self, simulation):
        self.sim = simulation
        self.weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        self.total_kwh_savings = 0.0
        self.total_dollar_savings = 0.0

    def plot_consumption_by_day(self) -> Figure:
        """
        Plots compressor system power consumption average by day as a figure.
        """
        total_kwh = [0.0] * 7  # Monday → Sunday

        for comp in self.sim.get_compressors():
            for i, day in enumerate(self.weekday_order):
                interval_kwh = sum(comp.data[day].values()) * (self.sim.get_interval() / 60)  # convert to kWh
                total_kwh[i] += interval_kwh

        fig = Figure(figsize=(10, 6), dpi=100)
        ax = fig.add_subplot(111)
        ax.plot(self.weekday_order, total_kwh, label='Total System', linewidth=2.5)
        ax.set_title('Compressor System kWh Consumption by Day of the Week', fontsize=18)
        ax.set_xlabel("Day of Week", fontsize=16)
        ax.set_ylabel("Average Energy Consumption (kWh)", fontsize=16)
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.tick_params(axis='x', labelrotation=45, labelsize=14)
        ax.tick_params(axis='y', labelsize=14)
        fig.tight_layout()

        return fig

    def compute_shutdown_savings(self, schedule: dict):
        kwh_rate = self.sim.get_kwh_rate()
        # compressor savings data structure:
        """
        {
            "compressor_savings": {
                    "Compressor A": {
                        "Monday": 10.5,
                        "Wednesday": 5.2,
                        ...
                        "Total": Weekly total kWh savings
                        "Total $" : Weekly total $ savings
                        "Annual" : annual savings for this compressor
                        "Annual $": Annual $ savings for this compressor
                        },
                    ..
            },
            ...
        }
        """
        compressor_savings = {}
        for compressor in self.sim.get_compressors():
            day_savings = {}
            for day, intervals in schedule.items():
                if not intervals or day not in compressor.data:
                    continue

                saved = 0.0
                for start_str, end_str in intervals:
                    start_min = self._time_str_to_minutes(start_str)
                    end_min = self._time_str_to_minutes(end_str)

                    for time_str, value in compressor.data[day].items():
                        time_min = self._time_str_to_minutes(time_str)
                        if start_min <= time_min <= end_min:
                            saved += value * (self.sim.get_interval() / 60)

                day_savings[day] = round(saved, 2)

            total = sum(day_savings.values())
            day_savings["Total"] = round(total, 2)
            day_savings["Total $"] = round((total * kwh_rate), 2)
            day_savings["Annual"] = total * 52.1429
            day_savings["Annual $"] = (day_savings["Annual"] * kwh_rate)
            compressor_savings[compressor.get_name()] = day_savings

        # savings by day
        """
        {
            "Monday" : sum of kwh savings for monday
            "Tuesday": sum of kwh savings for tuesday
            ...
            "active days":
        }        
        """
        savings_by_day = {}
        for day, _ in schedule.items():
            for compressor, savings_dict in compressor_savings.items():
                savings_by_day[day] = savings_by_day.get(day, 0) + savings_dict.get(day, 0)

        total_week_kwh = sum(comp["Total"] for comp in compressor_savings.values())
        total_week_dollars = total_week_kwh * kwh_rate
        total_kwh = total_week_kwh * 52.1429
        total_dollars = total_kwh * kwh_rate

        return {
            "compressor_savings": compressor_savings,   # individual compressor savings by week data
            "savings_by_day": savings_by_day,           # toal kWh savings indexed by day
            "total_week_kwh": total_week_kwh,           # weekly total kWh savings
            "total_week_dollars": total_week_dollars,   # weekly total dollars
            "total_kwh": total_kwh,                     # annual kwh savings
            "total_dollars": total_dollars              # annual dollar savings
        }

    def _time_str_to_minutes(self, time_str):
        h, m = map(int, time_str.split(":"))
        return h * 60 + m
    
    def plot_power_consumption_by_interval(self) -> Figure:
        """
        Creates a line plot of compressor power consumption for Monday intervals.
        Vertical axis = power in kW, Horizontal axis = time interval (HH:MM).
        Each line represents a different compressor.
        """
        # Create the figure and axis
        fig = Figure(figsize=(10, 6), dpi=100)
        ax = fig.add_subplot(1, 1, 1)

        # Loop over compressors and plot their Monday data
        for compressor in self.sim.get_compressors():
            data = compressor.get_data()
            monday_data = data.get("Monday", {})

            if not monday_data:
                continue  # Skip if no Monday data

            # Extract intervals and values in given order
            intervals = list(monday_data.keys())
            values = list(monday_data.values())

            # Plot line using compressor's name for the label
            ax.plot(intervals, values, marker='o', label=compressor.get_name())

        # Set titles and labels
        ax.set_title("Power Consumption Over Time - Average Monday", fontsize=18)
        ax.set_xlabel("Time Interval", fontsize=16)
        ax.set_ylabel("Power (kW)", fontsize=16)

        # Remove horizontal padding (set x-axis limits tightly)
        ax.set_xlim(intervals[0], intervals[-1])

        # Rotate x-axis labels and right center for readability
        ax.tick_params(axis='x', rotation=45)
        for label in ax.get_xticklabels():
            label.set_horizontalalignment('right')

        # add grid
        ax.grid(True, linestyle='--', alpha=0.6)

        # Show legend
        ax.legend()

        # Optimize layout
        fig.tight_layout()

        return fig