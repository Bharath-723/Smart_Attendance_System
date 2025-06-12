import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from datetime import datetime, timedelta
from database import get_attendance_stats, get_attendance_records
import numpy as np
from matplotlib.gridspec import GridSpec
import matplotlib as mpl
from matplotlib.container import BarContainer
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Set the style for modern look
plt.style.use('bmh')
mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans', 'Bitstream Vera Sans', 'sans-serif']
mpl.rcParams['axes.grid'] = True
mpl.rcParams['grid.alpha'] = 0.3
mpl.rcParams['axes.facecolor'] = '#f0f2f6'
mpl.rcParams['figure.facecolor'] = '#f0f2f6'
mpl.rcParams['axes.titleweight'] = 'bold'
mpl.rcParams['axes.labelweight'] = 'bold'

def show_attendance_pie():
    """Show attendance distribution as a pie chart"""
    stats, total_classes = get_attendance_stats()
    if not stats:
        print("No attendance data found!")
        return

    # Create figure
    fig = plt.figure(figsize=(10, 8))
    fig.patch.set_facecolor('#f0f2f6')
    
    # Prepare data
    names = [s[0] for s in stats]
    percentages = [s[2] for s in stats]
    
    # Create pie chart
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD', '#FFD93D', '#6C5B7B', '#355C7D']
    pie_result = plt.pie(
        percentages,
        labels=names,
        colors=colors[:len(names)],
        autopct='%1.1f%%',
        startangle=90,
        pctdistance=0.85,
        wedgeprops=dict(width=0.5, edgecolor='white', linewidth=2)
    )
    wedges, texts = pie_result[:2]
    autotexts = pie_result[2] if len(pie_result) > 2 else []
    
    # Customize chart
    plt.title('Attendance Distribution', pad=20, fontsize=14, fontweight='bold', color='#2C3E50')
    for text in texts:
        text.set_fontsize(10)
        text.set_color('#2C3E50')
    for autotext in autotexts:
        autotext.set_fontsize(10)
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    plt.show()

