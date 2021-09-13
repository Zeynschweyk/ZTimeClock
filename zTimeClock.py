from ast import Index
from sqlite3.dbapi2 import Error, PARSE_DECLTYPES
from tkinter import *
from tkinter import ttk
import tkinter.ttk
from tkinter import messagebox
import sqlite3
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
import random
from calendar import month, monthrange, week
from typing import AsyncContextManager
import smtplib
import mimetypes
from email.message import EmailMessage
#from openpyxl import load_workbook
import xlsxwriter as xl
import json
from tkinter.filedialog import askdirectory, asksaveasfile, asksaveasfilename

program_files_path = ""
database_file = program_files_path + "employee_time_clock.db"

root = Tk()
root.iconbitmap(program_files_path + "ChemtrolImage.ico")
width= root.winfo_width()
height= root.winfo_height()
root.geometry("%dx%d" % (1200, 773))
root.resizable(width=False, height=False)
root.title("SBCS (Chemtrol)")

def disable_event():
    pass

def validate_timestamp(time_string, format):
    try:
        datetime.strptime(time_string, format)
    except ValueError:
        return False
    else:
        return True

def insert_request(emp_id, time_string, format, clocked_in_time):
    if validate_timestamp(time_string, format) :
        conn = sqlite3.connect(database_file)
        c = conn.cursor()

        clock_out = datetime.strptime(time_string, format)
        clock_in = datetime.strptime(clocked_in_time, "%H:%M:%S")

        if clock_out.time() >= clock_in.time():
            formatted_time = datetime.strptime(time_string, format).strftime("%H:%M:%S")
            max_row = c.execute(f"SELECT row, ClockIn, Request FROM time_clock_entries WHERE empID = '{emp_id}' ORDER BY row DESC LIMIT 1;").fetchone()
            c.execute(f"UPDATE time_clock_entries SET ClockOut = 'FORGOT', Request = '{max_row[1][:10]} {formatted_time}' WHERE row = '{max_row[0]}';")
            conn.commit()
            conn.close()
            # if max_row[2] is None:
            messagebox.showinfo("Thank You", f"Your timestamp request of \"{time_string}\" has been sent to management for approval.")
            clear([greeting, enter_actual_clock_out_time_label], [enter_actual_clock_out_time_entry, actual_clock_out_time_submit_button], True, None)
            id_field.delete(0, "end")
            button.config(command=enter) 

            # else:
            #     replaced = datetime.strptime(max_row[2][11:], "%H:%M:%S").strftime("%I:%M:%S %p")
            #     messagebox.showinfo("Successful", f"Your timestamp request of \"{time_string}\" has been replaced by your previous request of \"{replaced}\", and has been sent to management for approval.")
        else:
            messagebox.showerror("Clock Out < Clock In", "Entry must be greater than or equal to your clock in timestamp.")
    else:
        messagebox.showerror("Wrong Time Format", "Enter timestamp in the format of \"HH:MM:SS am/pm\"")
        
    return

#root.config(bg="white")
def send_email(sender, password, recipient, body, subject, file_path):
    #Make file_path = "" if you don't want to send an attachment.
    message = EmailMessage()
    message['From'] = sender
    message['To'] = recipient
    message['Subject'] = subject
    message.set_content(body)

    if file_path != "":
        mime_type, _ = mimetypes.guess_type(file_path)
        mime_type, mime_subtype = mime_type.split('/')
        with open(file_path, 'rb') as file:
            message.add_attachment(file.read(),
            maintype=mime_type,
            subtype=mime_subtype,
            filename=file_path)

    mail_server = smtplib.SMTP_SSL('smtp.gmail.com')
    mail_server.set_debuglevel(1)
    mail_server.login(sender, password)
    mail_server.send_message(message)
    mail_server.quit()

    

def is_this_a_pay_day(date_in, format):
    date_in = datetime.strptime(date_in, format)
    last_day_of_month = monthrange(date_in.year, date_in.month)[1]

    # check if the date is the 15th, the end of the month, and it's a weekday
    if (date_in.day == 15 or date_in.day == last_day_of_month) and date_in.weekday() <= 4:
        return True
    else:
        # check if the date is <= the 15th, or the end of the month, by two days or less, and it's a Friday
        if ((date_in.day >= 13 and date_in.day <= 15) or (date_in.day >= last_day_of_month - 2 and date_in.day <= last_day_of_month)) and date_in.weekday() == 4: 
            return True
        else:
            return False

def send_report_if_pay_day():
    today = datetime.today()
    todays_date_as_string = today.strftime("%m/%d/%y")
    last_day_of_month = monthrange(today.year, today.month)[1]

    if today.day == 15 or today.day == last_day_of_month:
        final_list = []
        end_of_pay_period = todays_date_as_string
        if today.day == 15:
            all_emp_ids = get_all_emp_ids()
            beginning_of_pay_period = f"{str(today.month)}/01/{str(today.year)[2:4]}"
            for emp_id in all_emp_ids:
                final_list.append({"EmpID": str(emp_id[0]), "FLast": emp_id[1][0] + emp_id[2]} | calculate_employee_pay(beginning_of_pay_period, end_of_pay_period, "%m/%d/%y", str(emp_id[0])))
        else:
            all_emp_ids = get_all_emp_ids()
            beginning_of_pay_period = f"{str(today.month)}/16/{str(today.year)[2:4]}"
            for emp_id in all_emp_ids:
                final_list.append({"EmpID": str(emp_id[0]), "FLast": emp_id[1][0] + emp_id[2]} | calculate_employee_pay(beginning_of_pay_period, end_of_pay_period, "%m/%d/%y", str(emp_id[0])))

        json_string = json.dumps(final_list, indent=4)
        filename = program_files_path + "z_time_clock_report.json"
        jsonFile = open(filename, "w")
        jsonFile.write(json_string)
        jsonFile.close()
        body = """Time Clock Report,

    Below is the ZTimeClock report for this pay period. Please reply to this email for any questions.

    Happy Payrolling :)

    Sincerely,
    ZTimeClock
        """
        send_email("zschweyk@gmail.com", "Gmail1215!", "mrtaquito04@gmail.com", body, "ZTimeClock Pay Period Report for Chemtrol", filename)

# I'm not sure how to send a database file. It has a problem with the following line of code:
# mime_type, mime_subtype = mime_type.split('/')
# and says that it is NoneType. So instead

    root.after(24*60*60*1000, send_report_if_pay_day)
    return

def get_all_emp_ids():
    conn = sqlite3.connect(database_file)
    c = conn.cursor()

    ids = c.execute("SELECT ID, FirstName, LastName FROM employees").fetchall()

    conn.commit()
    conn.close()
    return ids

def greeting_time():
    global day_time_greeting
    string = ""
    hour = int(time.strftime("%H"))
    if hour < 12:
        string = "Good Morning"
    elif hour < 18:
        string = "Good Afternoon"
    else:
        string = "Good Evening"

    day_time_greeting.config(text=string)
    day_time_greeting.after(1000, greeting_time)


def subtract_time(t2, t1):
    d1 = datetime.strptime(t1, "%Y-%m-%d %H:%M:%S").timestamp()
    d2 = datetime.strptime(t2, "%Y-%m-%d %H:%M:%S").timestamp()
    return d2 - d1

def add_time_stamps(array):
    d1 = datetime.strptime(array[0], "%H:%M:%S")
    for str in range(1, len(array)):
        d1 += datetime.strptime(str, "%H:%M:%S")
    return d1



def format_seconds_to_hhmmss(seconds):
    hours = seconds // (60*60)
    seconds %= (60*60)
    minutes = seconds // 60
    seconds %= 60
    return "%02i:%02i:%02i" % (hours, minutes, seconds)

def clock():
    hour = time.strftime("%I")
    minute = time.strftime("%M")
    second = time.strftime("%S")
    am_pm = time.strftime("%p")
    day = time.strftime("%A")
    current_date = time.strftime("%x")
    program_clock.config(text=hour + ":" + minute + ":" + second + " " + am_pm)
    day_of_week.config(text=day[:3] + " " + current_date)
    program_clock.after(1000, clock)

def getWeekDays(todays_date, format):
    array_of_week_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    week_day = datetime.strptime(todays_date, format).weekday()
    today = datetime.strptime(todays_date, format)
    day_of_week = today
    result_array = []
    for i in range(week_day + 1):
        day_of_week = str(today - timedelta(days=week_day-i))
        result_array.append([array_of_week_days[i], day_of_week[5:7] + "/" + day_of_week[8:10] + "/" + day_of_week[0:4]])
    return result_array

def getArrayOfDates(start, end, entered_format, result_format):
    start_date = datetime.strptime(start, entered_format)
    end_date = datetime.strptime(end, entered_format)
    result_array = [start_date.strftime(result_format)]
    while start_date < end_date:
        start_date += timedelta(days=1)
        result_array.append(start_date.strftime(result_format))
    return result_array

def add_subtract_days(todays_date, format, num_of_days):
    today = datetime.strptime(todays_date, format)
    new_date = str(today + timedelta(days=num_of_days))
    new_date = new_date[5:7] + "/" + new_date[8:10] + "/" + new_date[0:4]
    return new_date

def getTodaysWeekDayAndDate():
    today = datetime.strptime(str(datetime.now().date()), "%Y-%m-%d")
    array_of_week_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    week_day = array_of_week_days[today.weekday()]
    todays_date = str(today.date())
    #todays_date = todays_date[5:7] + "/" + todays_date[8:10] + "/" + todays_date[0:4]
    todays_date = todays_date[:10]
    result = [week_day, todays_date]
    return result

def getWeekDayFromDate(entered_date, format):
    array_of_week_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    week_day = datetime.strptime(entered_date, format).weekday()
    return array_of_week_days[week_day]

def change_date_format(entered_date, input_format, output_format):
    initial_format = datetime.strptime(entered_date, input_format)
    new_format = initial_format.strftime(output_format)
    return new_format


