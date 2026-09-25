# Calendar Planner

A desktop calendar and event planner built with Python's Tkinter and SQLite. Browse months, add appointments, search events, compare the time between two events, and get reminders while the application is open.

## Requirements

- Python 3.9 or newer
- Tkinter (often installed separately on Linux)
- A desktop environment

The application uses only Python standard-library modules. On MX Linux or Debian, if `import tkinter` fails, install the package with:

```bash
sudo apt update
sudo apt install python3-tk
```

## Start the planner

Place `calendar_planner.py` in a folder where you have permission to create files, then run:

```bash
python3 calendar_planner.py
```

The program creates `calendar_events.sqlite3` **in the same folder as the script** when it starts. If you already have a calendar database, put it beside the script before running it. Keep the Python file and database together when moving the planner to another folder or computer. Back up the database periodically; it holds your events.

## Using the calendar

1. Use **Previous**, **Next**, or **Today** to browse months. Click a day to set the date for a new event.
2. Enter a title, date, start and end times, and optional location and notes. Dates use `YYYY-MM-DD`; times use 24-hour `HH:MM` (for example, `14:30`). The end must be after the start on the same day.
3. Set **Reminder minutes** to the number of minutes before the event, or `0` to turn its reminder off. Click **Add Event**.
4. Click an event in the list to load it into the form. Edit the fields and click **Update Selected**. **Clear Form** prepares the form for a new event.

The calendar colors distinguish the selected day, today, and days containing events. The event list shows the displayed month in date and time order. Use **Search** to filter by title, location, notes, or date. Check **Selected day** to see only events on the day you clicked. These filters affect the list only; they do not remove events from the database.

Select one or more entries and click **Delete Selected** to remove them after confirmation. To see the gap between appointments, select exactly two entries (Ctrl-click on most desktops) and click **Compare Selected**. A negative gap means the events overlap.

## Reports and printing

- **Save Report** writes the displayed month's events to a text file you choose.
- **Print Month** opens a temporary text report in your default text application on Linux or macOS so you can print it there. On Windows, it sends the report to the default printer.

The report includes event times, titles, locations, and notes. Search and the selected-day filter do not limit the monthly report.

## Reminders

Reminders appear as dialog boxes while the planner is running. The application checks about every 30 seconds and shows each eligible reminder once per session. It does not run in the background after you close it, and it does not send email or phone notifications.

## Data and troubleshooting

- `calendar_events.sqlite3` is a local SQLite database. It is created automatically and contains the saved appointments. Do not delete it unless you intend to erase those appointments.
- If saving events reports a read-only database error, move the script and database to a folder you can write to, such as a folder in your home directory.
- If the GUI cannot start, check that a desktop session is running and Tkinter is installed: `python3 -m tkinter`.
- If **Print Month** cannot open a report on Linux, use **Save Report** and open the saved text file with your preferred editor.
