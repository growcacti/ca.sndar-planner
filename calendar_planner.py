#!/usr/bin/env python3
import calendar
import os
import sqlite3
import subprocess
import sys
import tempfile
import tkinter as tk
from datetime import date, datetime, timedelta
from tkinter import filedialog, messagebox, ttk


APP_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(APP_DIRECTORY, "calendar_events.sqlite3")


class CalendarPlanner:
    def __init__(self, root):
        self.root = root
        self.root.title("Calendar Planner")
        self.root.minsize(1060, 700)
        self.database = sqlite3.connect(DATABASE_PATH)
        self.database.row_factory = sqlite3.Row
        self._create_database()

        today = date.today()
        self.display_year = today.year
        self.display_month = today.month
        self.selected_date = today.isoformat()
        self.notified = set()

        self.date_var = tk.StringVar(value=self.selected_date)
        self.title_var = tk.StringVar()
        self.start_var = tk.StringVar(value="09:00")
        self.end_var = tk.StringVar(value="10:00")
        self.location_var = tk.StringVar()
        self.reminder_var = tk.StringVar(value="15")
        self.clock_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Select a date, then add an event.")
        self.search_var = tk.StringVar()
        self.day_only_var = tk.BooleanVar(value=False)
        self.search_var.trace_add("write", lambda *_: self._load_month_events() if hasattr(self, "event_list") else None)

        self._create_widgets()
        self.refresh()
        self._tick()
        self._check_reminders()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _create_database(self):
        self.database.execute(
            """CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY,
                event_date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                title TEXT NOT NULL,
                location TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                reminder_minutes INTEGER NOT NULL DEFAULT 0
            )"""
        )
        self.database.commit()

    def _create_widgets(self):
        self.root.configure(bg="#eaf1f8")
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background="#eaf1f8")
        style.configure("TLabel", background="#eaf1f8", foreground="#18324d")
        style.configure("TLabelframe", background="#f8fbff", bordercolor="#b8cde1")
        style.configure("TLabelframe.Label", background="#eaf1f8", foreground="#173e63", font=("Segoe UI", 11, "bold"))
        style.configure("TButton", padding=(10, 6), foreground="#153b5f", background="#dbeafa", font=("Segoe UI", 10, "bold"))
        style.map("TButton", background=[("active", "#b9d7f6")])
        style.configure("Accent.TButton", background="#1768ac", foreground="white")
        style.map("Accent.TButton", background=[("active", "#0e4c83")])
        style.configure("Day.TButton", padding=8, anchor="center", background="#f8fbff", font=("Segoe UI", 10))
        style.configure("EventDay.TButton", padding=8, anchor="center", background="#dceefe", foreground="#114d7a", font=("Segoe UI", 10, "bold"))
        style.configure("Today.TButton", padding=8, anchor="center", background="#d8f1e5", foreground="#175d40", font=("Segoe UI", 10, "bold"))
        style.configure("SelectedDay.TButton", padding=8, anchor="center", background="#1768ac", foreground="white", font=("Segoe UI", 10, "bold"))
        style.map("SelectedDay.TButton", background=[("active", "#0e4c83")], foreground=[("active", "white")])
        style.configure("Treeview", rowheight=28, background="#ffffff", fieldbackground="#ffffff", foreground="#18324d")
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#dbeafa")
        style.configure("TEntry", padding=5)
        self.root.columnconfigure(0, weight=3)
        self.root.columnconfigure(1, weight=2)
        self.root.rowconfigure(1, weight=1)

        top = ttk.Frame(self.root, padding=(12, 10, 12, 4))
        top.grid(row=0, column=0, columnspan=2, sticky="ew")
        top.columnconfigure(1, weight=1)
        ttk.Label(top, text="Calendar Planner", font=("Segoe UI", 20, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(top, textvariable=self.clock_var, font=("Consolas", 15, "bold")).grid(row=0, column=1, sticky="e")

        calendar_panel = ttk.Frame(self.root, padding=(12, 4, 6, 12))
        calendar_panel.grid(row=1, column=0, sticky="nsew")
        calendar_panel.columnconfigure(0, weight=1)
        calendar_panel.rowconfigure(1, weight=1)

        navigator = ttk.Frame(calendar_panel)
        navigator.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        navigator.columnconfigure(1, weight=1)
        ttk.Button(navigator, text="< Previous", command=lambda: self.change_month(-1)).grid(row=0, column=0, sticky="w")
        self.month_label = ttk.Label(navigator, font=("Segoe UI", 15, "bold"), anchor="center")
        self.month_label.grid(row=0, column=1, sticky="ew")
        ttk.Button(navigator, text="Next >", command=lambda: self.change_month(1)).grid(row=0, column=2, sticky="e")
        ttk.Button(navigator, text="Today", command=self.show_today).grid(row=0, column=3, padx=(12, 0))

        self.month_grid = ttk.Frame(calendar_panel)
        self.month_grid.grid(row=1, column=0, sticky="nsew")
        for column in range(7):
            self.month_grid.columnconfigure(column, weight=1, uniform="days")
        for row in range(7):
            self.month_grid.rowconfigure(row, weight=1)

        details = ttk.Frame(self.root, padding=(6, 4, 12, 12))
        details.grid(row=1, column=1, sticky="nsew")
        details.columnconfigure(0, weight=1)
        details.rowconfigure(1, weight=1)

        form = ttk.LabelFrame(details, text="Event Details", padding=10)
        form.grid(row=0, column=0, sticky="ew")
        form.columnconfigure(1, weight=1)
        self._field(form, 0, "Date (YYYY-MM-DD)", self.date_var)
        self._field(form, 1, "Title", self.title_var)
        self._field(form, 2, "Start (HH:MM)", self.start_var)
        self._field(form, 3, "End (HH:MM)", self.end_var)
        self._field(form, 4, "Location", self.location_var)
        self._field(form, 5, "Reminder minutes", self.reminder_var)
        ttk.Label(form, text="Notes").grid(row=6, column=0, sticky="nw", pady=(6, 0))
        self.notes = tk.Text(form, height=4, width=32, wrap="word")
        self.notes.grid(row=6, column=1, sticky="ew", pady=(6, 0))
        buttons = ttk.Frame(form)
        buttons.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        ttk.Button(buttons, text="Add Event", style="Accent.TButton", command=self.add_event).pack(side="left")
        ttk.Button(buttons, text="Update Selected", command=self.update_event).pack(side="left", padx=5)
        ttk.Button(buttons, text="Clear Form", command=self.clear_form).pack(side="left")

        events_frame = ttk.LabelFrame(details, text="Events", padding=8)
        events_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        events_frame.columnconfigure(0, weight=1)
        events_frame.rowconfigure(1, weight=1)
        filters = ttk.Frame(events_frame)
        filters.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        filters.columnconfigure(1, weight=1)
        ttk.Label(filters, text="Search").grid(row=0, column=0, padx=(0, 6))
        ttk.Entry(filters, textvariable=self.search_var).grid(row=0, column=1, sticky="ew")
        ttk.Checkbutton(filters, text="Selected day", variable=self.day_only_var, command=self._load_month_events).grid(row=0, column=2, padx=(8, 0))
        self.event_list = ttk.Treeview(events_frame, columns=("when", "title"), show="headings", selectmode="extended", height=10)
        self.event_list.heading("when", text="When")
        self.event_list.heading("title", text="Event")
        self.event_list.column("when", width=130, anchor="w")
        self.event_list.column("title", width=220, anchor="w")
        self.event_list.grid(row=1, column=0, sticky="nsew")
        self.event_list.tag_configure("alternate", background="#f1f7fd")
        self.event_list.bind("<<TreeviewSelect>>", self.load_selected_event)
        scroll = ttk.Scrollbar(events_frame, orient="vertical", command=self.event_list.yview)
        scroll.grid(row=1, column=1, sticky="ns")
        self.event_list.configure(yscrollcommand=scroll.set)
        event_buttons = ttk.Frame(events_frame)
        event_buttons.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Button(event_buttons, text="Delete Selected", command=self.delete_events).pack(side="left")
        ttk.Button(event_buttons, text="Compare Selected", command=self.compare_events).pack(side="left", padx=5)
        ttk.Button(event_buttons, text="Print Month", command=self.print_month).pack(side="right")
        ttk.Button(event_buttons, text="Save Report", command=self.save_month_report).pack(side="right", padx=5)

        ttk.Label(self.root, textvariable=self.status_var, anchor="w", relief="sunken", padding=(8, 4)).grid(
            row=2, column=0, columnspan=2, sticky="ew")

    @staticmethod
    def _field(parent, row, label, variable):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=3)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=3)

    def change_month(self, offset):
        month = self.display_month + offset
        if month == 0:
            self.display_year -= 1
            month = 12
        elif month == 13:
            self.display_year += 1
            month = 1
        self.display_month = month
        self.refresh()

    def show_today(self):
        today = date.today()
        self.display_year, self.display_month = today.year, today.month
        self.selected_date = today.isoformat()
        self.date_var.set(self.selected_date)
        self.refresh()

    def refresh(self):
        self._draw_month()
        self._load_month_events()

    def _draw_month(self):
        for child in self.month_grid.winfo_children():
            child.destroy()
        self.month_label.configure(text=calendar.month_name[self.display_month] + " " + str(self.display_year))
        for column, weekday in enumerate(("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")):
            ttk.Label(self.month_grid, text=weekday, anchor="center", font=("Segoe UI", 10, "bold")).grid(
                row=0, column=column, sticky="nsew", padx=1, pady=1)
        counts = self._event_counts()
        for row, week in enumerate(calendar.monthcalendar(self.display_year, self.display_month), start=1):
            for column, day_number in enumerate(week):
                if not day_number:
                    ttk.Label(self.month_grid, text="", relief="solid").grid(row=row, column=column, sticky="nsew", padx=1, pady=1)
                    continue
                day_value = date(self.display_year, self.display_month, day_number).isoformat()
                event_count = counts.get(day_value, 0)
                label = str(day_number) + ("\n" + str(event_count) + " event(s)" if event_count else "")
                style = ("SelectedDay.TButton" if day_value == self.selected_date else
                         "Today.TButton" if day_value == date.today().isoformat() else
                         "EventDay.TButton" if event_count else "Day.TButton")
                button = ttk.Button(self.month_grid, text=label, style=style, command=lambda value=day_value: self.select_date(value))
                button.grid(row=row, column=column, sticky="nsew", padx=1, pady=1)

    def _event_counts(self):
        prefix = "{0:04d}-{1:02d}-%".format(self.display_year, self.display_month)
        rows = self.database.execute("SELECT event_date, COUNT(*) AS count FROM events WHERE event_date LIKE ? GROUP BY event_date", (prefix,))
        return {row["event_date"]: row["count"] for row in rows}

    def select_date(self, value):
        self.selected_date = value
        self.date_var.set(value)
        self.status_var.set("Selected " + datetime.strptime(value, "%Y-%m-%d").strftime("%A, %B %d, %Y") + ".")
        self._draw_month()
        if self.day_only_var.get():
            self._load_month_events()

    def _load_month_events(self):
        if not hasattr(self, "event_list"):
            return
        previous = set(self.event_list.selection())
        for item in self.event_list.get_children():
            self.event_list.delete(item)
        prefix = "{0:04d}-{1:02d}-%".format(self.display_year, self.display_month)
        query = "SELECT * FROM events WHERE event_date LIKE ?"
        parameters = [prefix]
        if self.day_only_var.get():
            query += " AND event_date = ?"
            parameters.append(self.selected_date)
        search = self.search_var.get().strip().casefold()
        rows = self.database.execute(query + " ORDER BY event_date, start_time, title", parameters)
        count = 0
        for row in rows:
            if search and search not in " ".join(str(row[key]) for key in ("title", "location", "notes", "event_date")).casefold():
                continue
            when = "{0} {1}".format(row["event_date"], row["start_time"])
            iid = str(row["id"])
            self.event_list.insert("", "end", iid=iid, values=(when, row["title"]), tags=("alternate",) if count % 2 else ())
            if iid in previous:
                self.event_list.selection_add(iid)
            count += 1

    def _event_values(self):
        event_date = self.date_var.get().strip()
        title = self.title_var.get().strip()
        start_time = self.start_var.get().strip()
        end_time = self.end_var.get().strip()
        try:
            date.fromisoformat(event_date)
            start_time = datetime.strptime(start_time, "%H:%M").strftime("%H:%M")
            end_time = datetime.strptime(end_time, "%H:%M").strftime("%H:%M")
            reminder = int(self.reminder_var.get().strip() or "0")
            if reminder < 0:
                raise ValueError
        except ValueError:
            raise ValueError("Use a valid date, 24-hour times (HH:MM), and zero or more reminder minutes.")
        if not title:
            raise ValueError("Enter an event title.")
        if end_time <= start_time:
            raise ValueError("The end time must be later than the start time.")
        return (event_date, start_time, end_time, title, self.location_var.get().strip(), self.notes.get("1.0", "end-1c").strip(), reminder)

    def add_event(self):
        try:
            values = self._event_values()
        except ValueError as error:
            messagebox.showerror("Event", str(error))
            return
        self.database.execute("INSERT INTO events (event_date, start_time, end_time, title, location, notes, reminder_minutes) VALUES (?, ?, ?, ?, ?, ?, ?)", values)
        self.database.commit()
        self.selected_date = values[0]
        selected = date.fromisoformat(values[0])
        self.display_year, self.display_month = selected.year, selected.month
        self.clear_form(keep_date=True)
        self.status_var.set("Event added.")
        self.refresh()

    def load_selected_event(self, _event=None):
        selected = self.event_list.selection()
        if len(selected) != 1:
            return
        row = self.database.execute("SELECT * FROM events WHERE id = ?", (int(selected[0]),)).fetchone()
        if not row:
            return
        self.date_var.set(row["event_date"])
        self.title_var.set(row["title"])
        self.start_var.set(row["start_time"])
        self.end_var.set(row["end_time"])
        self.location_var.set(row["location"])
        self.reminder_var.set(str(row["reminder_minutes"]))
        self.notes.delete("1.0", "end")
        self.notes.insert("1.0", row["notes"])
        self.selected_date = row["event_date"]
        duration = self._duration_text(row)
        self.status_var.set("Selected event duration: " + duration + ".")
        self._draw_month()

    def update_event(self):
        selected = self.event_list.selection()
        if len(selected) != 1:
            messagebox.showwarning("Update Event", "Select exactly one event to update.")
            return
        try:
            values = self._event_values()
        except ValueError as error:
            messagebox.showerror("Event", str(error))
            return
        self.database.execute("UPDATE events SET event_date=?, start_time=?, end_time=?, title=?, location=?, notes=?, reminder_minutes=? WHERE id=?", values + (int(selected[0]),))
        self.database.commit()
        self.notified.discard(int(selected[0]))
        self.selected_date = values[0]
        selected_date = date.fromisoformat(values[0])
        self.display_year, self.display_month = selected_date.year, selected_date.month
        self.status_var.set("Event updated.")
        self.refresh()

    def delete_events(self):
        selected = self.event_list.selection()
        if not selected:
            messagebox.showwarning("Delete Events", "Select one or more events to delete.")
            return
        if not messagebox.askyesno("Delete Events", "Delete the selected event(s)?"):
            return
        ids = [int(item) for item in selected]
        self.database.executemany("DELETE FROM events WHERE id = ?", [(item,) for item in ids])
        self.database.commit()
        self.notified.difference_update(ids)
        self.clear_form(keep_date=True)
        self.status_var.set("Deleted " + str(len(ids)) + " event(s).")
        self.refresh()

    def clear_form(self, keep_date=False):
        if not keep_date:
            self.date_var.set(self.selected_date)
        self.title_var.set("")
        self.start_var.set("09:00")
        self.end_var.set("10:00")
        self.location_var.set("")
        self.reminder_var.set("15")
        self.notes.delete("1.0", "end")
        for item in self.event_list.selection():
            self.event_list.selection_remove(item)

    def compare_events(self):
        selected = self.event_list.selection()
        if len(selected) != 2:
            messagebox.showwarning("Compare Events", "Select exactly two events to calculate the time between them.")
            return
        rows = [self.database.execute("SELECT * FROM events WHERE id = ?", (int(item),)).fetchone() for item in selected]
        rows.sort(key=lambda row: (row["event_date"], row["start_time"]))
        first_end = datetime.strptime(rows[0]["event_date"] + " " + rows[0]["end_time"], "%Y-%m-%d %H:%M")
        second_start = datetime.strptime(rows[1]["event_date"] + " " + rows[1]["start_time"], "%Y-%m-%d %H:%M")
        gap = second_start - first_end
        text = "Time from the end of '{0}' to the start of '{1}': {2}".format(rows[0]["title"], rows[1]["title"], self._timedelta_text(gap))
        self.status_var.set(text)
        messagebox.showinfo("Time Between Events", text)

    @staticmethod
    def _duration_text(row):
        start = datetime.strptime(row["start_time"], "%H:%M")
        end = datetime.strptime(row["end_time"], "%H:%M")
        return CalendarPlanner._timedelta_text(end - start)

    @staticmethod
    def _timedelta_text(value):
        sign = "-" if value.total_seconds() < 0 else ""
        total_minutes = int(abs(value.total_seconds()) // 60)
        days, remaining = divmod(total_minutes, 1440)
        hours, minutes = divmod(remaining, 60)
        pieces = []
        if days:
            pieces.append(str(days) + " day" + ("s" if days != 1 else ""))
        if hours:
            pieces.append(str(hours) + " hour" + ("s" if hours != 1 else ""))
        if minutes or not pieces:
            pieces.append(str(minutes) + " minute" + ("s" if minutes != 1 else ""))
        return sign + ", ".join(pieces)

    def _tick(self):
        self.clock_var.set(datetime.now().strftime("%A, %B %d, %Y   %I:%M:%S %p"))
        self.root.after(1000, self._tick)

    def _check_reminders(self):
        now = datetime.now()
        rows = self.database.execute("SELECT * FROM events WHERE event_date >= ?", (now.date().isoformat(),))
        for row in rows:
            if row["id"] in self.notified or row["reminder_minutes"] == 0:
                continue
            start = datetime.strptime(row["event_date"] + " " + row["start_time"], "%Y-%m-%d %H:%M")
            reminder_time = start - timedelta(minutes=row["reminder_minutes"])
            if reminder_time <= now < start + timedelta(minutes=1):
                self.notified.add(row["id"])
                messagebox.showinfo("Calendar Reminder", "{0}\nStarts at {1} on {2}".format(row["title"], row["start_time"], row["event_date"]))
        self.root.after(30000, self._check_reminders)

    def _month_report(self):
        prefix = "{0:04d}-{1:02d}-%".format(self.display_year, self.display_month)
        rows = self.database.execute("SELECT * FROM events WHERE event_date LIKE ? ORDER BY event_date, start_time, title", (prefix,)).fetchall()
        heading = calendar.month_name[self.display_month] + " " + str(self.display_year) + " Event Calendar"
        lines = [heading, "=" * len(heading), ""]
        if not rows:
            lines.append("No events scheduled.")
        for row in rows:
            lines.extend([
                "{0}  {1}-{2}  {3}".format(row["event_date"], row["start_time"], row["end_time"], row["title"]),
                "  Location: " + (row["location"] or "Not specified"),
                "  Notes: " + (row["notes"] or "None"),
                ""
            ])
        return "\n".join(lines) + "\n"

    def save_month_report(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")],
                                            initialfile="calendar_{0}_{1:02d}.txt".format(self.display_year, self.display_month))
        if path:
            try:
                with open(path, "w", encoding="utf-8") as report:
                    report.write(self._month_report())
                self.status_var.set("Saved report to " + path)
            except OSError as error:
                messagebox.showerror("Save Report", str(error))

    def print_month(self):
        path = os.path.join(tempfile.gettempdir(), "calendar_planner_{0}_{1:02d}.txt".format(self.display_year, self.display_month))
        try:
            with open(path, "w", encoding="utf-8") as report:
                report.write(self._month_report())
        except OSError as error:
            messagebox.showerror("Print Month", str(error))
            return
        try:
            if sys.platform == "win32":
                os.startfile(path, "print")
                self.status_var.set("Sent monthly report to the default printer.")
            else:
                subprocess.Popen(["xdg-open" if sys.platform.startswith("linux") else "open", path])
                self.status_var.set("Opened monthly report. Print it from the text editor.")
        except (OSError, AttributeError) as error:
            messagebox.showerror("Print Month", "Could not open the report: " + str(error))

    def close(self):
        self.database.close()
        self.root.destroy()


if __name__ == "__main__":
    application = tk.Tk()
    CalendarPlanner(application)
    application.mainloop()