def enter():
    conn = sqlite3.connect(database_file)
    c = conn.cursor()

    global greeting
    global time_in
    global time_out
    global time_duration
    global button
    button.config(text="Clear", command=lambda: clear([greeting, time_in, time_out, time_duration, day_total, period_total, period_days, period_daily_hours, employee_task_header_label, employee_task_label, enter_actual_clock_out_time_label], [forward, backward, enter_actual_clock_out_time_entry, actual_clock_out_time_submit_button], True, None))

    
    #Add the following as parameters to the clear function above.
    #Labels: employee_list_label, employee_hours_label, start_date_label, end_date_label
    #Buttons: employee_hours_button, employee_start_date, employee_end_date

    
    #root.bind("<Return>", lambda event=None: button.invoke())
    root.bind("<Return>", lambda event=None: button.invoke())
      



    if id_field.get() != "admin":
        emp_record = c.execute("SELECT FirstName, LastName FROM employees WHERE ID = '" + id_field.get() + "'").fetchone()
        if emp_record is not None:
            name = str(emp_record[0]) + " " + str(emp_record[1])

            time_clock_entries_record = c.execute("SELECT row, ClockIn, ClockOut FROM time_clock_entries WHERE empID = '" + id_field.get() + "' ORDER BY row DESC LIMIT 1;").fetchone()

            inOrOut = ""
            greeting_text = []
            
            if time_clock_entries_record is None or (time_clock_entries_record[1] is not None and time_clock_entries_record[2] is not None):
                #Clocked IN
                inOrOut = "In"
                greeting_text = ["Welcome", "Greetings", "Hello", "Have a great day", "Have a productive day", "Have a fun work day"]
                c.execute("INSERT INTO time_clock_entries(empID, ClockIn) VALUES('" + str(id_field.get()) + "', DateTime('now', 'localtime'));")
                conn.commit()
            elif time_clock_entries_record[1] is not None and time_clock_entries_record[2] == None:
                #Clocked OUT
                inOrOut = "Out"
                greeting_text = ["Goodbye", "Have a nice day", "See you later", "Have a wonderful day", "Thank you for your great work"]
                #c.execute("UPDATE time_clock_entries SET ClockOut = DateTime('now', 'localtime') WHERE row = " + str(time_clock_entries_record[0]) + ";")

                if time_clock_entries_record[1][:10] == getTodaysWeekDayAndDate()[1]:
                    c.execute("UPDATE time_clock_entries SET ClockOut = DateTime('now', 'localtime') WHERE row = " + str(time_clock_entries_record[0]) + ";")
                    conn.commit()
                else:
                    #c.execute("UPDATE time_clock_entries SET ClockOut = '" + str(time_clock_entries_record[1]) + "' WHERE row = '" + str(time_clock_entries_record[0]) + "';")
                    #c.execute("UPDATE time_clock_entries SET ClockOut = '" + "FORGOT" + "' WHERE row = '" + str(time_clock_entries_record[0]) + "';")

                    rand = random.randint(0, len(greeting_text)-1)
                    conn.commit()
                    conn.close()

                    clocked_in_time = datetime.strptime(time_clock_entries_record[1][11:], "%H:%M:%S")

                    #enter_actual_clock_out_time_label.config(text="Enter the time you clocked out at in the following format \"HH:MM:SS am/pm\", in order to be able to clock in again. Your request will be sent to management for approval.", wraplength=700)
                    enter_actual_clock_out_time_entry.delete(0, "end")
                    enter_actual_clock_out_time_entry.place(relx=.46, rely=.65, anchor=N)

                    actual_clock_out_time_submit_button.config(command=lambda: insert_request(id_field.get(), enter_actual_clock_out_time_entry.get(), "%I:%M:%S %p", clocked_in_time.strftime("%H:%M:%S")))
                    actual_clock_out_time_submit_button.place(relx=.55, rely=.6375)

                    # button.config(state=DISABLED)
                    # root.protocol("WM_DELETE_WINDOW", disable_event)
                    
                    
                    return greeting.config(text=name + ",\nyou forgot to clock out after your last clock in on " + getWeekDayFromDate(time_clock_entries_record[1][:10], "%Y-%m-%d") + ", " + datetime.strptime(time_clock_entries_record[1][:10], "%Y-%m-%d").strftime("%m/%d/%Y") + " at " + clocked_in_time.strftime("%I:%M:%S %p") + ".\n\nEnter the time you clocked out at in the following format \"HH:MM:SS am/pm\", in order to be able to clock in again. Your request will be sent to management for approval.", fg="red")

            # inOrOut = ""
            # in_greeting = ["Welcome", "Greetings", "Hello", "Have a great day", "Have a productive day", "Have a fun work day"]
            # out_greeting = ["Goodbye", "Have a nice day", "See you later", "Have a wonderful day", "Thank you for your great work"]
            # greeting_text = []

            # time_clock_entries_record = c.execute("SELECT row, ClockIn, ClockOut FROM time_clock_entries WHERE empID = '" + id_field.get() + "';").fetchall()
            # if len(time_clock_entries_record) == 0:
            #     #CLocked In
            #     inOrOut = "In"
            #     greeting_text = in_greeting
            #     c.execute("INSERT INTO time_clock_entries(empID, ClockIn) VALUES(" + str(id_field.get()) + ", DateTime('now', 'localtime'));")
            #     print("Entered if")
            # else:
            #     for i in range(len(time_clock_entries_record)):
            #         row = time_clock_entries_record[i][0]
            #         clock_in = time_clock_entries_record[i][1]
            #         clock_out = time_clock_entries_record[i][2]

                    

                    
            #         if clock_in is None and clock_out is not None and clock_out[:10] == getTodaysWeekDayAndDate()[1]:
            #             #Clocked In. This if statement only executes when the admin manually enters a datetime for ClockOut, but leaves ClockIn blank.
            #             inOrOut = "In"
            #             greeting_text = in_greeting
            #             c.execute("UPDATE time_clock_entries SET ClockIn = DateTime('now', 'localtime') WHERE row = " + str(row) + ";")
            #             break
            #         elif clock_in is not None and clock_out is None and clock_in[:10] == getTodaysWeekDayAndDate()[1]:
            #             #Clocked Out
            #             inOrOut = "Out"
            #             greeting_text = out_greeting
            #             c.execute("UPDATE time_clock_entries SET ClockOut = DateTime('now', 'localtime') WHERE row = " + str(row) + ";")
            #             break
            #         elif clock_in is not None and clock_out is not None and i == len(time_clock_entries_record) - 1:
            #             #Clocked In
            #             inOrOut = "In"
            #             greeting_text = in_greeting
            #             c.execute("INSERT INTO time_clock_entries(empID, ClockIn) VALUES(" + id_field.get() + ", DateTime('now', 'localtime'));")
            #             break
                        

                    
            # conn.commit()
                    





            rand = random.randint(0, len(greeting_text)-1)
            #greeting.config(text=greeting_text[rand] + " " + name + ", you have been clocked " + inOrOut + "!\nToday's history:")
            
            
            
            
            
            
            
            
            
            
            
            
            
            # time_in_out_records = c.execute("SELECT ClockIn, ClockOut FROM time_clock_entries WHERE empID = '" + str(id_field.get()) + "' AND ClockIn LIKE '%" + str(date.today()) + "%';").fetchall()

            # print_time_in_records = ""
            # print_time_out_records = ""
            # print_duration_records = ""
            # total_seconds = 0
            # #times_array = []
            # for record in time_in_out_records:
            #     print_time_in_records += datetime.strptime(record[0][11:], "%H:%M:%S").strftime("%I:%M:%S %p") + "\n"
                
            #     if record[1] is not None:
            #         print_time_out_records += datetime.strptime(record[1][11:], "%H:%M:%S").strftime("%I:%M:%S %p") + "\n"
            #         t1 = datetime.strptime(record[1], "%Y-%m-%d %H:%M:%S").timestamp()
            #         t2 = datetime.strptime(record[0], "%Y-%m-%d %H:%M:%S").timestamp()
            #         total_seconds += t1 - t2
            #         diff = format_seconds_to_hhmmss(t1 - t2)
            #         print_duration_records += diff + "\n"
                    

            #         #t2 = record[1]
            #         #t1 = record[0]
            #         #time_difference = subtract_time(t2, t1)
            #         #times_array.append(str(time_difference))
            #         #print_duration_records += str(time_difference) + "\n"
            #     else:
            #         print_time_out_records += "\n"

            # time_in.config(text="\nTime In\n-----------\n" + print_time_in_records)

            # time_out.config(text="\nTime Out\n-----------\n" + print_time_out_records)

            # #time_duration.config(text="\nDuration\n-----------\n" + print_duration_records + "\nDay Total " + format_seconds_to_hhmmss(total_seconds))
            # time_duration.config(text="\nDuration\n-----------\n" + print_duration_records)
            # #time_duration.config(text="Duration\n-----------\n" + print_duration_records + "\nDay Total " + add_time_stamps(times_array))

            # forward.place(relx=.3, rely=.17, anchor=N)
            # backward.place(relx=.2, rely=.17, anchor=N)

            forward.place(relx=.52, rely=.6, anchor=N)
            backward.place(relx=.48, rely=.6, anchor=N)

            global current_date_mm_dd_yy
            current_date_mm_dd_yy = datetime.strptime(str(datetime.now().date()), "%Y-%m-%d").date()
            calculate_and_display_day_totals(0, id_field.get())

















            
            greeting.config(text=greeting_text[rand] + "\n" + name + "\n\nYou are clocked " + inOrOut, fg="green")
            global entered_id
            entered_id = id_field.get()
            
            # day_total.config(text="Today's Total - " + format_seconds_to_hhmmss(total_seconds))
            
            # dates = getPeriodDays()
            # displayed_dates = "Date\n-----------\n"
            # displayed_daily_hours = "Total Hours\n-----------\n"
            # period_hours_sum = 0
            # for adate in dates:
            #     displayed_dates += adate + "\n"
            #     #period_hours_sum += getRawTotalEmployeeHours(adate, "%m/%d/%y", id_field.get())
            #     #displayed_daily_hours += str(getRawTotalEmployeeHours(adate, "%m/%d/%y", id_field.get())) + "\n"
            #     period_hours_sum += getTotalDailyHoursAccountingForBreaks(adate, "%m/%d/%y", entered_id)
            #     displayed_daily_hours += str(getTotalDailyHoursAccountingForBreaks(adate, "%m/%d/%y", entered_id)) + "\n"

            # period_total.config(text="Period's Total Hours - " + str(round(period_hours_sum, 3)))
            # period_days.config(text=displayed_dates)
            # period_daily_hours.config(text=displayed_daily_hours)

            calculate_and_display_period_totals_for_employees(entered_id)


            #Retreive task from database table and display it on the screen
            # employee_task_header_label.config(text="Your Task")
            # today = datetime.strptime(str(datetime.now().date()), "%Y-%m-%d").strftime("%m/%d/%Y")
            # employee_task_label.config(text=selectTask(id_field.get(), today, "%m/%d/%Y"))
            fetch_and_display_task(entered_id)
            

            id_field.delete(0, END)
        else:
            greeting.config(text="Incorrect Password", fg="red")

        conn.commit()
        conn.close()
    else:
        id_field.delete(0, END)
        greeting.config(text="Hello Admin!", fg="green")

        #main_menu.config(text="Main Menu")
        main_menu.place(relx=.5, rely=.425, anchor=N)

        global main_menu_buttons
        main_menu_buttons = [["Employee Codes", employee_codes_function], ["Assign Tasks", assign_tasks_function], ["This Period's Totals", period_totals_function], ["Historical Totals", historical_totals_function]]

        global employee_codes_child_buttons
        employee_codes_child_buttons = [["Add New Employee", employee_codes__add_new_employee_function], ["Edit", employee_codes__edit_function], ["Delete", employee_codes__delete_function], ["View", employee_codes__view_function]]

        fill_frame(main_menu, main_menu_buttons, "Main Menu", None)



        conn.commit()
        conn.close()

def fetch_and_display_task(id):
    task = selectTask(id, str(current_date_mm_dd_yy), "%Y-%m-%d")
    if current_date_mm_dd_yy == datetime.strptime(str(datetime.now().date()), "%Y-%m-%d").date():
        employee_task_header_label.config(text="Today's Task")
    else:
        employee_task_header_label.config(text=str(current_date_mm_dd_yy)[5:7] + "/" + str(current_date_mm_dd_yy)[8:10] + "/" + str(current_date_mm_dd_yy)[2:4] + " Task")

    employee_task_label.config(text=task)
    return

