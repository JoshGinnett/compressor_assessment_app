import tkinter as tk
import threading
import os
from datetime import datetime
from tkinter import messagebox, ttk, filedialog
from tkcalendar import DateEntry
from simulation import Simulation
from compressor import Compressor
from exporter import Exporter
from analyzer import Analyzer
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

class CompressorFrame(ttk.Frame):
    def __init__(self, parent, simulation, can_remove=True, remove_callback=None):
        super().__init__(parent, style="Compressor.TFrame", relief=tk.RIDGE, borderwidth=2, padding=10)
        self.sim = simulation
        self.remove_callback = remove_callback
        
        # Compressor Name
        ttk.Label(self, text="Name:", style="Compressor.TLabel").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.name_entry = ttk.Entry(self, width=20, foreground="#000000", font=("Segoe UI", 11))
        self.name_entry.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        # Voltage
        ttk.Label(self, text="Voltage:", style="Compressor.TLabel").grid(row=0, column=2, sticky=tk.W, padx=10, pady=2)
        self.voltage_entry = ttk.Entry(self, width=10, foreground="#000000", font=("Segoe UI", 11))
        self.voltage_entry.grid(row=0, column=3, sticky=tk.W, pady=2)
        
        # File selector
        ttk.Label(self, text="Data File:", style="Compressor.TLabel").grid(row=1, column=0, sticky=tk.W, pady=2)

        file_frame = ttk.Frame(self)
        file_frame.configure(style="Compressor.TFrame")
        file_frame.grid(row=1, column=1, columnspan=3, sticky="ew", pady=2)
        file_frame.columnconfigure(1, weight=1)  # Let the label expand

        self.file_path_var = tk.StringVar(value="No file selected")

        browse_button = ttk.Button(file_frame, text="Browse...", style="Compressor.TButton", command=self.browse_file)
        browse_button.grid(row=0, column=0, sticky=tk.W)

        self.file_label = ttk.Label(
            file_frame,
            textvariable=self.file_path_var,
            style="Compressor.TLabel",
            anchor="w"
        )
        self.file_label.grid(row=0, column=1, sticky="ew", padx=(10, 0))

        # Remove button
        if can_remove:
            self.remove_button = ttk.Button(self, text="Remove", style="Compressor.TButton", command=self.remove_self)
            self.remove_button.grid(row=0, column=4, rowspan=3, padx=10, sticky=tk.N)
        else:
            ttk.Label(self, text="", style="Compressor.TLabel").grid(row=0, column=4, rowspan=3, padx=10)

        self.columnconfigure(3, weight=1)

    def browse_file(self):
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        filepath = filedialog.askopenfilename(title="Select Compressor Data File", initialdir=downloads_path, filetypes=[("CSV files", "*.csv")])
        if filepath:
            self.file_path_var.set(filepath)

    def remove_self(self):
        if self.remove_callback:
            self.remove_callback(self)

    def get_compressor_data(self):
        """
        Validate and return a Compressor instance with the current UI data.
        Raises ValueError with appropriate message if validation fails.
        """
        name = self.name_entry.get().strip()
        voltage_str = self.voltage_entry.get().strip()
        file_path = self.file_path_var.get().strip()

        if not name:
            raise ValueError("Compressor name is required.")

        if not voltage_str.isdigit():
            raise ValueError(f"Voltage for compressor '{name or 'Unnamed'}' must be a valid integer.")

        if not os.path.isfile(file_path) or file_path == "No file selected":
            raise ValueError(f"A valid data file must be selected for compressor '{name}'.")

        voltage = int(voltage_str)

        return Compressor(name=name, simulation=self.sim, voltage=voltage, file_path=file_path)

