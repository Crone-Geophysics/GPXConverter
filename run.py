import tkinter as tk
from pathlib import Path
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter.messagebox import showinfo, showerror
import chardet
import gpxpy
import pandas as pd
import utm


class GPXConverter:
    def __init__(self):
        window = tk.Tk()
        window.minsize(300, 100)
        window.title("GPX Converter")

        frame = tk.Frame(master=window)
        choose_btn = tk.Button(master=frame, text="Select File...", command=self.open_gpx)
        self.chosen_file_label = tk.Label(master=frame, wraplength=300, anchor="w", justify="left",
                                          text="Selected GPX file: None")
        convert_btn = tk.Button(master=frame, text="Convert File...", command=self.save_csv)
        statusbar = tk.Label(window, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W)

        frame.pack(fill=tk.BOTH, expand=False)
        self.chosen_file_label.pack(padx=5, pady=3, fill=tk.X)
        choose_btn.pack(padx=5, pady=3, fill=tk.X)
        convert_btn.pack(padx=5, pady=3, fill=tk.X)
        # statusbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.gpx_file = None

        window.mainloop()

    def open_gpx(self):
        """Open a file for editing."""
        filepath = askopenfilename(filetypes=[("GPX Files", "*.gpx")])
        if not filepath:
            return

        print(f"Opening {filepath}.")
        self.gpx_file = filepath
        self.chosen_file_label["text"] = f"Selected GPX file: {filepath}."

    def save_csv(self):
        gps = self.convert_gpx()
        if gps is None:
            return

        filepath = asksaveasfilename(
            defaultextension="CSV",
            initialfile=Path(self.gpx_file).with_suffix(".CSV").name,
            filetypes=[("CSV Files", "*.CSV"), ("Text Files", "*.txt")])
        if not filepath:
            return

        filepath = Path(filepath)
        showinfo("Success", f"File saved as {filepath}.")
        print(f"Saving file to {filepath}")
        gps.to_csv(filepath, index=False)
        # os.startfile(str(filepath))

    def convert_gpx(self):
        if not self.gpx_file:
            print(f"No GPX file selected.")
            return

        def get_utm(gpx_file):
            """
            Retrieve the GPS from the GPS file in UTM coordinates
            :param gpx_file: str or Path, filepath
            :param as_string: bool, return a string instead of tuple if True
            :return: latitude, longitude, elevation, unit, stn
            """
            def parse_gpx(filepath):
                with open(filepath, 'rb') as byte_file:
                    byte_content = byte_file.read()
                    encoding = chardet.detect(byte_content).get('encoding')
                    print(f"Using {encoding} encoding.")
                    str_contents = byte_content.decode(encoding=encoding)
                gpx = gpxpy.parse(str_contents)
                gps = []

                # Use Route points if no waypoints exist
                if gpx.waypoints:
                    for waypoint in gpx.waypoints:
                        name = waypoint.name
                        gps.append([waypoint.latitude, waypoint.longitude, waypoint.elevation, '0', name])
                    if len(gpx.waypoints) != len(gps):
                        print(f"{len(gpx.waypoints)} waypoints found in GPX file but {len(gps)} points parsed.")
                elif gpx.routes:
                    route = gpx.routes[0]
                    for point in route.points:
                        name = point.name
                        gps.append(
                            [point.latitude, point.longitude, None, '0', name])  # Routes have no elevation data, thus None.
                    if len(route.points) != len(gps):
                        print(f"{len(route.points)} points found in GPX file but {len(gps)} points parsed.")
                else:
                    raise ValueError(F"No waypoints or routes found in {Path(filepath).name}.")

                return gps

            try:
                gps = parse_gpx(gpx_file)
            except Exception as e:
                raise Exception(str(e))
            zone = None
            utm_gps = []
            for row in gps:
                lat = row[0]
                lon = row[1]
                elevation = row[2]
                units = row[3]
                name = row[4]  # Station name usually
                u = utm.from_latlon(lat, lon)
                zone = u[2]
                utm_gps.append([u[0], u[1], elevation, units, name])
            return utm_gps, zone

        try:
            utm_gps, zone = get_utm(self.gpx_file)
        except Exception as e:
            showerror("Error", f"Error parsing GPX file:\n{e}.")
            return None
        else:
            df = pd.DataFrame(utm_gps, columns=["Easting", "Northing", "Elevation", "Units", "Name"])
            print(df)
            return df


w = GPXConverter()