def calculate_and_display_period_totals_for_employees(id):
    dates = getPeriodFromDateString(str(current_date_mm_dd_yy), "%Y-%m-%d")
    current_period_dates = getPeriodDays()

    displayed_dates = "Date\n-----------\n"
    displayed_daily_hours = "Total Hours\n-----------\n"
    period_hours_sum = 0
    for adate in dates:
        displayed_dates += adate + "\n"
        #period_hours_sum += getRawTotalEmployeeHours(adate, "%m/%d/%y", id_field.get())
        #displayed_daily_hours += str(getRawTotalEmployeeHours(adate, "%m/%d/%y", id_field.get())) + "\n"
        period_hours_sum += getTotalDailyHoursAccountingForBreaks(adate, "%m/%d/%y", id)
        displayed_daily_hours += str(getTotalDailyHoursAccountingForBreaks(adate, "%m/%d/%y", id)) + "\n"
    if dates[0] == current_period_dates[0]:
        period_total.config(text="Current\nPeriod's Total Hours: " + str(round(period_hours_sum, 3)))
    else:
        #print(current_date_mm_dd_yy - dates[-1])

        last_day_of_period = ""
        current_date = str(current_date_mm_dd_yy)
        day = int(current_date[8:10])
        month = current_date[5:7]
        year = current_date[:4]
        num_of_days_in_month = monthrange(current_date_mm_dd_yy.year, int(month))[1]
        #mm/dd/yy
        if day >= 1 and day < 16:
            last_day_of_period = f"{month}/15/{year}"
        else:
            last_day_of_period = f"{month}/{num_of_days_in_month}/{year}"
        period_total.config(text=last_day_of_period + "\nPeriod's Total Hours: " + str(round(period_hours_sum, 3)))

    period_days.config(text=displayed_dates)
    period_daily_hours.config(text=displayed_daily_hours)


def previous_day_totals():
    # conn = sqlite3.connect(database_file)
    # c = conn.cursor()

    

    # global current_date_mm_dd_yy
    # global entered_id
    # current_date_mm_dd_yy -= timedelta(days=1)

    # time_in_out_records = c.execute("SELECT ClockIn, ClockOut FROM time_clock_entries WHERE empID = '" + str(entered_id) + "' AND ClockIn LIKE '%" + str(current_date_mm_dd_yy) + "%';").fetchall()

    # print_time_in_records = ""
    # print_time_out_records = ""
    # print_duration_records = ""
    # total_seconds = 0
    # #times_array = []
    # for record in time_in_out_records:
    #     print_time_in_records += datetime.strptime(record[0][11:], "%H:%M:%S").strftime("%I:%M:%S %p") + "\n"
                
    #     if record[1] is not None:
    #         print_time_out_records += datetime.strptime(record[1][11:], "%H:%M:%S").strftime("%I:%M:%S %p") + "\n"
    #         t1 = datetime.strptime(record[1], "%Y-%m-%d %H:%M:%S").timestamp()
    #         t2 = datetime.strptime(record[0], "%Y-%m-%d %H:%M:%S").timestamp()
    #         total_seconds += t1 - t2
    #         diff = format_seconds_to_hhmmss(t1 - t2)
    #         print_duration_records += diff + "\n"

    #     else:
    #         print_time_out_records += "\n"

    # time_in.config(text="\nTime In\n-----------\n" + print_time_in_records)

    # time_out.config(text="\nTime Out\n-----------\n" + print_time_out_records)

    # #time_duration.config(text="\nDuration\n-----------\n" + print_duration_records + "\nDay Total " + format_seconds_to_hhmmss(total_seconds))
    # time_duration.config(text="\nDuration\n-----------\n" + print_duration_records)

    # day_total.config(text=str(current_date_mm_dd_yy)[5:7] + "/" + str(current_date_mm_dd_yy)[8:10] + "/" + str(current_date_mm_dd_yy)[:4] + " Total - " + format_seconds_to_hhmmss(total_seconds))
    
    # conn.commit()
    # conn.close()
    global entered_id
    calculate_and_display_day_totals(-1, entered_id)
    fetch_and_display_task(entered_id)
    calculate_and_display_period_totals_for_employees(entered_id)
    return

def next_day_totals():
    global entered_id
    calculate_and_display_day_totals(1, entered_id)
    fetch_and_display_task(entered_id)
    calculate_and_display_period_totals_for_employees(entered_id)
    return

def calculate_and_display_day_totals(num_added_days, id):
    conn = sqlite3.connect(database_file)
    c = conn.cursor()

    global current_date_mm_dd_yy
    

    if current_date_mm_dd_yy + timedelta(days=num_added_days) >= datetime.strptime(str(datetime.now().date()), "%Y-%m-%d").date():
        forward.config(state=DISABLED)
        #return
    else:
        forward.config(state=NORMAL)

    current_date_mm_dd_yy += timedelta(days=num_added_days)

    time_in_out_records = c.execute("SELECT ClockIn, ClockOut FROM time_clock_entries WHERE empID = '" + id + "' AND ClockIn LIKE '%" + str(current_date_mm_dd_yy) + "%';").fetchall()

    print_time_in_records = ""
    print_time_out_records = ""
    print_duration_records = ""
    total_seconds = 0
    #times_array = []
    for record in time_in_out_records:
        print_time_in_records += datetime.strptime(record[0][11:], "%H:%M:%S").strftime("%I:%M:%S %p") + "\n"
                
        if record[1] is not None:
            if record[1] != "FORGOT":
                print_time_out_records += datetime.strptime(record[1][11:], "%H:%M:%S").strftime("%I:%M:%S %p") + "\n"
                t1 = datetime.strptime(record[1], "%Y-%m-%d %H:%M:%S").timestamp()
                t2 = datetime.strptime(record[0], "%Y-%m-%d %H:%M:%S").timestamp()
                total_seconds += t1 - t2
                diff = format_seconds_to_hhmmss(t1 - t2)
                print_duration_records += diff + "\n"
            else:
                print_time_out_records += "FORGOT\n"

        else:
            print_time_out_records += "\n"

    time_in.config(text="\nTime In\n-----------\n" + print_time_in_records)

    time_out.config(text="\nTime Out\n-----------\n" + print_time_out_records)

    #time_duration.config(text="\nDuration\n-----------\n" + print_duration_records + "\nDay Total " + format_seconds_to_hhmmss(total_seconds))
    time_duration.config(text="\nDuration\n-----------\n" + print_duration_records)

    if current_date_mm_dd_yy == datetime.strptime(str(datetime.now().date()), "%Y-%m-%d").date():
        #format_seconds_to_hhmmss(total_seconds), this returns the raw duration that an employee spends at work.
        # The below function, getTotalDailyHoursAccountingForBreaks, shows the employee their total paid hours, which is calculated by considering the break hours and total day duration.
        day_total.config(text="Today's\nTotal Hours: " + str(getTotalDailyHoursAccountingForBreaks(str(current_date_mm_dd_yy), "%Y-%m-%d", id)))
    else:
        day_total.config(text=current_date_mm_dd_yy.strftime("%m/%d/%y") + "\nTotal Hours: " + str(getTotalDailyHoursAccountingForBreaks(str(current_date_mm_dd_yy), "%Y-%m-%d", id)))
    
    conn.commit()
    conn.close()
    return


#clear([id_label_widget, first_name_label_widget, last_name_label_widget, deparment_label_widget], [commit_changes], False, None)

def clear(all_labels, all_buttons, bool, reset_commands):
    #all_labels = [greeting, time_in, time_out, time_duration, employee_list_label, employee_hours_label]

    for label in all_labels:
        clear_widget_text(label)

    for single_button in all_buttons:
        single_button.place_forget()

    if reset_commands is not None:
        for row in reset_commands:
            row[0].config(command=row[1])

    #employee_hours_button.place_forget()
    if bool:
        button.config(text="Enter", command=enter)
        root.bind("<Return>", lambda event=None: button.invoke())
    
    clear_frame(main_menu)
    main_menu.place_forget()

def fill_frame(frame, button_names_and_funcs, frame_header, return_to_array):
    clear_frame(frame)
    frame.config(text=frame_header)
    global num_of_menu_items
    num_of_menu_items = len(button_names_and_funcs)
    for i in range(1, num_of_menu_items + 1):
        #menu_item_number = Label(frame, text=str(i) + ") ", font=("Arial", 15))
        #menu_item_number.grid(row=i-1, column=0, pady=15)
        menu_item = Button(frame, text=button_names_and_funcs[i-1][0], command=button_names_and_funcs[i-1][1])
        menu_item.grid(row=i-1, column=1, pady=15)
    #["text", function]
    if return_to_array != None:
        return_to_menu = Button(frame, text="Return to " + return_to_array[0], command=return_to_array[1], bg="red")
        return_to_menu.grid(row=num_of_menu_items, column=0, columnspan=2, pady=10)

def clear_frame(frame):
    for widget in frame.winfo_children():
        widget.destroy()

def main_menu_function():
    fill_frame(main_menu, main_menu_buttons, "Main Menu", None)
    return

def employee_codes_function():
    clear_frame(main_menu)
    #main_menu.config(text="Employee Codes")
    fill_frame(main_menu, employee_codes_child_buttons, "Employee Codes", ["Main Menu", main_menu_function])
    # return_to_main_menu = Button(main_menu, text="Return to Main Menu", command=lambda: fill_frame(main_menu, main_menu_buttons, "Main Menu"))
    # return_to_main_menu.grid(row=num_of_menu_items, column=0, columnspan=2)
    global_confirmation_text.set("")
    return

def assign_tasks_function():
    fill_frame(main_menu, [["Assign by Department", assign_tasks__by_department], ["Assign by Employee", assign_tasks__by_employee]], "Assign Tasks", ["Main Menu", main_menu_function])
    return

def assign_tasks__by_department():
    clear_frame(main_menu)
    assign_tasks_by_department_label = Label(main_menu, text="Department: ", font=("Arial", 15), pady=10, padx=10)
    assign_tasks_by_department_label.grid(row=0, column=0, sticky="e")

    #tkinter.ttk.Separator(main_menu, orient=VERTICAL).grid(row=0, column=1, rowspan=6, sticky="nsw", padx=10)

    none_department = StringVar()
    MG_department = StringVar()
    MK_department = StringVar()
    PD_department = StringVar()
    CL_department = StringVar()

    departments = ["None", "MG", "MK", "PD", "CL"]
    department_strvars = [none_department, MG_department, MK_department, PD_department, CL_department]

    next_row = 0
    for department, strvar, counter in zip(departments, department_strvars, range(len(departments))):
        Checkbutton(main_menu, text=department, variable=strvar, onvalue=department, offvalue="").grid(row=counter, column=1, sticky="w", pady=6)
        if counter == len(departments) - 1:
            next_row = counter + 1

    Label(main_menu, text="Seperate entries with (s) by commas and no spaces", font=("Arial", 8), pady=10, anchor=CENTER).grid(row=next_row, column=0, columnspan=2, sticky="ew")

    exclude_label = Label(main_menu, text="ID(s) to Exclude: ", font=("Arial", 15), pady=10, padx=10)
    exclude_label.grid(row=next_row+1, column=0, sticky="e")

    exclude_entry_widget = Entry(main_menu)
    exclude_entry_widget.grid(row=next_row+1, column=1, sticky="w")

    tkinter.ttk.Separator(main_menu, orient=HORIZONTAL).grid(row=next_row+2, column=0, columnspan=2, padx=10)

    #root.unbind("<Return>")

    task_label = Label(main_menu, text="Task: ", font=("Arial", 15), pady=10, padx=10)
    task_label.grid(row=next_row+3, column=0, sticky="e")

    task_entry = Text(main_menu, width=15, height=2)
    task_entry.grid(row=next_row+3, column=1, sticky="w")

    date_label = Label(main_menu, text="Date(s) mm/dd/yyyy: ", font=("Arial", 15), pady=10, padx=10)
    date_label.grid(row=next_row+4, column=0, sticky="e")

    date_entry = Entry(main_menu)
    date_entry.grid(row=next_row+4, column=1, sticky="w")

    submit_button = Button(main_menu, text="Assign Tasks", command=lambda: assign_tasks__by_department_submit_button_function(department_strvars, exclude_entry_widget.get(), task_entry.get("1.0","end-1c"), date_entry.get()))
    submit_button.grid(row=next_row+5, column=0, columnspan=2, pady=10)

    return_to_employee_codes = Button(main_menu, text="Return to Assign Tasks", command=assign_tasks_function)
    return_to_employee_codes.grid(row=next_row+6, column=0, columnspan=2, pady=10)

    return