class ShutdownSchedulerWidget(ttk.Frame):
    def __init__(self, parent, interval_minutes=15, on_change=None):
        super().__init__(parent)
        self.interval = interval_minutes
        self.on_change = on_change
        self.cell_states = {}
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        self.time_blocks = self._generate_time_blocks()

        self.dragging = False
        self.drag_toggled_cells = set()

        # Create a canvas
        # Calculate total width for full week
        self.cell_size_x = 140  # Slightly wider for clarity
        self.cell_size_y = 30
        self.time_col_width = 60  # or some smaller width than cell_size_x (which is 120)

        total_width = self.time_col_width + self.cell_size_x * len(self.days)
        total_height = self.cell_size_y * (len(self.time_blocks) + 3)  # +2 for headers


        self.canvas = tk.Canvas(self, bg="#000e2f", highlightthickness=0, height=total_height, width=total_width)
        self.canvas.pack(side="top", fill="both", expand=True)

        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self.canvas.bind("<B1-Motion>", self._on_drag_move)
        self.canvas.bind("<ButtonRelease-1>", self._on_drag_end)


        self._draw_grid()

    def _generate_time_blocks(self):
        blocks = []
        total_minutes = 24 * 60
        for minute in range(0, total_minutes, self.interval):
            hour = minute // 60
            min_in_hour = minute % 60
            blocks.append(f"{hour:02d}:{min_in_hour:02d}")
        return blocks

    def _set_column(self, day):
        # Check if any cell is currently OFF (False)
        any_off = any(not self.cell_states[(day, time_str)] for time_str in self.time_blocks)

        # Decide new state: if any off, turn all ON, else turn all OFF
        new_state = True if any_off else False

        for time_str in self.time_blocks:
            key = (day, time_str)
            self.cell_states[key] = new_state
            new_color = "red" if new_state else "green"
            self.canvas.itemconfig(self.cell_rects[key], fill=new_color)
        
        if self.on_change:
            self.on_change()

    def _draw_grid(self):
        self.canvas.delete("all")
        self.cell_rects = {}

        # Draw day labels with some padding
        for col, day in enumerate(self.days):
            btn = tk.Button(
                self.canvas,
                text=day,
                command=lambda d=day: self._set_column(d),
                bg="#000e2f",
                fg="#ffffff",
                font=("Segoe UI", 10, "bold"),
                relief="flat",
                cursor="hand2",
                takefocus=0
            )
            x = self.time_col_width + col * self.cell_size_x + self.cell_size_x / 2
            self.canvas.create_window(x, 5, window=btn, anchor="n")

        # Draw time labels and grid rectangles
        for row, time_str in enumerate(self.time_blocks):
            y = (row + 1) * self.cell_size_y + 40  # shifted down a bit for day labels
            # Time label, right aligned inside time column
            self.canvas.create_text(self.time_col_width - 5, y, text=time_str, anchor="ne", fill="white", font=("Segoe UI", 9))


            for col, day in enumerate(self.days):
                x = self.time_col_width + col * self.cell_size_x
                rect = self.canvas.create_rectangle(
                    x, y,
                    x + self.cell_size_x, y + self.cell_size_y,
                    fill="green", outline="#444"
                )
                self.cell_rects[(day, time_str)] = rect
                self.cell_states[(day, time_str)] = False

    def _toggle_cell_at(self, x, y):
        for (day, time_str), rect in self.cell_rects.items():
            if (day, time_str) in self.drag_toggled_cells:
                continue

            coords = self.canvas.coords(rect)
            x1, y1, x2, y2 = coords
            if x1 <= x <= x2 and y1 <= y <= y2:
                self.cell_states[(day, time_str)] = not self.cell_states[(day, time_str)]
                new_color = "red" if self.cell_states[(day, time_str)] else "green"
                self.canvas.itemconfig(rect, fill=new_color)
                self.drag_toggled_cells.add((day, time_str))
                if self.on_change:
                    self.on_change()
                return

    def _on_click(self, event):
        self.drag_toggled_cells.clear()
        self._toggle_cell_at(event.x, event.y)
    
    def _on_drag_start(self, event):
        self.dragging = True
        self.drag_toggled_cells.clear()
        self._toggle_cell_at(event.x, event.y)

    def _on_drag_move(self, event):
        if self.dragging:
            self._toggle_cell_at(event.x, event.y)

    def _on_drag_end(self, event):
        self.dragging = False
        self.drag_toggled_cells.clear()

    def get_schedule(self):
        """
        Converts the red-highlighted time blocks into shutdown intervals.
        Returns: dict[day] = list of (start_time, end_time)
        """
        schedule = {day: [] for day in self.days}

        for day in self.days:
            current_interval = None
            for time_str in self.time_blocks:
                active = self.cell_states[(day, time_str)]
                if active:
                    if current_interval is None:
                        current_interval = [time_str, time_str]
                    else:
                        current_interval[1] = time_str
                else:
                    if current_interval:
                        schedule[day].append(tuple(current_interval))
                        current_interval = None
            if current_interval:
                schedule[day].append(tuple(current_interval))

        return schedule

