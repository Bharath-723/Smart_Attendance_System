import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import configparser
import os
from database import get_contact_info, get_daily_absences, get_attendance_records
from datetime import datetime
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import io

def send_notifications(name):
    """Send email notification to parent/teacher when attendance is marked."""
    try:
        print(f"\n📧 Attempting to send email notification for {name}")
        
        # Get contact info from database
        contact_info = get_contact_info(name)
        if not contact_info:
            print(f"❌ No contact info found for {name}")
            return
            
        parent_phone, email = contact_info
        print(f"📧 Found contact info - Email: {email}")
        
        # Load email configuration
        config = configparser.ConfigParser()
        config_path = os.path.join('data', 'config.ini')
        if not os.path.exists(config_path):
            print(f"❌ Config file not found at {config_path}")
            return
            
        config.read(config_path)
        print("📧 Loaded email configuration")
        
        sender_email = config['EMAIL']['EMAIL']
        sender_password = config['EMAIL']['PASSWORD']
        smtp_server = config['EMAIL']['SMTP_SERVER']
        smtp_port = int(config['EMAIL']['SMTP_PORT'])
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = f"Attendance Marked - {name}"
        
        body = f"""
        Dear Parent/Guardian,
        
        This is to inform you that attendance has been marked for {name}.
        
        Best regards,
        Face Attendance System
        """
        
        msg.attach(MIMEText(body, 'plain'))
        print(f"📧 Created email message for {email}")
        
        # Send email
        print(f"📧 Connecting to SMTP server {smtp_server}:{smtp_port}")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            print("📧 Starting TLS connection")
            server.starttls()
            print("📧 Attempting login")
            server.login(sender_email, sender_password)
            print("📧 Sending message")
            server.send_message(msg)
            
        print(f"✅ Email notification sent to {email}")
        
    except Exception as e:
        print(f"❌ Email notification error: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")

def generate_teacher_report(teacher, date=None):
    """Generate a daily attendance report for teacher's assigned hours."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    # Get absences for teacher's hours (for today only)
    absences = get_daily_absences(date, teacher['hours'])
    
    # Create a DataFrame for the report (only absentees)
    report_data = []
    for hour, student in absences:
        report_data.append({
            'Hour': hour,
            'Student': student,
            'Status': 'Absent'
        })
    
    df = pd.DataFrame(report_data)
    if not df.empty:
        df = df.sort_values(['Hour', 'Student'])
    
    # Create a figure for visualization
    plt.figure(figsize=(10, 6))
    hours = sorted(teacher['hours'])
    present_counts = []
    absent_counts = []
    
    # For the plot, we still need present/absent counts
    # Get attendance records for the day
    records = get_attendance_records()
    today_records = [r for r in records if r[1] == date and r[2] in teacher['hours']]
    for hour in hours:
        hour_data = [r for r in today_records if r[2] == hour]
        present = len(hour_data)
        absent = len([a for a in absences if a[0] == hour])
        present_counts.append(present)
        absent_counts.append(absent)
    
    x = range(len(hours))
    width = 0.35
    plt.bar(x, present_counts, width, label='Present', color='green', alpha=0.6)
    plt.bar(x, absent_counts, width, bottom=present_counts, label='Absent', color='red', alpha=0.6)
    plt.title(f'Attendance Report for {date}')
    plt.xlabel('Hour')
    plt.ylabel('Number of Students')
    plt.xticks(x, hours)
    plt.legend()
    plt.grid(True, alpha=0.3)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    # Create CSV report (only absentees)
    csv_buf = io.BytesIO()
    df.to_csv(csv_buf, index=False)
    csv_buf.seek(0)
    
    return buf, csv_buf, df

def send_teacher_report(teacher):
    """Send daily attendance report to teacher."""
    try:
        print(f"\n📧 Attempting to send teacher report to {teacher['name']}")
        
        # Generate report
        date = datetime.now().strftime("%Y-%m-%d")
        plot_buf, csv_buf, df = generate_teacher_report(teacher, date)
        
        # Load email configuration
        config = configparser.ConfigParser()
        config_path = os.path.join('data', 'config.ini')
        if not os.path.exists(config_path):
            print(f"❌ Config file not found at {config_path}")
            return
            
        config.read(config_path)
        print("📧 Loaded email configuration")
        
        sender_email = config['EMAIL']['EMAIL']
        sender_password = config['EMAIL']['PASSWORD']
        smtp_server = config['EMAIL']['SMTP_SERVER']
        smtp_port = int(config['EMAIL']['SMTP_PORT'])
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = teacher['email']
        msg['Subject'] = f"Daily Attendance Report - {date}"
        
        # Create email body with summary
        total_students = len(df['Student'].unique()) if not df.empty else 0
        present_count = len(df[df['Status'] == 'Present']) if not df.empty else 0
        absent_count = len(df[df['Status'] == 'Absent']) if not df.empty else 0
        
        body = f"""
        Dear {teacher['name']},
        
        Please find attached the daily attendance report for your assigned hours ({', '.join(map(str, teacher['hours']))}).
        
        Summary for {date}:
        - Total Students: {total_students}
        - Present: {present_count}
        - Absent: {absent_count}
        
        The attached CSV file contains detailed attendance records, and the PNG file shows a visual summary.
        
        Best regards,
        Face Attendance System
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach the plot
        plot_attachment = MIMEApplication(plot_buf.getvalue(), _subtype='png')
        plot_attachment.add_header('Content-Disposition', 'attachment', 
                                 filename=f'attendance_report_{date}.png')
        msg.attach(plot_attachment)
        
        # Attach the CSV file
        csv_attachment = MIMEApplication(csv_buf.getvalue(), _subtype='csv')
        csv_attachment.add_header('Content-Disposition', 'attachment', 
                                  filename=f'attendance_report_{date}.csv')
        msg.attach(csv_attachment)
        
        print(f"📧 Created email message for {teacher['email']}")
        
        # Send email
        print(f"📧 Connecting to SMTP server {smtp_server}:{smtp_port}")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            print("📧 Starting TLS connection")
            server.starttls()
            print("📧 Attempting login")
            server.login(sender_email, sender_password)
            print("📧 Sending message")
            server.send_message(msg)
            
        print(f"✅ Daily report sent to {teacher['email']}")
        
    except Exception as e:
        print(f"❌ Report sending error: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}") 