def assign_tasks__by_department_submit_button_function(strvars, excluded_emps, single_task_string, date_string):

    if single_task_string == "" or date_string == "" or all(var.get() == "" for var in strvars):
        messagebox.showerror("Empty field(s)!", "No tasks were assigned. 'Task', 'Date', or 'Department' fields were blank.")
        return

    conn = sqlite3.connect(database_file)
    c = conn.cursor()



    employees_array = []
    excluded_emps = excluded_emps.split(",")
    date_string = date_string.split(",")
    for strvar in strvars:
        value = strvar.get()
        if value != "":
            if value == "None":
                all_matching_emp_ids = c.execute("SELECT ID FROM employees WHERE Department = '" + value + "' OR Department = '';").fetchall()
            else:
                all_matching_emp_ids = c.execute("SELECT ID FROM employees WHERE Department = '" + value + "';").fetchall()
            for matching_id in all_matching_emp_ids:
                if str(matching_id[0]) not in excluded_emps:
                    employees_array.append(str(matching_id[0]))

    replaced = ""

    for emp in employees_array:
        for single_date in date_string:
            try:
                datetime.strptime(single_date, "%m/%d/%Y")
            except ValueError:
                messagebox.showerror("Wrong Date Format!", "Format must be in (mm/dd/yyyy)")
                return
            
            today = datetime.strptime(getTodaysWeekDayAndDate()[1], "%Y-%m-%d")
            
            if datetime.strptime(single_date, "%m/%d/%Y") < today:
                messagebox.showerror("Cannot Assign Tasks on Past Dates!", "Check your dates such that each one is greater than or equal to today's date.")
                return

            old_date = single_date.split("/")
            if len(old_date[0]) < 2:
                old_date[0] = "0" + old_date[0]
            if len(old_date[1]) < 2:
                old_date[1] = "0" + old_date[1]
            single_date = "/".join(old_date)

            task_id_for_matching_emp_and_date = c.execute("SELECT task_id, task FROM employee_tasks WHERE employee_id = '" + emp + "' AND task_date = '" + single_date + "';").fetchone()
            name = c.execute(f"SELECT FirstName, LastName FROM employees WHERE ID = '{emp}';").fetchone()
            if task_id_for_matching_emp_and_date != None:
                c.execute("UPDATE employee_tasks SET task = '" + single_task_string + "' WHERE task_id = '" + str(task_id_for_matching_emp_and_date[0]) + "';")
                replaced += f"{name[0]} {name[1]}'s task, '{task_id_for_matching_emp_and_date[1]}', on {single_date} was over-written.\n\n"
            else:
                sql_statement = f"INSERT INTO employee_tasks(employee_id, task_date, task) VALUES('{emp}', '{single_date}', '{single_task_string}')"
                c.execute(sql_statement)
                replaced += f"A task for {name[0]} {name[1]} on {single_date} was added.\n\n"
    
    messagebox.showinfo("Successful!", "Your tasks have been succesfully assigned.\n\n" + replaced)

    conn.commit()
    conn.close()
    return

def assign_tasks__by_employee():
    clear_frame(main_menu)
    Label(main_menu, text="Seperate entries labeled with \"(s)\" by commas and no spaces", font=("Arial", 8), pady=10, anchor=CENTER).grid(row=0, column=0, columnspan=2, sticky="ew")

    emp_label = Label(main_menu, text="Employee ID(s): ", font=("Arial", 15), pady=10, padx=10)
    emp_label.grid(row=1, column=0, sticky="e")

    emp_id_entry = Entry(main_menu)
    emp_id_entry.grid(row=1, column=1, sticky="w")

    task_label = Label(main_menu, text="Task: ", font=("Arial", 15), pady=10, padx=10)
    task_label.grid(row=2, column=0, sticky="e")

    task_entry = Text(main_menu, width=15, height=2)
    task_entry.grid(row=2, column=1, sticky="w")

    date_label = Label(main_menu, text="Date(s) mm/dd/yyyy: ", font=("Arial", 15), pady=10, padx=10)
    date_label.grid(row=3, column=0, sticky="e")

    date_entry = Entry(main_menu)
    date_entry.grid(row=3, column=1, sticky="w")

    submit_button = Button(main_menu, text="Assign Tasks", command=lambda: assign_tasks__by_employee_submit_button(emp_id_entry.get(), task_entry.get("1.0","end-1c"), date_entry.get()))
    submit_button.grid(row=4, column=0, columnspan=2, pady=10)

    return_to_employee_codes = Button(main_menu, text="Return to Assign Tasks", command=assign_tasks_function)
    return_to_employee_codes.grid(row=5, column=0, columnspan=2, pady=10)
    return

def assign_tasks__by_employee_submit_button(id_string, task, date_string):
    if task == "" or date_string == "" or id_string == "":
        messagebox.showerror("Empty field(s)!", "No tasks were assigned. 'Task', 'Date', or 'Department' fields were blank.")
        return

    conn = sqlite3.connect(database_file)
    c = conn.cursor()

    date_array = date_string.split(",")
    id_array = id_string.split(",")

    all_ids = c.execute("SELECT ID FROM employees;").fetchall()
    
    print(all_ids)
    for single_id in id_array:
        print(single_id)
        if str(single_id) in all_ids:
            print("Exists")
        else:
            print("DNE")


    conn.commit()
    conn.close()
    return

def get_period_days(num):
    today = datetime.today()
    day = ""
    additional_months = 0
    if 0 < today.day < 16:
        if num >= 0:
            additional_months = int(num / 2)
        elif num / 2 != int(num / 2):
            additional_months = int(num / 2 - 1)
        else:
            additional_months = int(num / 2)

        if num % 2 == 0:
            day = "01"
        else:
            day = "16"
    else:
        if num >= 0:
            additional_months = int((num + 1) / 2)
        elif num / 2 != int(num / 2):
            additional_months = int((num + 1) / 2 - 1)
        else:
            additional_months = int((num + 1) / 2)

        if num % 2 == 0:
            day = "16"
        else:
            day = "01"

    temporary_date = datetime.strptime((today + relativedelta(months=additional_months)).strftime("%m/%d/%Y"), "%m/%d/%Y").strftime("%m/%d/%Y")
    beginning_of_period = temporary_date[:3] + day + temporary_date[5:]

    end_of_period = datetime.strptime(beginning_of_period, "%m/%d/%Y")
    while not is_this_a_pay_day(end_of_period.strftime("%m/%d/%Y"), "%m/%d/%Y"):
        end_of_period += timedelta(days=1)

    last_day_of_calculated_period_days = 0
    if day == "16":
        # mm/dd/yy
        last_day_of_calculated_period_days = str(monthrange(int(beginning_of_period[6:]), int(beginning_of_period[:2]))[1])
    else:
        last_day_of_calculated_period_days = "15"

    # (displayed_period_boundaries, calculated_pay_days_from_1_to_15)
    
    return ((datetime.strptime(beginning_of_period, "%m/%d/%Y").strftime("%m/%d/%y") , end_of_period.strftime("%m/%d/%y")), tuple(getArrayOfDates(beginning_of_period, end_of_period.strftime("%m/%d/%Y")[:3] + last_day_of_calculated_period_days + end_of_period.strftime("%m/%d/%Y")[5:], "%m/%d/%Y", "%m/%d/%y")))

def next_previous_period(num):
    global period_count
    period_count += num
    return display_period_totals(period_count)

def display_period_totals(num):
    conn = sqlite3.connect(database_file)
    c = conn.cursor()

    displayed_period_range, period_days = get_period_days(num)

    Label(main_menu, text=displayed_period_range[0] + " - " + displayed_period_range[1], font=("Arial", 10), pady=10).grid(row=1, column=5)

    global next_period
    if num == 0:
        next_period.config(state=DISABLED)
    else:
        next_period.config(state=NORMAL)

    # label_1 = Label(main_menu, text="", font=("Arial", 10), pady=10)
    # label_1.grid(row=2, column=0)

    # label_2 = Label(main_menu, text="", font=("Arial", 10), pady=10)
    # label_2.grid(row=2, column=1)

    all_ids = c.execute("SELECT ID, FirstName, LastName FROM employees;").fetchall()

    # id_column = "ID\n---------------\n"
    # flast_column = "FLast\n---------------\n"

    # regular_hours = "RegHours\n---------------\n"
    # regular_pay = "RegPay\n---------------\n"
    # overtime_hours = "OvertimeHours\n---------------\n"
    # overtime_pay = "OvertimePay\n---------------\n"
    # double_time_hours = "DoubleTimeHours\n---------------\n"
    # double_time_pay = "DoubleTimePay\n---------------\n"
    # total_hours = "TotalHours\n---------------\n"
    # total_pay = "TotalPay\n---------------\n"

    label_headers = ["ID\n---------------\n",
                     "FLast\n---------------\n",
                     "TotalPay\n---------------\n",
                     "TotalHours\n---------------\n",
                     "RegHours\n---------------\n",
                     "OvertimeHours\n---------------\n",
                     "DoubleTimeHours\n---------------\n",
                     "RegPay\n---------------\n",
                     "OvertimePay\n---------------\n",
                     "DoubleTimePay\n---------------\n"
                     ]

    label_dictionary = {
        "Total Pay": [],
        "Total Hours": [],
        "Regular Hours": [],
        "Overtime Hours": [],
        "Double Time Hours": [],
        "Regular Pay": [],
        "Overtime Pay": [],
        "Double Time Pay": []
    }

    another_two_fields = {
        "ID": [],
        "FLast": []
    }

    for record in all_ids:
        id = record[0]
        fname = record[1]
        lname = record[2]

        another_two_fields["ID"].append(str(id))
        another_two_fields["FLast"].append(fname[0] + lname)
        
        dictionary_info = calculate_employee_pay(period_days[0], period_days[-1], "%m/%d/%y", str(id))
        for key, value in dictionary_info.items():
            label_dictionary[key].append(str(value))
            

    # label_1.config(text=id_column)
    # label_2.config(text=flast_column)
     
    label_dictionary = {**another_two_fields, **label_dictionary}


    for counter, value, header in zip(range(len(label_dictionary)), label_dictionary.values(), label_headers):
        text = header + "\n"
        for elem in value:
            text += elem + "\n"
        Label(main_menu, text=text, font=("Arial", 10), pady=10, padx=10).grid(row=2, column=counter)

    return_to_main_menu = Button(main_menu, text="Return to Main Menu", command=main_menu_function)
    return_to_main_menu.grid(row=3, column=5, pady=10)

    
    file_name = "Employee_Period_Totals_" + datetime.strptime(displayed_period_range[1], "%m/%d/%y").strftime("%m%d%y")
    create_file = Button(main_menu, text="Create Excel Report From Data", font=("Arial", 10), pady=10, command=lambda: create_excel_file_with_table(file_name, label_dictionary))
    create_file.grid(row=1, column=9)

    

    conn.commit()
    conn.close()
    return