class Interface(tk.Tk):
    def __init__(self):
        super().__init__()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True)

        self.title("Compressor System Assessment")
        self.geometry("1920x1080")
        self.configure(bg="#000e2f")    # Background Set
        self.iconphoto(False, tk.PhotoImage(file='logo.png'))

        # setup ttk for the whole app
        style = ttk.Style(self)
        style.theme_use('clam')
        
        style.theme_settings("clam", {
            "TEntry": {
                "configure": {"fieldbackground": "#ffffff", "foreground": "#000000", "bordercolor": "#AAAAAA"}
                }
            }
        )

        # Colors for labels, buttons, entries
        # -- main styling
        style.configure("TLabel", background="#000e2f", foreground="#ffffff", font=("Segoe UI", 12))
        style.configure("TButton", background="#000e2f", foreground="#ffffff", font=("Segoe UI", 12, "bold"))
        style.map("TButton", foreground=[('pressed', '#000e2f'), ('active', '#000e2f')], background=[('pressed', '#ffffff'), ('active', '#ffffff')])
        style.configure("TMenubutton", background= "#ffffff", foreground="#000000", font=("Segoe UI", 11), relief="raised")
        style.configure("Comp.TButton", background="#000e2f", foreground="#ffffff", font=("Segoe UI", 11))
        style.configure("CompSelected.TButton", background="#ffffff", foreground="#000e2f", font=("Segoe UI", 11))


        # -- compressor frame style
        style.configure("Container.TFrame", background="#000e2f")
        style.configure("Compressor.TFrame", background="#000e2f")
        style.configure("Compressor.TLabel", background="#000e2f", foreground="#ffffff")
        style.configure("Compressor.TButton", background="#000e2f", foreground="#ffffff", font=("Segoe UI", 12))
        # -- notebook styling
        style.configure("TNotebook", background="#000e2f", borderwidth=0)
        style.configure("TNotebook.Tab", background="#000e2f", foreground="#ffffff", padding=[10, 5])
        style.map("TNotebook.Tab", background=[("selected", "#000e2f")], foreground=[("selected", "#ffffff")])
        style.configure("TNotebook.Tab", font=("Segoe UI", 12))
        style.configure("TNotebook.Tab", borderwidth=0)
        
        self.sim = Simulation() # Main instance of the simulation

        self.create_widgets()
        self.compressor_frames = []
        self.add_compressor_frame(can_remove=False) # initial unremovable compressor frame

    def create_widgets(self):
        # --- Setup Tab ---
        self.setup_tab, self.scrollable_setup, self.setup_canvas = self.create_scrollable_tab("Setup")

        # --- kWh Rate + Interval in a clean grid ---
        form_frame = ttk.Frame(self.scrollable_setup, style="Container.TFrame")
        form_frame.pack(pady=10, padx=10, anchor="w")  # Align left

        # kWh Rate
        ttk.Label(form_frame, text="kWh Rate:").grid(row=0, column=0, padx=(0, 5), pady=5, sticky="e")
        self.kwh_entry = ttk.Entry(form_frame, font=("Segoe UI", 11), width=13)
        self.kwh_entry.grid(row=0, column=1, pady=5, sticky="w")

        # Interval
        ttk.Label(form_frame, text="Bucket Size / Interval:").grid(row=1, column=0, padx=(0, 5), pady=5, sticky="e")
        self.interval_options = {
            "15 Minutes": 15,
            "30 Minutes": 30,
            "Hour": 60
        }
        self.interval_var = tk.StringVar(self)
        self.interval_var.set("15 Minutes")

        self.interval_menu = ttk.OptionMenu(form_frame, self.interval_var, "15 Minutes", *self.interval_options.keys())
        self.interval_menu.grid(row=1, column=1, pady=5, sticky="w")

        self.interval_menu["menu"].config(
            font=("Segoe UI", 11),
            background="#ffffff",
            foreground="#000000",
            activebackground="#ffffff",
            activeforeground="#000000",
        )

        # Deployed Date
        ttk.Label(form_frame, text="Sensor Deployed Date:").grid(row=2, column=0, padx=(0, 5), pady=5, sticky="e")
        self.deployed_date_entry = DateEntry(form_frame, width=12, background="#AAAAAA",
                                            foreground="#000000", borderwidth=2, date_pattern='mm/dd/yyyy',
                                            showweeknumbers=False, font=('Segoe UI', 11))
        self.deployed_date_entry.grid(row=2, column=1, pady=5, sticky="w")

        # Collected Date
        ttk.Label(form_frame, text="Sensor Collected Date:").grid(row=3, column=0, padx=(0, 5), pady=5, sticky="e")
        self.collected_date_entry = DateEntry(form_frame, width=12, background="#AAAAAA",
                                            foreground="#000000", borderwidth=2, date_pattern='mm/dd/yyyy',
                                            showweeknumbers=False, font=('Segoe UI', 11))
        self.collected_date_entry.grid(row=3, column=1, pady=5, sticky="w")
        self.collected_date_entry.configure(background="#AAAAAA", foreground="#000000")

        # --- Container Frame for Compressor Data
        self.comp_container = ttk.Frame(self.scrollable_setup, style="Container.TFrame")
        self.comp_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Frame inside comp_container to hold compressor frames and the add button
        self.comp_inner_frame = ttk.Frame(self.comp_container, style="Container.TFrame")
        self.comp_inner_frame.pack(fill=tk.X, expand=False)

        # Add Compressor Button below compressor frames, packed inside comp_inner_frame
        self.add_compressor_button = ttk.Button(self.comp_container, text="Add Compressor", command=self.add_compressor_frame)
        self.add_compressor_button.pack(pady=5)

        # Run Simulation Button
        self.run_button = ttk.Button(self.scrollable_setup, text="Run Simulation", command=self.run_simulation)
        self.run_button.pack(pady=20)

        # Status Label
        self.status_label = ttk.Label(self.scrollable_setup, text="", foreground="#ffffff", background="#000e2f")
        self.status_label.pack()

        # Progress bar (indeterminate mode for ongoing task)
        self.progress = ttk.Progressbar(self.scrollable_setup, mode="indeterminate", length=200)
        self.progress.pack(pady=(5, 10))
        self.progress.pack_forget()  # Hide initially

    def add_compressor_frame(self, can_remove=True):
        frame = CompressorFrame(self.comp_inner_frame, simulation=self.sim, can_remove=can_remove, remove_callback=self.remove_compressor_frame)
        frame.pack(fill=tk.X, pady=5)
        self.compressor_frames.append(frame)
        # scroll to bottom
        self.setup_canvas.update_idletasks()
        self.setup_canvas.yview_moveto(1.0)

    def remove_compressor_frame(self, frame):
        if frame in self.compressor_frames:
            frame.destroy()
            self.compressor_frames.remove(frame)

    def create_scrollable_tab(self, tab_name):
        """
        Creates a new tab with a scrollable frame.
        Returns both the outer tab frame and the inner scrollable content frame.
        """
        # Outer tab frame
        tab = ttk.Frame(self.notebook, style="Container.TFrame")
        self.notebook.add(tab, text=tab_name)

        # Scrollable canvas setup
        canvas = tk.Canvas(tab, bg="#000e2f", highlightthickness=0)
        scrollbar = tk.Scrollbar(tab, orient='vertical', command=canvas.yview)

        canvas.configure(yscrollcommand=scrollbar.set)

        # Place the canvas and scrollbar
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Create inner frame
        scrollable_frame = ttk.Frame(canvas, style="Container.TFrame")

        # Create window in canvas and save the window ID
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        # Update scrollregion when scrollable_frame changes
        def on_frame_configure(event):
            canvas.update_idletasks()
            bbox = canvas.bbox("all")
            if bbox:
                x0, y0, x1, y1 = bbox
                height = max(y1, canvas.winfo_height())  # Prevent scrollregion from being too small
                canvas.configure(scrollregion=(x0, y0, x1, height))

        scrollable_frame.bind("<Configure>", on_frame_configure)

        # Ensure the scrollable_frame width matches the canvas
        def on_canvas_configure(event):
            canvas.itemconfig(window_id, width=event.width)

        canvas.bind("<Configure>", on_canvas_configure)

        # Mouse wheel support
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _on_mousewheel_linux(event):
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")

        def bind_mousewheel_events(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", _on_mousewheel_linux)
            canvas.bind_all("<Button-5>", _on_mousewheel_linux)

        def unbind_mousewheel_events(event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        canvas.bind("<Enter>", bind_mousewheel_events)
        canvas.bind("<Leave>", unbind_mousewheel_events)

        return tab, scrollable_frame, canvas

    def populate_data_text(self):
        """
        Gets export data as a string from exporter class. Stores in export_text member for 
        use by create data tab.
        """
        exporter = Exporter(self.sim)
        text_data = exporter.get_all_results_text()  # get the export text as string

        self.export_text.delete('1.0', tk.END)  # clear old content
        self.export_text.insert(tk.END, text_data)
    
    def save_data_txt(self):
        """
        Command for save data as txt file button.
        """
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        
        file_path = filedialog.asksaveasfilename(
            initialdir=downloads_path,
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.export_text.get('1.0', tk.END))
            messagebox.showinfo("Save Successful", f"File saved to:\n{file_path}")

    def create_data_tab(self):
        self.data_tab = ttk.Frame(self.notebook, style="Container.TFrame")
        self.notebook.add(self.data_tab, text="Power Data")

        # Text widget with scrollbar
        self.export_text = tk.Text(self.data_tab, wrap='word', font=("Segoe UI", 10))
        self.export_text.pack(side='left', fill='both', expand=True, padx=(10,0), pady=10)

        scrollbar = tk.Scrollbar(self.data_tab, command=self.export_text.yview)
        scrollbar.pack(side='right', fill='y', pady=10)
        self.export_text['yscrollcommand'] = scrollbar.set

        # Buttons frame below text
        button_frame = ttk.Frame(self.data_tab)
        button_frame.pack(fill='x', padx=10, pady=(0, 10))

        # Save TXT button
        save_txt_btn = ttk.Button(button_frame, text="Save as .txt", command=self.save_data_txt)
        save_txt_btn.pack(side='left')

        # (Future) Save CSV button can be added similarly here

        # Populate the text widget with export data
        self.populate_data_text()

    def create_graph_tab(self):
        # create graph tab
        graph_tab, scrollable_frame, canvas = self.create_scrollable_tab("Graphs")

        # Analyzer
        analyzer = Analyzer(self.sim)
        # build consumption by day plot and add
        kwh_by_day_fig = analyzer.plot_consumption_by_day()
        self.add_graph_to_tab(kwh_by_day_fig, scrollable_frame)

    def add_graph_to_tab(self, fig, container):
        frame = ttk.Frame(container)
        frame.pack(fill='both', expand=True, pady=10)

        # Create and pack Matplotlib canvas
        mpl_canvas = FigureCanvasTkAgg(fig, master=frame)
        mpl_canvas.draw()
        mpl_widget = mpl_canvas.get_tk_widget()
        mpl_widget.pack(side='top', fill='both', expand=True)

        # Toolbar for zoom/pan
        toolbar = NavigationToolbar2Tk(mpl_canvas, frame)
        toolbar.update()
        toolbar.pack(side='top', fill='x')
    
    def create_shutdown_tab(self):
        shutdown_tab, scrollable_frame, canvas = self.create_scrollable_tab("Shutdown Savings")

        # Horizontal container inside scrollable frame
        row_frame = ttk.Frame(scrollable_frame, style="Container.TFrame")
        row_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Scheduler widget on LEFT inside row_frame
        self.scheduler = ShutdownSchedulerWidget(
            row_frame,
            interval_minutes=self.sim.get_interval(),
            on_change=self.calculate_shutdown_savings
        )
        self.scheduler.pack(side="left", fill="y")  # fill vertically, natural width horizontally
    
        # Tables container on RIGHT inside row_frame
        table_frame = ttk.Frame(row_frame, style="Container.TFrame")
        table_frame.pack(side="left", fill="both", expand=True, padx=10)

        # Now create your weekly and annual tables inside table_frame
        table_style = ttk.Style()
        style = ttk.Style()
        style.configure("Treeview", rowheight=28)
        table_style.configure("Black.TLabel", foreground="black", background="#dcdad5", font=("Segoe UI", 11, "bold"))

        # Weekly Table Frame
        weekly_frame = ttk.Frame(table_frame)
        weekly_frame.pack(fill="x", pady=(0, 20))  # spacing below

        weekly_label = ttk.Label(weekly_frame, text="Weekly Shutdown Savings", style="Black.TLabel")
        weekly_label.pack(anchor="w", padx=5)

        self.weekly_table = ttk.Treeview(weekly_frame, columns=("Compressor", "Total kWh", "Total Savings ($)"), show="headings")
        self.weekly_table.heading("Compressor", text="Compressor")
        self.weekly_table.heading("Total kWh", text="Total kWh")
        self.weekly_table.heading("Total Savings ($)", text="Total Savings ($)")
        self.weekly_table.pack(padx=10, pady=5, fill="x")

        # Annual Table Frame
        annual_frame = ttk.Frame(table_frame)
        annual_frame.pack(fill="x")

        annual_label = ttk.Label(annual_frame, text="Annual Savings Summary", style="Black.TLabel")
        annual_label.pack(anchor="w", padx=5)

        self.annual_table = ttk.Treeview(annual_frame, columns=("Compressor", "Annual Savings kWh", "Annual Savings ($)"), show="headings")
        self.annual_table.heading("Compressor", text="Compressor")
        self.annual_table.heading("Annual Savings kWh", text="Annual Savings kWh")
        self.annual_table.heading("Annual Savings ($)", text="Annual Savings ($)")

        # Set column widths and alignment
        self.annual_table.column("Compressor", anchor="center", width=150)
        self.annual_table.column("Annual Savings kWh", anchor="center", width=140)
        self.annual_table.column("Annual Savings ($)", anchor="center", width=140)

        self.annual_table.pack(padx=10, pady=5, fill="x")

    def calculate_shutdown_savings(self):
        analyzer = Analyzer(self.sim)
        schedule = self.scheduler.get_schedule()                    # shutdown schedule 
        result = analyzer.compute_shutdown_savings(schedule)        # stores shutdown savings data
        compressor_savings = result['compressor_savings']           # shutdown savings data by compressor
        savings_by_day = result['savings_by_day']                   # shutdown savings by day
        active_days = [day for day in schedule if schedule[day]]    # active days in shutdown schedule

        # ----------- WEEKLY TABLE ---------------#
        # create columns for table
        columns = ["Compressor"] + [day for day in active_days] + ["Total kWh", "Total Savings ($)"]
        # destroy and rebuild Treeview (table) with new columns
        self.weekly_table.destroy()
        self.weekly_table = ttk.Treeview(self.weekly_table.master, columns=columns, show="headings")
        # set a fixed width per column to control table width
        for col in columns:
            self.weekly_table.heading(col, text=col)
            if col == "Compressor":
                width = 120
            elif col == "Total kWh":
                width = 80
            elif col == "Total Cost Savings ($)":
                width = 120
            else:
                width = 40
            self.weekly_table.column(col, anchor="center", width=width)
        self.weekly_table.pack(padx=10, pady=10, fill="x")

        # Insert rows for each compressor
        for comp_name, savings_dict in compressor_savings.items():
            # add kWh savings by day
            row_values = [comp_name]
            for day in active_days:
                val = savings_dict.get(day, 0.0)
                row_values.append(f"{val:,.2f}")
            # add kWh for week column
            total_val = savings_dict.get("Total", 0.0)
            row_values.append(f"{total_val:,.2f}")
            # Add weekly cost savings for this compressor
            cost_savings = savings_dict.get("Total $", 0.0)
            row_values.append(f"${cost_savings:,.2f}")
            # add 
            self.weekly_table.insert("", "end", values=row_values)

        # Insert total row
        total_row_values = ["Total"] + [f"{savings_by_day.get(day):,.2f}" for day in active_days] + [f"{result['total_week_kwh']:,.2f}"] + [f"${result['total_week_dollars']:,.2f}"]
        self.weekly_table.insert("", "end", values=total_row_values, tags=("total_row",))
        self.weekly_table.tag_configure("total_row", background="#747474", font=("Segoe UI", 10, "bold"))

        # ----------- ANNUAL TABLE ----------- #
        # Clear old rows
        for row in self.annual_table.get_children():
            self.annual_table.delete(row)

        # insert rows for each compressor
        for comp_name, savings_dict in compressor_savings.items():
            annual_kwh = savings_dict.get("Annual", 0.0)
            annual_dollars = savings_dict.get("Annual $", 0.0)
            self.annual_table.insert("", "end", values=(
                comp_name,
                f"{annual_kwh:,.2f}",
                f"${annual_dollars:,.2f}"
            ))

        # insert and format total row
        self.annual_table.insert("", "end", values=(
            "Total",
            f"{result['total_kwh']:,.2f}",
            f"${result['total_dollars']:,.2f}"
        ), tags=("total_row",))
        self.annual_table.tag_configure("total_row", background="#747474", font=("Segoe UI", 10, "bold"))

    def create_measur_export_tab(self):
        """
        Creates the export to MEASUR tab.
        """
        measur_tab, scrollable_frame, canvas = self.create_scrollable_tab("MEASUR Export")
        top_frame = ttk.Frame(scrollable_frame, style="Container.TFrame")
        top_frame.grid(row=0, sticky="n", pady=10)
        
        content_frame = ttk.Frame(scrollable_frame, style="Container.TFrame")
        content_frame.grid(row=1, column=0, sticky="nw")
        left_frame = ttk.Frame(content_frame, style="Container.TFrame")
        right_frame = ttk.Frame(content_frame, style="Container.TFrame")
        left_frame.grid(row=0, column=0, sticky="nw", padx=(0,200), pady=10)
        right_frame.grid(row=0, column=1, sticky="nw", pady=10)

        # --- Warning Message in top frame
        warning_border = tk.Frame(top_frame, background="#FFBE31", padx=2, pady=2)
        warning_border.grid(row=0, column=0, padx=(10,5), pady=0, sticky="w")
        ttk.Label(warning_border, text="WARNING: Do not make any mouse or keyboard inputs while export is in process. Export process starts 5 seconds after clicking 'Export' button.", foreground="#FFBE31", padding=5).grid(sticky="w")

        # --- Dropdown for day selection ---
        ttk.Label(left_frame, text="Select Day:").grid(row=0, column=0, padx=(10, 5), pady=0, sticky="w")

        # --- Day options ---
        day_values = self.sim.get_daytypes()
        self.day_var = tk.StringVar(self)
        default_day = day_values[0] if day_values else ""
        self.day_var.set(default_day)

        # --- OptionMenu for day selection ---
        self.day_menu = ttk.OptionMenu(left_frame, self.day_var, default_day, *day_values)
        self.day_menu.grid(row=0, column=1, padx=(0, 5), pady=0, sticky="w")

        # Apply the same menu styling as your other dropdown
        self.day_menu["menu"].config(
            font=("Segoe UI", 11),
            background="#ffffff",
            foreground="#000000",
            activebackground="#ffffff",
            activeforeground="#000000",
        )

        # --- Label for compressors ---
        ttk.Label(left_frame, text="Select Compressors:").grid(row=1, column=0, padx=(10, 5), pady=(10,5), sticky="w")

        # --- Compressor checkboxes ---
        self.comp_selected = {}  # Track selection state
        self.comp_buttons = {}   # Keep references to buttons
        compressor_objs = self.sim.get_compressors()     

        def toggle_comp(comp):
            name = comp.get_name()
            selected = self.comp_selected.get(name, False)
            self.comp_selected[name] = not selected
            btn = self.comp_buttons[name]

            if not selected:
                btn.config(style="CompSelected.TButton")
            else:
                btn.config(style="Comp.TButton")

        for i, comp in enumerate(compressor_objs):
            name = comp.get_name()
            self.comp_selected[name] = False
            btn = ttk.Button(left_frame, text=name, style="Comp.TButton")
            btn.grid(row=2 + i, column=1, sticky="w", padx=(0, 5), pady=2)
            btn.config(command=lambda c=comp: toggle_comp(c))
            self.comp_buttons[name] = btn

        # --- Export button to the right ---
        def on_export():
            export_list = [comp for comp in compressor_objs if self.comp_selected.get(comp.get_name(), False)]
            print("Selected compressors:", [comp.get_name() for comp in export_list])

            # Destroy old labels if they exist
            if hasattr(self, "countdown_label") and self.countdown_label.winfo_exists():
                self.countdown_label.destroy()
            if hasattr(self, "warning_label") and self.warning_label.winfo_exists():
                self.warning_label.destroy()

            # Create new labels and store references
            self.countdown_label = ttk.Label(right_frame, text="")
            self.countdown_label.grid(row=4, column=0, pady=10, sticky="w")

            self.warning_label = ttk.Label(right_frame, text=f"Please Ensure 0:00 for {export_list[0].get_name()} is selected.")
            self.warning_label.grid(row=3, column=0, pady=10, sticky="w")

            wait_seconds = 5
            self.countdown_label.config(text=f"Export Process Starting in {wait_seconds}", foreground="#ffffff")

            def update_countdown(seconds_remaining):
                if seconds_remaining > 0:
                    self.countdown_label.config(
                        text=f"Export Process Starting in {seconds_remaining}",
                        foreground="#ff0000" if seconds_remaining % 2 == 0 else "#ffffff",
                        background=""  # reset background to default
                    )
                    self.countdown_label.after(1000, update_countdown, seconds_remaining - 1)
                else:
                    self.countdown_label.config(text="EXPORTING", foreground="#ffffff", background="#ff0000")

                    def do_export():
                        print("Performing export...")
                        exporter = Exporter(self.sim)
                        export_day = str(self.day_var.get())
                        exporter.export_to_measur(day=export_day, export_compressors=export_list)
                        self.countdown_label.config(text=f"EXPORT FOR {export_day.upper()} COMPLETE", foreground="#00ca2c", background="#000e2f")
                        self.warning_label.config(text="")

                    self.countdown_label.after(100, do_export)

            update_countdown(wait_seconds)
    
        export_btn = ttk.Button(right_frame, text="Export", command=on_export)
        # Place button top-right aligned with compressor checkboxes area
        export_btn.grid(row=0, column=0, sticky="w", padx=5, pady=5)


    def run_simulation(self):
        """
        Pressed when all simulation data has been entered, including kWh rate, start and end date, compressor information. 
        Triggers processing and generation of tabs.
        """
        # Disable button to prevent spamming
        self.run_button.config(state=tk.DISABLED)
        self.status_label.config(text="Running simulation...")
        self.progress.pack()
        self.progress.start(10)  # Animate progress bar

        # Run simulation
        threading.Thread(target=self._run_simulation_background, daemon=True).start()

    def reset_result_tabs(self):
        # Keep only the first tab (Simulation Setup)
        while self.notebook.index("end") > 1:
            self.notebook.forget(1)

    def _run_simulation_background(self):
        try:
            self.reset_result_tabs()

            # Capture user input
            # kWh Rate
            kwh_text = self.kwh_entry.get().strip()
            if not kwh_text:
                raise ValueError("Please enter a valid kWh rate.")
            try:
                kWh_rate = float(kwh_text)
            except ValueError:
                raise ValueError("Please enter a valid kWh rate.")
            
            # Interval
            interval_label = self.interval_var.get()
            interval_value = self.interval_options[interval_label]

            # Deployed / Collected Date
            deployed_date_str = self.deployed_date_entry.get()
            collected_date_str = self.collected_date_entry.get()
            deployed_date = datetime.strptime(deployed_date_str, "%m/%d/%Y")
            collected_date = datetime.strptime(collected_date_str, "%m/%d/%Y")

            if deployed_date >= collected_date:
                raise ValueError("Deployed date must be earlier than collected date.")
            today = datetime.today()
            if deployed_date > today or collected_date > today:
                raise ValueError("Dates cannot be in the future.")


            self.sim.set_kwh_rate(kWh_rate)
            self.sim.set_interval(interval_value)
            self.sim.set_deployed_date(deployed_date_str)
            self.sim.set_collected_date(collected_date_str)

            compressors = []
            compressor_names = []
            for frame in self.compressor_frames:
                compressor = frame.get_compressor_data()
                compressors.append(compressor)
                compressor_names.append(compressor.get_name())
            self.sim.set_compressors(compressors)

            if (len(compressor_names) != len(set(compressor_names))):
                raise ValueError("Compressor names must be unique.")

            # compute power buckets
            self.sim.compute_power_buckets()

            # Schedule UI updates on main thread
            self.after(0, self._on_simulation_complete)

        except Exception as e:
            self.after(0, lambda e=e: self._on_simulation_error(e))

    def _on_simulation_complete(self):
        self.create_graph_tab()
        self.create_shutdown_tab()
        self.create_measur_export_tab()
        self.create_data_tab()
        self.status_label.config(text="Simulation complete.")
        self.run_button.config(state=tk.NORMAL)
        self.progress.stop()
        self.progress.pack_forget()

    def _on_simulation_error(self, error):
        messagebox.showerror("Simulation Error", str(error))
        self.status_label.config(text="Simulation failed.")
        self.run_button.config(state=tk.NORMAL)
        self.progress.stop()
        self.progress.pack_forget()

if __name__ == "__main__":
    app = Interface()
    app.mainloop()