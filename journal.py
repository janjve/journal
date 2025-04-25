#!/usr/bin/env -S uv run

import os
import sys
import argparse
import datetime
import curses
import subprocess


def get_title(date) -> str:
    return date.strftime("%Y-%m-%d-%a").upper()


def create_journal_file(date, output_dir="."):
    """Create a journal file for the specified date."""
    # Format the date as YYYY-MM-DD-dayname
    title = get_title(date)
    filename = f"{title}.md"
    filepath = os.path.join(output_dir, filename)

    file_exists = os.path.exists(filepath)

    if not file_exists:
        # Create the file with title and separator
        with open(filepath, "w") as f:
            f.write(f"{title}\n")
            f.write("=" * len(title) + "\n\n")
        print(f"Created new journal file: {filepath}")
    else:
        print(f"Opening existing journal file: {filepath}")

    # Open the file with vi
    subprocess.call(["vi", filepath])

    return filepath


def get_file_line_count(filepath):
    """Count the number of lines in a file."""
    if not os.path.exists(filepath):
        return 0

    with open(filepath, "r") as f:
        return sum(1 for _ in f)


def select_date(stdscr, output_dir="."):
    """Interactive date selection using curses."""
    curses.curs_set(0)  # Hide the cursor
    stdscr.clear()

    # Setup colors
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_RED, -1)  # For new files
    curses.init_pair(2, curses.COLOR_WHITE, -1)  # For existing files
    curses.init_pair(3, curses.COLOR_YELLOW, -1)  # For the arrow

    # Get dates for the last week
    today = datetime.datetime.now()
    dates = [(today - datetime.timedelta(days=i)) for i in range(7)]
    # Reverse the dates so today is at the top
    dates.reverse()

    max_row = len(dates) - 1
    current_row = max_row  # Set to today's date

    # Check which dates already have journal files and count lines
    files_exist = []
    line_counts = []

    for date in dates:
        filename = f"{get_title(date)}.md"
        filepath = os.path.join(output_dir, filename)
        exists = os.path.exists(filepath)
        files_exist.append(exists)

        # Count lines if file exists
        if exists:
            line_count = get_file_line_count(filepath) - 3
            line_counts.append(line_count)
        else:
            line_counts.append(0)

    # Display the menu
    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # Draw options
        for idx, date in enumerate(dates):
            date_str = get_title(date)

            # Add line count for existing files
            if files_exist[idx]:
                display_str = f"{date_str}: {line_counts[idx]}"
            else:
                display_str = date_str

            # Choose color based on file existence
            color_pair = (
                curses.color_pair(2) if files_exist[idx] else curses.color_pair(1)
            )

            # Calculate positions
            arrow_x = (width - len(display_str)) // 2 - 2
            text_x = (width - len(display_str)) // 2
            y = 4 + idx

            # Draw arrow for selected row
            if idx == current_row:
                stdscr.attron(curses.color_pair(3))
                stdscr.addstr(y, arrow_x, ">")
                stdscr.attroff(curses.color_pair(3))

            # Draw date text
            stdscr.attron(color_pair)
            stdscr.addstr(y, text_x, display_str)
            stdscr.attroff(color_pair)

        # Instructions
        stdscr.addstr(
            height - 2, 2, "Use arrow keys to navigate, Enter to select, q to quit"
        )

        stdscr.refresh()

        # Get user input
        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < max_row:
            current_row += 1
        elif key == ord("\n"):  # Enter key
            return dates[current_row]
        elif key == ord("q"):
            return None


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Create and edit journal entries.")
    parser.add_argument(
        "-o", "--out", default=".", help="Output directory for journal files"
    )
    parser.add_argument(
        "-s", "--select", action="store_true", help="Select a date from the last week"
    )

    args = parser.parse_args()

    # Check if output directory exists
    if not os.path.isdir(args.out):
        print(f"Error: Output directory '{args.out}' does not exist.")
        sys.exit(1)

    # Get the date to use
    if args.select:
        selected_date = curses.wrapper(select_date, args.out)
        if selected_date is None:
            sys.exit(0)
        date = selected_date
    else:
        date = datetime.datetime.now()

    # Create and open the journal file
    create_journal_file(date, args.out)


if __name__ == "__main__":
    main()