def create_excel_file_with_table(file_name, dictionary):
    """
    file_name is the name of the Excel file without the extension.

    The labels of the passed in dictionary will become the columns of the Excel table.
    Expects that the values in the dictionary are lists. All values must have equally sized lists.
    """
    dict_values_to_list = []
    for value in dictionary.values():
        dict_values_to_list.append(value)
    
    data = []
    for i in range(len(dict_values_to_list[0])):
        sub_array = []
        for j in range(len(dict_values_to_list)):
            sub_array.append(dict_values_to_list[j][i])
        data.append(sub_array)

    columns = []
    for label in dictionary.keys():
        columns.append({"header": label})

    files = [("Excel File", "*.xlsx")]

    file_name = asksaveasfilename(filetypes=files, defaultextension=files, initialfile=file_name)
    try:
        file_name = file_name[(every_index(file_name, "/")[-1] + 1):]
        workbook = xl.Workbook(file_name)
        sheet = workbook.add_worksheet()

        abc = ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z")

        sheet.add_table("A1:" + abc[len(columns) - 1] + str(len(data) + 1), {"data": data, "columns": columns})

        workbook.close()

        messagebox.showinfo("Successful", file_name + " has been saved!")
    except TypeError:
        pass

def every_index(string, char):
    result_list = []
    for index, letter in enumerate(string):
        if letter == char:
            result_list.append(index)

    return result_list

def period_totals_function():
    conn = sqlite3.connect(database_file)
    c = conn.cursor()

    clear_frame(main_menu)
    main_menu.config(text="Period Totals")

    # Label(main_menu, text=)
    # getPeriodFromDateString()

    global period_count
    period_count = 0

    global next_period
    next_period = Button(main_menu, text="Next", font=("Arial", 10), pady=10, command=lambda: next_previous_period(1))
    next_period.grid(row=1, column=6)

    previous_period = Button(main_menu, text="Previous", font=("Arial", 10), pady=10, command=lambda: next_previous_period(-1))
    previous_period.grid(row=1, column=4)
    
    next_period.config(state=DISABLED)

    display_period_totals(0)

    

    return

def historical_totals_function():
    return



def employee_codes__add_new_employee_function():
    clear_frame(main_menu)
    main_menu.config(text="Add New Employee")

    padding = 3

    id_label = Label(main_menu, text="ID: ", font=("Arial", 15), pady=5)
    id_label.grid(row=0, column=0, sticky=E)

    employee_codes__add_new_employee_id = Entry(main_menu, width=25)
    employee_codes__add_new_employee_id.grid(row=0, column=1)

    f_name_label = Label(main_menu, text="First Name: ", font=("Arial", 15), pady=padding)
    f_name_label.grid(row=1, column=0, sticky=E)

    employee_codes__add_new_employee_first_name = Entry(main_menu, width=25)
    employee_codes__add_new_employee_first_name.grid(row=1, column=1)

    l_name_label = Label(main_menu, text="Last Name: ", font=("Arial", 15), pady=padding)
    l_name_label.grid(row=2, column=0, sticky=E)

    employee_codes__add_new_employee_last_name = Entry(main_menu, width=25)
    employee_codes__add_new_employee_last_name.grid(row=2, column=1)

    department_label = Label(main_menu, text="Department: ", font=("Arial", 15), pady=padding)
    department_label.grid(row=3, column=0, sticky=NE)

    employee_codes__add_new_employee_department = Listbox(main_menu, height=4, width=25)
    employee_codes__add_new_employee_department.insert(1, "MG")
    employee_codes__add_new_employee_department.insert(2, "MK")
    employee_codes__add_new_employee_department.insert(3, "PD")
    employee_codes__add_new_employee_department.insert(4, "CL")
    employee_codes__add_new_employee_department.grid(row=3, column=1, sticky=W, pady=padding)

    hourly_pay_label = Label(main_menu, text="Hourly Pay: ", font=("Arial", 15), pady=padding)
    hourly_pay_label.grid(row=4, column=0, sticky=E)

    hourly_pay_entry_widget = Entry(main_menu, width=25)
    hourly_pay_entry_widget.grid(row=4, column=1, pady=padding)

    ot_allowed_label = Label(main_menu, text="OT Allowed: ", font=("Arial", 15), pady=padding)
    ot_allowed_label.grid(row=5, column=0, sticky=E)

    ot_allowed_listbox = Listbox(main_menu, height=2, width=25)
    ot_allowed_listbox.insert(1, "Yes")
    ot_allowed_listbox.insert(2, "No")
    ot_allowed_listbox.grid(row=5, column=1, sticky=W, pady=padding)

    max_daily_hours_label = Label(main_menu, text="Max Daily Hours: ", font=("Arial", 15), pady=padding)
    max_daily_hours_label.grid(row=6, column=0, sticky=E)

    max_daily_hours_entry = Entry(main_menu, width=25)
    max_daily_hours_entry.grid(row=6, column=1, pady=padding)

    add_to_database = Button(main_menu, text="Add Employee", command=lambda: add_new_employee(employee_codes__add_new_employee_id.get(), employee_codes__add_new_employee_first_name.get(), employee_codes__add_new_employee_last_name.get(), employee_codes__add_new_employee_department.get(ANCHOR), hourly_pay_entry_widget.get(), ot_allowed_listbox.get(ANCHOR), max_daily_hours_entry.get()))
    add_to_database.grid(row=7, column=0, columnspan=2, pady=padding)

    root.bind("<Return>", lambda event=None: add_to_database.invoke())

    return_to_employee_codes = Button(main_menu, text="Return to Employee Codes", command=employee_codes_function)
    return_to_employee_codes.grid(row=8, column=0, columnspan=2, pady=padding)
    
    return

def add_new_employee(id, first, last, department, hourly_pay, ot_allowed, max_daily_hours):
    conn = sqlite3.connect(database_file)
    c = conn.cursor()
    if id == "" or first == "" or last == "" or department == "" or hourly_pay == "" or ot_allowed == "" or max_daily_hours == "":
        messagebox.showerror("Empty Field", "Missing 'Id', 'First Name', 'Last Name', 'Department', 'Hourly Pay', 'OT Allowed', or 'Max Daily Hours'")
        #label_widget.config(text="Missing 'Id', 'First Name', 'Last Name', 'Department', 'Hourly Pay', 'OT Allowed', or 'Max Daily Hours'")
        return
    else:
        try:
            float(hourly_pay)
            float(max_daily_hours)
        except ValueError:
            messagebox.showerror("Invalid Field", "'Hourly Pay' and 'Max Daily Hours' must be numbers!")
            #label_widget.config(text="'Hourly Pay' and 'Max Daily Hours' must be numbers!")
            return

    result = ""
    try:
        c.execute(f"INSERT INTO employees(ID, FirstName, LastName, Department, HourlyPay, OTAllowed, MaxDailyHours) VALUES('{id}', '{first}', '{last}', '{department}', '{hourly_pay}', '{ot_allowed}', '{max_daily_hours}');")

    except sqlite3.IntegrityError:
        result = "ID already exists"
    else:
        result = "'" + first + " " + last + "' successfully added!"
    conn.commit()
    conn.close()
    messagebox.showinfo("Successful!", result)
    #label_widget.config(text=result)

def employee_codes__edit_function():
    clear_frame(main_menu)
    main_menu.config(text="Edit")

    id_label_widget = Label(main_menu, text="Enter Employee ID to Edit", font=("Arial", 15), pady=10)
    id_label_widget.grid(row=0, column=0, columnspan=2)

    id_entry_widget = Entry(main_menu, width=25)
    id_entry_widget.grid(row=1, column=0, columnspan=2, pady=10)

    #error_message = Label(main_menu, text="", font=("Arial", 15), pady=10)
    #confirmation_message = Label(main_menu, text="", font=("Arial", 15), pady=10)
    #confirmation_message.grid(row=11, column=0, columnspan=2)

    edit_button = Button(main_menu, text="Edit", command=lambda: employee_codes__edit__edit_button(id_entry_widget.get(), return_to_employee_codes))
    edit_button.grid(row=3, column=0, columnspan=2)

    root.bind("<Return>", lambda event=None: edit_button.invoke())

    return_to_employee_codes = Button(main_menu, text="Return to Employee Codes", command=employee_codes_function)
    return_to_employee_codes.grid(row=4, column=0, columnspan=2, pady=10)

    return