def show_attendance_bar():
    """Show attendance by date and hours present"""
    records = get_attendance_records()
    if not records:
        print("No attendance data found!")
        return

    # Convert to DataFrame
    df = pd.DataFrame(records, columns=['name', 'date', 'hour'])
    df['date'] = pd.to_datetime(df['date'])
    
    # Create figure
    fig = plt.figure(figsize=(12, 6))
    fig.patch.set_facecolor('#f0f2f6')
    
    # Group by date and hour
    daily_hourly = df.groupby(['date', 'hour']).size().unstack(fill_value=0)
    
    # Create stacked bar plot
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD', '#FFD93D', '#6C5B7B', '#355C7D']
    daily_hourly.plot(kind='bar', stacked=True, color=colors[:len(daily_hourly.columns)])
    
    # Customize plot
    plt.title('Attendance by Date and Hour', fontsize=14, fontweight='bold', color='#2C3E50')
    plt.xlabel('Date', fontsize=12, color='#2C3E50')
    plt.ylabel('Number of Students', fontsize=12, color='#2C3E50')
    plt.legend(title='Hour', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.xticks(rotation=45, ha='right')
    
    # Add value labels
    for container in plt.gca().containers:
        if isinstance(container, BarContainer):
            plt.gca().bar_label(container, fmt='%d', padding=3)
    
    plt.tight_layout()
    plt.show()

def show_attendance_line():
    """Show attendance trends over time"""
    records = get_attendance_records()
    if not records:
        print("No attendance data found!")
        return

    # Convert to DataFrame
    df = pd.DataFrame(records, columns=['name', 'date', 'hour'])
    df['date'] = pd.to_datetime(df['date'])
    
    # Create figure
    fig = plt.figure(figsize=(12, 6))
    fig.patch.set_facecolor('#f0f2f6')
    
    # Group by date and name
    daily_attendance = df.groupby(['date', 'name']).size().unstack(fill_value=0)
    
    # Create line plot
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD', '#FFD93D', '#6C5B7B', '#355C7D']
    daily_attendance.plot(kind='line', marker='o', color=colors[:len(daily_attendance.columns)])
    
    # Customize plot
    plt.title('Attendance Trends', fontsize=14, fontweight='bold', color='#2C3E50')
    plt.xlabel('Date', fontsize=12, color='#2C3E50')
    plt.ylabel('Classes Attended', fontsize=12, color='#2C3E50')
    plt.legend(title='Students', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    plt.show()

def create_modern_dashboard(parent=None):
    """Create a modern dashboard-style visualization"""
    records = get_attendance_records()
    stats, total_classes = get_attendance_stats()
    
    if not records or not stats:
        print("No attendance data found!")
        return

    # Create the main window
    if parent is None:
        root = tk.Tk()
    else:
        root = tk.Toplevel(parent)
        root.transient(parent)  # Make this window stay on top of parent
        root.grab_set()  # Make this window modal
    
    # Configure window
    root.title("Attendance Dashboard")
    root.geometry("1400x900")
    root.minsize(1200, 800)  # Set minimum window size
    root.resizable(True, True)  # Allow window resizing
    
    # Create main container with padding
    main_frame = ttk.Frame(root, padding="10")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Create figure for plots with adjusted size
    fig = plt.figure(figsize=(13, 7))
    fig.patch.set_facecolor('#f0f2f6')
    
    # Create grid layout with adjusted spacing
    gs = GridSpec(2, 2, figure=fig, height_ratios=[1, 1], wspace=0.25, hspace=0.3)
    
    # Modern color palette
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD', '#FFD93D', '#6C5B7B', '#355C7D']
    
    # Convert records to DataFrame
    df = pd.DataFrame(records, columns=['name', 'date', 'hour'])
    df['date'] = pd.to_datetime(df['date'])
    
    # 1. Top Left: Attendance Overview (Donut Chart)
    ax1 = fig.add_subplot(gs[0, 0])
    names = [s[0] for s in stats]
    percentages = [s[2] for s in stats]
    
    pie_result = ax1.pie(
        percentages,
        labels=names,
        colors=colors[:len(names)],
        autopct='%1.1f%%',
        startangle=90,
        pctdistance=0.85,
        wedgeprops=dict(width=0.5, edgecolor='white', linewidth=2)
    )
    wedges, texts = pie_result[:2]
    autotexts = pie_result[2] if len(pie_result) > 2 else []
    
    ax1.set_title('Attendance Distribution', pad=20, fontsize=14, fontweight='bold', color='#2C3E50')
    
    # 2. Top Right: Daily Attendance (Bar Chart)
    ax2 = fig.add_subplot(gs[0, 1])
    daily_counts = df.groupby(['date', 'name']).size().unstack(fill_value=0)
    daily_counts.plot(kind='bar', ax=ax2, color=colors[:len(daily_counts.columns)])
    
    ax2.set_title('Daily Attendance', fontsize=14, fontweight='bold', color='#2C3E50')
    ax2.set_xlabel('Date', fontsize=12, color='#2C3E50')
    ax2.set_ylabel('Classes Attended', fontsize=12, color='#2C3E50')
    ax2.legend(title='Students', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
    
    # 3. Bottom: Hourly Distribution (Stacked Area)
    ax3 = fig.add_subplot(gs[1, :])
    hourly_data = df.groupby(['hour', 'name']).size().unstack(fill_value=0)
    hourly_data.plot(kind='area', ax=ax3, color=colors[:len(hourly_data.columns)], alpha=0.7)
    
    ax3.set_title('Hourly Attendance Distribution', fontsize=14, fontweight='bold', color='#2C3E50')
    ax3.set_xlabel('Hour of Day', fontsize=12, color='#2C3E50')
    ax3.set_ylabel('Number of Students', fontsize=12, color='#2C3E50')
    ax3.legend(title='Students', bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Add title to the entire dashboard
    fig.suptitle('Student Attendance Dashboard', fontsize=24, fontweight='bold', y=0.95, color='#2C3E50')
    
    # Create canvas for the plots with padding
    canvas_frame = ttk.Frame(main_frame)
    canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 10))
    
    canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    # Create summary frame with padding
    summary_frame = ttk.LabelFrame(main_frame, text="Attendance Summary", padding="5")
    summary_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
    
    # Create text widget for summary with padding
    text_widget = tk.Text(summary_frame, wrap=tk.WORD, width=100, height=8)
    text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # Add scrollbar
    scrollbar = ttk.Scrollbar(summary_frame, orient="vertical", command=text_widget.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    text_widget.configure(yscrollcommand=scrollbar.set)
    
    # Create summary text
    summary_text = "=== Attendance Summary ===\n\n"
    summary_text += f"Total Classes: {total_classes}\n"
    summary_text += f"Total Students: {len(stats)}\n\n"
    
    for name, present, percentage in stats:
        summary_text += f"{name}:\n"
        summary_text += f"  Classes: {present}/{total_classes}\n"
        summary_text += f"  Percentage: {percentage:.1f}%\n"
        
        student_hours = df[df['name'] == name]['hour'].value_counts()
        if not student_hours.empty:
            most_common_hour = student_hours.index[0]
            summary_text += f"  Peak Hour: {most_common_hour}:00\n"
        summary_text += "\n"
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    summary_text += f"\nGenerated: {timestamp}"
    
    # Insert summary text
    text_widget.insert(tk.END, summary_text)
    text_widget.config(state=tk.DISABLED)
    
    # Adjust layout
    fig.subplots_adjust(top=0.9, bottom=0.1, left=0.1, right=0.9, hspace=0.4, wspace=0.3)
    
    # Make sure the window stays on top initially
    root.lift()
    root.attributes('-topmost', True)
    root.after_idle(root.attributes, '-topmost', False)
    
    # Start the Tkinter event loop only if this is a standalone window
    if parent is None:
        root.mainloop()

def visualize_attendance():
    """Show the attendance dashboard"""
    while True:
        print("\n=== Attendance Dashboard ===")
        print("1. Show Dashboard")
        print("2. Show Pie Chart")
        print("3. Show Bar Chart")
        print("4. Show Line Chart")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == '1':
            create_modern_dashboard()
        elif choice == '2':
            show_attendance_pie()
        elif choice == '3':
            show_attendance_bar()
        elif choice == '4':
            show_attendance_line()
        elif choice == '5':
            break
        else:
            print("Invalid choice! Please try again.")

if __name__ == "__main__":
    visualize_attendance()