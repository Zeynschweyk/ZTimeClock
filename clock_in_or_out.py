from my_import_statements import *
from static_widgets import StaticWidgets

Builder.load_file("clock_in_or_out.kv")


class ClockInOrOut(StaticWidgets):
    emp_obj: Employee = None

    # name_and_status = ObjectProperty(None)
    # date_and_total_day_hours = ObjectProperty(None)
    # time_in = ObjectProperty(None)
    # time_out = ObjectProperty(None)
    # duration = ObjectProperty(None)

    def __init__(self, **kw):
        super().__init__(**kw)

    def show_day_totals(self, day):
        daily_records, total_day_hours = \
            self.emp_obj.get_records_and_hours_for_day(day.strftime("%m/%d/%y"), "%m/%d/%y")
        self.date_and_total_day_hours.text = f"Today's\nTotal Hours: {round(total_day_hours, 2)}"

        self.time_in.text = "Time In\n" + "-" * 25 + "\n"
        self.time_out.text = "Time Out\n" + "-" * 25 + "\n"
        self.duration.text = "Duration\n" + "-" * 25 + "\n"
        y_pos = .37
        self.widgets = []
        for rec in daily_records:
            time_in = Label(text=rec[0], pos_hint={"center_x": .4, "center_y": y_pos}, halign="center")
            time_out = Label(text=rec[1], pos_hint={"center_x": .5, "center_y": y_pos}, halign="center")
            duration = Label(text=rec[2], pos_hint={"center_x": .6, "center_y": y_pos}, halign="center")
            self.widgets.append([time_in, time_out, duration])
            self.add_widget(time_in)
            self.add_widget(time_out)
            self.add_widget(duration)
            y_pos -= .03

    def on_leave(self, *args):
        Thread(target=self.z_clear_widgets())

    def z_clear_widgets(self):
        try:
            for time_in, time_out, duration in self.widgets:
                self.clear_widgets([time_in, time_out, duration])
        except:
            pass

    def show_period_totals(self):
        pass

    def on_pre_enter(self, *args):
        self.name_and_status = Label(
            pos_hint={"center_y": .7},
            halign="center",
            font_size=30
        )
        self.add_widget(self.name_and_status)


        self.back_button()

        # self.emp_obj.min_wait_time = 10 * 60 by default. clock_in_or_out automatically checks if the duration
        # between clock out and clock in is >= self.emp_obj.min_wait_time. To change it, set it in
        # employee_menu_screen.py in the clock_in_or_out method.

        # Reasons why this would be False:
        #   1. They try to clock in before self.emp_obj.min_wait_time has passed
        #   2. They try to clock out on a different day than their previous clock in
        #
        # The test in the clock_in_or_out method in the employee_menu_screen will make sure that #1 passes
        if self.emp_obj.clock_in_or_out():


            self.date_and_total_day_hours = Label(
                pos_hint={"center_y": .5},
                halign="center",
                font_size=27
            )
            self.add_widget(self.date_and_total_day_hours)

            self.time_in = Label(
                pos_hint={"center_x": .4, "center_y": .4},
                halign="center"
            )
            self.add_widget(self.time_in)

            self.time_out = Label(
                pos_hint={"center_y": .4},
                halign="center"
            )
            self.add_widget(self.time_out)

            self.duration = Label(
                pos_hint={"center_x": .6, "center_y": .4},
                halign="center"
            )
            self.add_widget(self.duration)

            self.name_and_status.text = self.emp_obj.first + " " + self.emp_obj.last + \
                                        f"\nYou're clocked {'IN' if self.emp_obj.get_status() else 'OUT'}"
            Thread(target=lambda: self.show_day_totals(datetime.today())).start()
        else:
            # self.clear_widgets([self.date_and_total_day_hours, self.time_in, self.time_out, self.duration])
            self.name_and_status.text = self.emp_obj.first + " " + self.emp_obj.last
            # c.exec_sql()
            instructions = Label(
                text="On your last workday on 12/12/12, you clocked in at TIME and forgot to clock out.\n"
                     "Please select the time you left work on that day.",
                pos_hint={"center_y": .6},
                halign="center"
            )
            self.add_widget(instructions)

            self.pick_time_text_box = MDTextField(
                hint_text="HH:MM am/pm",
                font_size=25,
                pos_hint={"center_y": .5, "center_x": .5},
                size_hint=(.15, .085),
                on_touch_down=lambda x, y: self.open_time_picker(x, y)
            )
            self.add_widget(self.pick_time_text_box)

            return

    def open_time_picker(self, x, y):
        if self.pick_time_text_box.collide_point(*y.pos):
            time_picker_dialog = MDTimePicker()
            if self.pick_time_text_box.text != "":
                default_time = datetime.strptime(self.pick_time_text_box.text, "%I:%M %p").time()
            else:
                clock_in = c.exec_sql("SELECT ClockIn FROM time_clock_entries WHERE empID = ? ORDER BY row DESC LIMIT 1;",
                           param=(self.emp_obj.emp_id,),
                           fetch_str="one"
                           )[0][11:]
                default_time = (datetime.strptime(clock_in, "%H:%M:%S") + timedelta(minutes=1)).time()
            time_picker_dialog.set_time(default_time)
            time_picker_dialog.bind(on_save=self.get_time)
            time_picker_dialog.open()
            # self.pick_time_text_box.text = time_picker_dialog.hour + ":" + time_picker_dialog.minute

    def get_time(self, instance, t):
        self.pick_time_text_box.text = t.strftime("%I:%M %p")