def employee_codes__edit__edit_button(id, return_button):
    return_button.grid_forget()
    #confirmation_message.config(text="")
    

    conn = sqlite3.connect(database_file)
    c = conn.cursor()

    try:
        emp_info = c.execute(f"SELECT * FROM employees WHERE ID = @0;", (id,)).fetchone()
    except Exception as e:
        #error_message.destroy()
        return_button.grid(row=10, column=0, columnspan=2, pady=10)
        messagebox.showerror("Error", str(e))
        #confirmation_message.config(text="Error: " + str(e))
        #confirmation_message.grid(row=11, column=0, columnspan=2)
        conn.commit()
        conn.close()
        return

    padding = 1
    id_label_widget = Label(main_menu, text="ID: ", font=("Arial", 15), pady=padding)
    id_entry_widget = Entry(main_menu, width=18)
    first_name_label_widget = Label(main_menu, text="First: ", font=("Arial", 15), pady=padding)
    first_name_entry_widget = Entry(main_menu, width=18)
    last_name_label_widget = Label(main_menu, text="Last: ", font=("Arial", 15), pady=padding)
    last_name_entry_widget = Entry(main_menu, width=18)
    deparment_label_widget = Label(main_menu, text="Department ('MG', 'MK', 'PD', 'CL'): ", font=("Arial", 15), pady=padding)
    department_entry_widget = Entry(main_menu, width=18)
    hourly_pay_label_widget = Label(main_menu, text="Hourly Pay: ", font=("Arial", 15), pady=padding)
    hourly_pay_entry_widget = Entry(main_menu, width=18)
    ot_allowed_label_widget = Label(main_menu, text="OT Allowed ('Yes', 'No'): ", font=("Arial", 15), pady=padding)
    ot_allowed_entry_widget = Entry(main_menu, width=18)
    max_daily_hours_label_widget = Label(main_menu, text="Max Daily Hours: ", font=("Arial", 15), pady=padding)
    max_daily_hours_entry_widget = Entry(main_menu, width=18)
    commit_changes = Button(main_menu, text="Commit Changes")
    
    #error_message = Label(main_menu, font=("Arial", 15), pady=10)
    #confirmation_message = Label(main_menu, text="", font=("Arial", 15), pady=10)
    #confirmation_message.grid(row=11, column=0, columnspan=2)


    if emp_info is not None:
        #error_message.grid_forget()
        #error_message.destroy()
        #confirmation_message.destroy()
        #confirmation_message.config(text="")
        
        #confirmation_message.destroy()
        #clear([error_message, id_label_widget, first_name_label_widget, last_name_label_widget, deparment_label_widget], [commit_changes], False, [])

        id_label_widget.grid(row=4, column=0, sticky=E)

        id_entry_widget.grid(row=4, column=1, sticky=W)
        id_entry_widget.insert(END, str(emp_info[0]))

        first_name_label_widget.grid(row=5, column=0, sticky=E)

        first_name_entry_widget.grid(row=5, column=1, sticky=W)
        first_name_entry_widget.insert(END, emp_info[1])

        last_name_label_widget.grid(row=6, column=0, sticky=E)

        last_name_entry_widget.grid(row=6, column=1, sticky=W)
        last_name_entry_widget.insert(END, emp_info[2])

        deparment_label_widget.grid(row=7, column=0, sticky=NE)

        department_options = ["MG", "MK", "PD", "CL"]

        department_entry_widget.grid(row=7, column=1, sticky=W, pady=padding)
        department_entry_widget.insert(END, emp_info[3])

        #department_listbox_widget.event_generate("<<ListboxSelect>>")

        hourly_pay_label_widget.grid(row=8, column=0, sticky=NE)

        hourly_pay_entry_widget.grid(row=8, column=1, sticky=W)
        hourly_pay_entry_widget.insert(END, emp_info[4])

        ot_allowed_label_widget.grid(row=9, column=0, sticky=NE)
        ot_allowed_entry_widget.grid(row=9, column=1, sticky=W, pady=padding)
        ot_allowed_entry_widget.insert(END, emp_info[5])

        max_daily_hours_label_widget.grid(row=10, column=0, sticky=NE)

        max_daily_hours_entry_widget.grid(row=10, column=1, sticky=W)
        max_daily_hours_entry_widget.insert(END, emp_info[6])





        
        #confirmation_message.grid(row=11, column=0, columnspan=2)

        #department_listbox_widget.curselection()
        #                                                                                       old_id, new_id,             new_first,                      new_last,                   new_department,                 new_hourly_pay,                 new_ot_allowed,                 new_max_daily_hours
        commit_changes.config(command=lambda: employee_codes__edit__edit_button__commit_changes(id, id_entry_widget.get(), first_name_entry_widget.get(), last_name_entry_widget.get(), department_entry_widget.get(), hourly_pay_entry_widget.get(), ot_allowed_entry_widget.get(), max_daily_hours_entry_widget.get()))
        commit_changes.grid(row=11, column=0, columnspan=2, pady=padding)

        root.bind("<Return>", lambda event=None: commit_changes.invoke())

        return_button.grid(row=12, column=0, columnspan=2, pady=padding)
        
    else:
        clear_frame(main_menu)

        main_menu.config(text="Edit")

        id_label_widget = Label(main_menu, text="Enter Employee ID to Edit", font=("Arial", 15), pady=10)
        id_label_widget.grid(row=0, column=0, columnspan=2)

        id_entry_widget = Entry(main_menu, width=25)
        id_entry_widget.grid(row=1, column=0, columnspan=2, pady=10)

        edit_button = Button(main_menu, text="Edit", command=lambda: employee_codes__edit__edit_button(id_entry_widget.get(), return_to_employee_codes))
        edit_button.grid(row=2, column=0, columnspan=2)

        return_to_employee_codes = Button(main_menu, text="Return to Employee Codes", command=employee_codes_function)
        return_to_employee_codes.grid(row=3, column=0, columnspan=2, pady=10)

        messagebox.showerror("Invalid ID", f"ID \"{id}\" does not exist. Please try again.")
        # error_message = Label(main_menu, text="ID '" + id + "' Does Not Exist", font=("Arial", 15), pady=10)
        # error_message.grid(row=4, column=0, columnspan=2)

        #confirmation_message = Label(main_menu, text="", font=("Arial", 15), pady=10)
        #confirmation_message.grid(row=11, column=0, columnspan=2)

        

        root.bind("<Return>", lambda event=None: edit_button.invoke())

        
        
        conn.commit()
        conn.close()
        return
    
    

    conn.commit()
    conn.close()
    return

def employee_codes__edit__edit_button__commit_changes(old_id, new_id, new_first, new_last, new_department, new_hourly_pay, new_ot_allowed, new_max_daily_hours):
    conn = sqlite3.connect(database_file)
    c = conn.cursor()

    hour = time.strftime("%I")
    minute = time.strftime("%M")
    second = time.strftime("%S")
    am_pm = time.strftime("%p")

    current_time = hour + ":" + minute + ":" + second + " " + am_pm

    emp_info = c.execute("SELECT * FROM employees WHERE ID = '" + old_id + "';").fetchone()

    # if new_id == "" or new_first == "" or new_last == "" or new_hourly_pay == "":
    #     confirmation_message.config(text="Missing 'Id', 'First Name', 'Last Name', or 'Hourly Pay'")
    #     confirmation_message.grid(row=11, column=0, columnspan=2)
    #     return
    # else:
    #     try:
    #         float(new_hourly_pay)
    #     except ValueError:
    #         confirmation_message.config(text="'Hourly Pay' must be a number")
    #         confirmation_message.grid(row=11, column=0, columnspan=2)
    #         return

    try:
        
        
        departments = ["MG", "MK", "PD", "CL"]
        ot_responses = ["Yes", "No"]
        
        if new_id == "" or new_first == "" or new_last == "" or (new_department not in departments) or new_hourly_pay == "" or (new_ot_allowed not in ot_responses) or new_max_daily_hours == "":
            messagebox.showerror("Empty Field", "Missing 'Id', 'First Name', 'Last Name', valid 'Department', 'Hourly Pay', valid 'OT Allowed', or 'Max Daily Hours'")
            #confirmation_message.config(text="Missing 'Id', 'First Name', 'Last Name', valid 'Department', 'Hourly Pay', valid 'OT Allowed', or 'Max Daily Hours'")
            #confirmation_message.grid(row=13, column=0, columnspan=2)
            return
        else:
            try:
                float(new_hourly_pay)
                float(new_max_daily_hours)
            except ValueError:
                messagebox.showerror("Invalid Entry", "'Hourly Pay' and 'Max Daily Hours' must both be numbers")
                # confirmation_message.config(text="'Hourly Pay' and 'Max Daily Hours' must both be numbers")
                # confirmation_message.grid(row=13, column=0, columnspan=2)
                return

        edited_info = ""
        # "s" = string, "f" = float, "m" = $float
        types =    ["s", "s", "s", "s", "m", "s", "f"]
        #old_info = [emp_info[0], emp_info[1], emp_info[2], emp_info[3], emp_info[4], emp_info[5], emp_info[6]]
        displayed_labels_for_changes = ["ID", "First Name", "Last Name", "Department", "Hourly Pay", "OT Allowed", "Max Daily Hours"]
        new_info = [new_id, new_first, new_last, new_department, new_hourly_pay, new_ot_allowed, new_max_daily_hours]

        for type, label, old, new in zip(types, displayed_labels_for_changes, emp_info, new_info):
            if type == "s":
                if str(old) != str(new):
                    edited_info += label + ": '" + str(old) + "' => '" + str(new) + "'\n"
            elif type == "f":
                if float(old) != float(new):
                    edited_info += label + ": '" + str(float(old)) + "' => '" + str(float(new)) + "'\n"
            elif type == "m":
                if float(old) != float(new):
                    edited_info += label + ": '$" + str(float(old)) + "' => '$" + str(float(new)) + "'\n"

        if edited_info == "":
            messagebox.showinfo("No Changes", "No modifications were made. All information already matched.")
            #confirmation_message.config(text="No modifications made")
        else:
            employees_table_update = f"UPDATE employees SET ID = '{new_id}', FirstName = '{new_first}', LastName = '{new_last}', Department = '{new_department}', HourlyPay = '{new_hourly_pay}', OTAllowed = '{new_ot_allowed}', MaxDailyHours = '{new_max_daily_hours}' WHERE ID = '{old_id}';"
            time_clock_entries_table_update = f"UPDATE time_clock_entries SET empID = '{new_id}' WHERE empID = '{old_id}';"
            employee_tasks_table_update = f"UPDATE employee_tasks SET employee_id = '{new_id}' WHERE employee_id = '{old_id}';"
            updated_table_query_array = [employees_table_update, time_clock_entries_table_update, employee_tasks_table_update]
            for updated_table_query in updated_table_query_array:
                c.execute(updated_table_query)
            conn.commit()
            conn.close()
            messagebox.showinfo("Successful", old_id + "' was edited at " + current_time + "!\n" + edited_info)
            #confirmation_message.config(text="Successful! '" + old_id + "' was edited at " + current_time + "!\n" + edited_info)

    except Exception as e:
        if str(e) == "'NoneType' object is not iterable":
            messagebox.showerror("Invalid ID", f"ID '{old_id}' could not be found. You may have changed it.")
            #confirmation_message.config(text=f"ID '{old_id}' could not be found. You may have changed it.")
        else:
            messagebox.showerror("Unknown Error", "Unsuccessful. " + old_id + " was not edited at " + current_time + " due to the following error: " + str(e))
            #confirmation_message.config(text="Unsuccessful. " + old_id + " was not edited at " + current_time + " due to the following error: " + str(e))
        #confirmation_message.grid(row=11, column=0, columnspan=2)
    #else:
        # edited_info = ""
        # new_info = [new_id, new_first, new_last, new_department, new_hourly_pay]

        # for old, new in zip(emp_info, new_info):
        #     if str(old) != str(new):
        #         edited_info += "'" + str(old) + "' => '" + str(new) + "'\n"

        # if edited_info == "":
        #     confirmation_message.config(text="No modifications made")
        # else:
        #     confirmation_message.config(text="Successful! '" + old_id + "' was edited at " + current_time + "!\n" + edited_info)
        #confirmation_message.grid(row=11, column=0, columnspan=2)
    #confirmation_message.grid(row=13, column=0, columnspan=2)

    
    return

def employee_codes__delete_function():

    #global_confirmation_text

    clear_frame(main_menu)
    main_menu.config(text="Delete")

    id_label_widget = Label(main_menu, text="Enter Employee Id to Delete", font=("Arial", 15), pady=10)
    id_label_widget.grid(row=0, column=0, columnspan=2)

    id_entry_widget = Entry(main_menu, width=25)
    id_entry_widget.grid(row=1, column=0, columnspan=2, pady=10)

    delete_button = Button(main_menu, text="Delete", command=lambda: employee_codes__delete_function__delete_button(id_entry_widget.get()))
    delete_button.grid(row=2, column=0, columnspan=2, pady=10)

    root.bind("<Return>", lambda event=None: delete_button.invoke())

    return_to_employee_codes = Button(main_menu, text="Return to Employee Codes", command=employee_codes_function)
    return_to_employee_codes.grid(row=3, column=0, columnspan=2, pady=10)
    return


def employee_codes__delete_function__delete_button(id):
    conn = sqlite3.connect(database_file)
    c = conn.cursor()

    # global global_confirmation_text
    name = c.execute("SELECT FirstName, LastName FROM employees WHERE ID = '" + id + "';").fetchone()
    try:
        if name == None:
            messagebox.showerror("Invalid ID", f"An employee with the id of \"{id}\" does not exist. Please try again.")
            #global_confirmation_text.set("'" + id + "' Does Not Exist.")
            conn.commit()
            conn.close()
            return
        response = messagebox.askyesno("Warning!", f"Are you sure you'd like to delete the employee, \"{name[0]} {name[1]}\", and all his/her data? This action is irreversible.")
        if response:
            c.execute("DELETE FROM employees WHERE ID = '" + id + "';")
            c.execute("DELETE FROM time_clock_entries WHERE empID = '" + id + "';")
            c.execute("DELETE FROM employee_tasks WHERE employee_id = '" + id + "';")
        else:
            conn.commit()
            conn.close()
            return
    except Exception as e:
        messagebox.showerror("Unknown Error", "Error:\n" + str(e))
        # global_confirmation_text.set("Error: " + str(e))
    else:
        messagebox.showinfo("Successful!", f"\"{id}\" ({name[0]} {name[1]}) has been successfully deleted.")
        # global_confirmation_text.set("'" + id + "' has been successfully deleted!")

    conn.commit()
    conn.close()
    return

def employee_codes__view_function():
    fill_frame(main_menu, [["View Employees", employee_codes__view_function__view_employees], ["View Timeclock Entries", employee_codes__view_function__view_timeclock_entries]], "View", ["Employee Codes", employee_codes_function])
    # return_to_main_menu = Button(main_menu, text="Return to Employee Codes", command=employee_codes_function)
    # return_to_main_menu.grid(row=num_of_menu_items, column=0, columnspan=2, pady=10)
    return


def employee_codes__view_function__view_employees():
    conn = sqlite3.connect(database_file)
    c = conn.cursor()

    main_menu.config(text="View Employees")

    clear_frame(main_menu)

    id_label = Label(main_menu, text="")
    first_name_label = Label(main_menu, text="")
    last_name_label = Label(main_menu, text="")
    department_label = Label(main_menu, text="")
    hourly_pay_label = Label(main_menu, text="")
    ot_allowed_label = Label(main_menu, text="")
    max_daily_hours_label = Label(main_menu, text="")
    master_label_array = [id_label, first_name_label, last_name_label, department_label, hourly_pay_label, ot_allowed_label, max_daily_hours_label]

    id = "ID\n-------------\n\n"
    first_name = "First Name\n-------------\n\n"
    last_name = "Last Name\n-------------\n\n"
    department = "Department\n-------------\n\n"
    hourly_pay = "Hourly Pay\n-------------\n\n"
    ot_allowed = "OT Allowed\n-------------\n\n"
    max_daily_hours = "Max Daily Hours\n-------------\n\n"
    master_field_array = [id, first_name, last_name, department, hourly_pay, ot_allowed, max_daily_hours]

    data = c.execute("SELECT * FROM employees").fetchall()

    for record in data:
        for item, db_fields_counter in zip(record, range(len(record))):
            master_field_array[db_fields_counter] += str(item) + "\n"

    #print(master_field_array)
    next_column = 0
    for label, field, column_counter in zip(master_label_array, master_field_array, range(len(master_label_array))):
        label.config(text=field)
        label.grid(row=0, column=column_counter)
        if column_counter == len(master_label_array) - 1:
            next_column = column_counter + 1

    return_button = Button(main_menu, text="Return to View", command=employee_codes__view_function)
    return_button.grid(row=1, column=3)

    root.bind("<Return>", lambda event=None: button.invoke())



    conn.commit()
    conn.close()
    return

def employee_codes__view_function__view_timeclock_entries():
    conn = sqlite3.connect(database_file)
    c = conn.cursor()

    main_menu.config(text="View Timeclock Entries", width=1000)

    clear_frame(main_menu)

    data = c.execute("SELECT empID, ClockIn, ClockOut, Request FROM time_clock_entries ORDER BY empID").fetchall()

    main_frame = Frame(main_menu)
    main_frame.pack(fill=BOTH, expand=1)

    canvas = Canvas(main_frame)
    canvas.pack(side=LEFT, fill=BOTH, expand=1)
    
    scrollbar = ttk.Scrollbar(main_frame, orient=VERTICAL, command=canvas.yview)
    scrollbar.pack(side=LEFT, fill=Y)

    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    second_frame = Frame(canvas)

    canvas.create_window((0,0), window=second_frame, anchor="nw")

    #row_label = Label(second_frame, text="")
    emp_id_label = Label(second_frame, text="")
    clock_in_label = Label(second_frame, text="")
    clock_out_label = Label(second_frame, text="")
    requests_label = Label(second_frame, text="")
    master_label_array = [emp_id_label, clock_in_label, clock_out_label, requests_label]

    #row = "Row\n-------------\n\n"
    id = "ID\n-------------\n\n"
    clock_in = "Clock In\n-------------\n\n"
    clock_out = "Clock Out\n-------------\n\n"
    request = "Request\n-------------\n\n"
    master_field_array = [id, clock_in, clock_out, request]

    for record, r in zip(data, range(len(data))):
        #master_field_array[0] += str(r+1) + "\n\n"
        for item, db_fields_counter in zip(record, range(len(record))):
            if db_fields_counter == 1 and item != "FORGOT" and item is not None:
                master_field_array[db_fields_counter] += datetime.strptime(item, "%Y-%m-%d %H:%M:%S").strftime("%m/%d/%y %I:%M:%S %p") + "\n\n"
            elif db_fields_counter == 2 and item != "FORGOT" and item is not None:
                master_field_array[db_fields_counter] += datetime.strptime(item, "%Y-%m-%d %H:%M:%S").strftime("%I:%M:%S %p") + "\n\n"
            elif db_fields_counter == 3:
                if item is None:
                    master_field_array[db_fields_counter] += "\n\n"
                else:
                    master_field_array[db_fields_counter] += datetime.strptime(item[11:], "%H:%M:%S").strftime("%I:%M:%S %p") + "\n\n"
            else:
                master_field_array[db_fields_counter] += str(item) + "\n\n"
    
    for label, field, column_counter in zip(master_label_array, master_field_array, range(len(master_label_array))):
        label.config(text=field)
        label.grid(row=0, column=column_counter)

    return_button = Button(second_frame, text="Return to View", command=employee_codes__view_function)
    return_button.grid(row=1, column=1, columnspan=2)

    root.bind("<Return>", lambda event=None: button.invoke())

    conn.commit()
    conn.close()
    return





















def selectTask(emp_id, task_date, format):
    conn = sqlite3.connect(database_file)
    c = conn.cursor()
    task = c.execute("SELECT task FROM employee_tasks WHERE employee_id = '" + emp_id + "' AND task_date = '" + str(datetime.strptime(task_date, format).strftime("%m/%d/%Y")) + "';").fetchone()
    conn.commit()
    conn.close()
    if task != None:
        return task[0]
    else:
        return "You don't have any tasks!"

def getPeriodDays():
    result_str = []
    current_date = time.strftime("%x")
    day = int(current_date[3:5])
    month = current_date[0:2]
    year = current_date[6:8]
    num_of_days_in_month = monthrange(datetime.now().year, int(month))[1]
    #mm/dd/yy
    if day >= 1 and day < 16:
        for i in range(1, day+1):
            if i < 10:
                result_str.append(month + "/0" + str(i) + "/" + year)
            else:
                result_str.append(month + "/" + str(i) + "/" + year)
    else:
        for i in range(16, day+1):
            result_str.append(month + "/" + str(i) + "/" + year)
    return result_str

def getPeriodFromDateString(date_string, format):
    result_array_of_str_dates = []
    date = str(datetime.strptime(date_string, format).strftime("%m/%d/%y"))
    day = int(date[3:5])
    month = date[0:2]
    year = date[6:8]
    if day >= 1 and day < 16:
        for i in range(1, day+1):
            if i < 10:
                result_array_of_str_dates.append(month + "/0" + str(i) + "/" + year)
            else:
                result_array_of_str_dates.append(month + "/" + str(i) + "/" + year)
    else:
        for i in range(16, day+1):
            result_array_of_str_dates.append(month + "/" + str(i) + "/" + year)
    return result_array_of_str_dates


# %Y means 2021, %y means 21



#Fix later
# def getAllEmployeeHours(start, end, entered_format, result_format):

#     employee_hours_button.config(command=lambda: clear([employee_list_label, employee_hours_label], [], False, [[employee_hours_button, getAllEmployeeHours]]))

#     conn = sqlite3.connect(database_file)
#     c = conn.cursor()
    

#     employees_table = c.execute("SELECT * FROM employees;").fetchall()

#     conn.commit()
#     conn.close()

#     array_of_dates = getArrayOfDates(start, end, entered_format, result_format)

#     employee_list_string = "Employee\n---------------\n"
#     employee_hours_string = "Hours\n---------------\n"
#     for record in employees_table:
#         id = record[0]
#         employee_list_string += record[1] + " " + record[2] + "\n\n"  
#         for single_date in array_of_dates:
#             employee_hours_string += str(getTotalEmployeeHours(single_date, result_format, str(id))) + "\n\n"
                            
#     employee_list_label.config(text=employee_list_string)
#     employee_hours_label.config(text=employee_hours_string)
    

    
        
def getRawTotalEmployeeHours(entered_date, format, id):
    #Other commented version: getRawTotalEmployeeHours(start, end, id):
    conn = sqlite3.connect(database_file)
    c = conn.cursor()

    time_in_out_records = c.execute("SELECT ClockIn, ClockOut FROM time_clock_entries WHERE empID = '" + id + "' AND ClockIn LIKE '%" + str(datetime.strptime(entered_date, format).strftime("%Y-%m-%d")) + "%';").fetchall()

    total_seconds = 0
    for record in time_in_out_records:
        t1 = datetime.strptime(str(datetime.now()), "%Y-%m-%d %H:%M:%S.%f").timestamp()
        t0 = datetime.strptime(record[0], "%Y-%m-%d %H:%M:%S").timestamp()        
        if record[1] is not None:
            if record[1] == "FORGOT":
                #t1 = t0
                continue
            else:
                t1 = datetime.strptime(record[1], "%Y-%m-%d %H:%M:%S").timestamp()
        total_seconds += t1 - t0
    employee_hours = round(total_seconds / 3600, 3)
    conn.close()
    return employee_hours


def getTotalDailyHoursAccountingForBreaks(entered_date, format, id):

    conn = sqlite3.connect(database_file)
    c = conn.cursor()

    total_period_hours = getRawTotalEmployeeHours(entered_date, format, id)

    time_in_out_records = c.execute("SELECT ClockIn, ClockOut FROM time_clock_entries WHERE empID = '" + id + "' AND ClockIn LIKE '%" + str(datetime.strptime(entered_date, format).strftime("%Y-%m-%d")) + "%';").fetchall()

    # (ClockIn, ClockOut)
    # (ClockIn, ClockOut)
    # (ClockIn, ClockOut)
    # (ClockIn, ClockOut)
    # (ClockIn, ClockOut)

    total_break_hours = 0
    for record in range(len(time_in_out_records)):
        if record < len(time_in_out_records) - 1:
            out_to_lunch = datetime.strptime(time_in_out_records[record][1], "%Y-%m-%d %H:%M:%S").timestamp()
            back_from_lunch = datetime.strptime(time_in_out_records[record+1][0], "%Y-%m-%d %H:%M:%S").timestamp()
            total_break_hours += back_from_lunch - out_to_lunch
    
    conn.close()
    total_break_hours = round(total_break_hours / 3600, 3)

    if total_period_hours >= 8:
        if total_break_hours >= .5:
            return total_period_hours
        else:
            return total_period_hours - (.5 - total_break_hours)
    else:
        return total_period_hours

def calculateTotalPaidEmpHours(start_date, end_date, entered_format, id):
    dates = getArrayOfDates(start_date, end_date, entered_format, "%Y-%m-%d")
    total_break_hours = 0
    array_of_total_hours_per_day = []
    for single_date in dates:
        total_break_hours += getTotalDailyHoursAccountingForBreaks(single_date, "%Y-%m-%d", id)
        array_of_total_hours_per_day.append(getTotalDailyHoursAccountingForBreaks(single_date, "%Y-%m-%d", id))
    return total_break_hours, array_of_total_hours_per_day



def calculate_employee_pay(start_date, end_date, entered_format, id):
    conn = sqlite3.connect(database_file)
    c = conn.cursor()

    array_of_hours_per_day = calculateTotalPaidEmpHours(start_date, end_date, entered_format, id)[1]

    ot_allowed = c.execute("SELECT OTAllowed FROM employees WHERE ID = ?", (id,)).fetchone()
    hourly_pay = c.execute("SELECT HourlyPay FROM employees WHERE ID = ?", (id,)).fetchone()
    conn.commit()
    conn.close()

    ot_allowed = ot_allowed[0].lower()
    hourly_pay = hourly_pay[0]


    regular_hours = 0
    overtime_hours = 0
    double_time_hours = 0
    if ot_allowed == "yes":
        for hours_per_day in array_of_hours_per_day:
            if hours_per_day <= 8:
                #regular_pay += hourly_pay * hours_per_day
                regular_hours += hours_per_day
            elif hours_per_day > 8 and hours_per_day < 12:
                #total_pay += hourly_pay * 8 + hourly_pay * 1.5 * (hours_per_day - 8)
                regular_hours += 8
                overtime_hours += hours_per_day - 8
            else:
                #total_pay += hourly_pay * 8 + hourly_pay * 1.5 * 4 + hourly_pay * 2 * (hours_per_day - 12)
                regular_hours += 8
                overtime_hours += 4
                double_time_hours += hours_per_day - 12
    elif ot_allowed == "no":
        #total_pay += hourly_pay * total_employee_hours
        regular_hours = calculateTotalPaidEmpHours(start_date, end_date, entered_format, id)[0]

    regular_pay = round(hourly_pay * regular_hours, 2)
    overtime_pay = round(hourly_pay * 1.5 * overtime_hours, 2)
    double_time_pay = round(hourly_pay * 2 * double_time_hours, 2)

    regular_hours = round(regular_hours, 3)
    overtime_hours = round(overtime_hours, 3)
    double_time_hours = round(double_time_hours, 3)

    total_pay = round(regular_pay + overtime_pay + double_time_pay, 2)
    total_hours = round(calculateTotalPaidEmpHours(start_date, end_date, entered_format, id)[0], 3)

    #returned_array = [total_pay, [regular_hours, overtime_hours, double_time_hours], [regular_pay, overtime_pay, double_time_pay]]

    dictionary = {
        "Regular Hours": regular_hours,
        "Regular Pay": regular_pay,
        "Overtime Hours": overtime_hours,
        "Overtime Pay": overtime_pay,
        "Double Time Hours": double_time_hours,
        "Double Time Pay": double_time_pay,
        "Total Hours": total_hours,
        "Total Pay": total_pay,
    }

    return dictionary

    




        

    



    # The following works, however, since I fixed the time clock entries such that they can only be on the same day, all the nested if statements aren't necessary.
    # start_date = datetime.strptime(start, "%m/%d/%y").timestamp()
    # print(start_date)
    # end_date = datetime.strptime(end, "%m/%d/%y").timestamp()
    # print(end_date)

    # employee_hours = 0
    # time_in_out_records = c.execute("SELECT ClockIn, ClockOut FROM time_clock_entries WHERE empID = '" + id + "';").fetchall()
    # total_seconds = 0
    # for time_record in time_in_out_records:
    #     t0 = datetime.strptime(time_record[0], "%Y-%m-%d %H:%M:%S").timestamp()
    #     t1 = datetime.strptime(str(datetime.now()), "%Y-%m-%d %H:%M:%S.%f").timestamp()
    #     if time_record[1] is not None:
    #         t1 = datetime.strptime(time_record[1], "%Y-%m-%d %H:%M:%S").timestamp()
                
    #     if end_date > start_date and t1 > t0:
    #         if t0 >= start_date and t1 <= end_date:
    #             total_seconds += t1 - t0
    #             print("1: " + str(total_seconds))
    #         elif t0 < start_date and t1 <= end_date:
    #             total_seconds += t1 - start_date
    #             print("2: " + str(total_seconds))
    #         elif t0 >= start_date and t1 > end_date:
    #             total_seconds += end_date - t0
    #             print("3: " + str(total_seconds))
    #         elif start_date < t0 and end_date < t0:
    #             total_seconds += end_date - start_date
    #             print("4: " + str(total_seconds))
    #         elif start_date > t1 and end_date > t1:
    #             total_seconds += end_date - start_date
    #             print("5: " + str(total_seconds))
                
    # employee_hours = round(total_seconds / 3600, 8)

    # conn.commit()
    # conn.close()
    # return employee_hours




#clear([start_date_label, end_date_label], )







    
def clear_widget_text(widget):
    widget['text'] = ""



global_confirmation_text = StringVar()


#Setup
day_of_week = Label(root, text="", font=("Arial", 25), fg="blue", pady=45)
day_of_week.place(relx=.175, rely=0.0, anchor=N)

program_clock = Label(root, text="", font=("Arial", 25), fg="blue", pady=45)
program_clock.place(relx=.825, rely=0.0, anchor=N)

day_time_greeting = Label(root, text="", font=("Arial", 25), fg="blue")
day_time_greeting.place(relx=0.5, rely=0.189, anchor=N)

clock()
#root.after(1000, clock)
greeting_time()
send_report_if_pay_day()

header = Label(root, text="SBCS\nEmployee Time Clock", font=("Times New Roman", 25, "bold"), pady=22.5)
header.place(relx=0.5, rely=0.0, anchor=N)




#Employee Widgets:
id_field_label = Label(root, text="ID: ", font=("Arial", 20))
id_field_label.place(relx=0.39, rely=.28, anchor=N)

id_field = Entry(root, font=("Arial", 20), show="\u2022")
id_field.place(relx=.50, rely=.289, width=200, height=28, anchor=N)

button = Button(root, text="Enter", command=enter, font=("Arial", 15))
button.place(relx=.6, rely=.28)
root.bind("<Return>", lambda event=None: button.invoke())

greeting = Label(root, text="", font=("Arial", 18), wraplength=700)
greeting.place(relx=.5, rely=.36, anchor=N)

#rely = .35
#rely = .375
#rely = .4



enter_actual_clock_out_time_label = Label(root, text="", font=("Arial", 18))
enter_actual_clock_out_time_label.place(relx=.5, rely=.425, anchor=N)

enter_actual_clock_out_time_entry = Entry(root, font=("Arial", 18), width=13)

actual_clock_out_time_submit_button = Button(root, text="Submit", font=("Arial", 18))

time_in = Label(root, text="", font=("Arial", 10))
time_in.place(relx=.075, rely=.4, anchor=N)

time_out = Label(root, text="", font=("Arial", 10))
time_out.place(relx=.175, rely=.4, anchor=N)

forward = Button(root, text=">", font=("Arial", 15), command=next_day_totals)

backward = Button(root, text="<", font=("Arial", 15), command=previous_day_totals)

current_date_mm_dd_yy = datetime.strptime(str(datetime.now().date()), "%Y-%m-%d").date()

day_total = Label(root, text="", font=("Arial", 20, "underline"))
day_total.place(relx=.175, rely=.3, anchor=N)

period_total = Label(root, text="", font=("Arial", 20, "underline"))
period_total.place(relx=.825, rely=.3, anchor=N)

period_days = Label(root, text="", font=("Arial", 10))
period_days.place(relx=.775, rely=.42, anchor=N)

period_daily_hours = Label(root, text="", font=("Arial", 10))
period_daily_hours.place(relx=.875, rely=.42, anchor=N)

time_duration = Label(root, text="", font=("Arial", 10))
time_duration.place(relx=.275, rely=.4, anchor=N)

employee_task_header_label = Label(root, text="", font=("Arial", 20, "underline"))
employee_task_header_label.place(relx=.5, rely=.7, anchor=N)

employee_task_label = Label(root, text="", font=("Arial", 13), wraplength=300, justify="center")
employee_task_label.place(relx=.5, rely=.77, anchor=N)

z_time_clock_label = Label(root, text="ZTimeClock Ver 1.01", font=("Arial", 10))
z_time_clock_label.place(relx=.9, rely=.9, anchor=N)

















# #Admin Widgets:

# #Employee Codes
# employee_codes_label_for_button = Label(root, text="", font=("Arial", 15))
# employee_codes_label_for_button.place(relx=.4605, rely=.29, anchor=N)
# employee_codes_button = Button(root, text="", font=("Arial", 15))

# #Assign Tasks
# assign_tasks_label_for_button = Label(root, text="", font=("Arial", 15))
# assign_tasks_label_for_button.place(relx=.4605, rely=.33, anchor=N)
# assign_tasks_button = Button(root, text="", font=("Arial", 15))

# #Current Period Totals
# period_totals_label_for_button = Label(root, text="", font=("Arial", 15))
# period_totals_label_for_button.place(relx=.4605, rely=.37, anchor=N)
# period_totals_button = Button(root, text="", font=("Arial", 15))

# #Historical Totals
# historical_totals_label_for_button = Label(root, text="", font=("Arial", 15))
# historical_totals_label_for_button.place(relx=.4605, rely=.41, anchor=N)
# historical_totals_button = Button(root, text="", font=("Arial", 15))


main_menu = LabelFrame(root, padx=50, pady=25)



employee_codes_label_for_button = Label(root)
employee_codes_button = Button(root)
#Sub buttons
employee_codes_button__add_new_employee_label_for_button = Label(root)
employee_codes_button__add_new_employee_button = Button(root)
employee_codes_button__edit__label_for_button = Label(root)
employee_codes_button__edit_button = Button(root)
employee_codes_button__delete_label_for_button = Label(root)
employee_codes_button__delete_button = Button(root)
employee_codes_button__view_label_for_button = Label(root)
employee_codes_button__view_button = Button(root)






assign_tasks_label_for_button = Label(root)
assign_tasks_button = Button(root)
period_totals_label_for_button = Label(root)
period_totals_button = Button(root)
historical_totals_label_for_button = Label(root)
historical_totals_button = Button(root)



















# employee_hours_button = Button(root, text="", font=("Arial", 10))

# employee_list_label = Label(root, text="", font=("Arial", 10))
# employee_list_label.place(relx=.48, rely=.32, anchor=N)

# employee_hours_label = Label(root, text="", font=("Arial", 10))
# employee_hours_label.place(relx=.52, rely=.32, anchor=N)

# start_date_label = Label(root, text="", font=("Arial", 10))
# start_date_label.place(relx=.4, rely=.28, anchor=CENTER)

# end_date_label = Label(root, text="", font=("Arial", 10))
# end_date_label.place(relx=.5, rely=.28, anchor=CENTER)

# employee_start_date = Entry(root, text="", font=("Arial", 10))
# employee_end_date = Entry(root, text="", font=("Arial", 10))


root.mainloop()

#[start_date_label, end_date_label, greeting, time_in, time_out, time_duration, employee_list_label, employee_hours_label], [employee_hours_button, employee_start_date, employee_end_date]