import kivy
import kivymd
from kivy.config import Config

from kivy.uix.label import Label

from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDFlatButton
from kivymd.uix.button import MDRoundFlatButton
from kivymd.uix.button import MDFillRoundFlatButton
from kivymd.uix.dialog import MDDialog
from kivy.uix.scrollview import ScrollView
from kivymd.uix.list import MDList, OneLineListItem, TwoLineListItem
# from kivymd.uix.datatables import MDDataTable
from kivymd.uix.picker import MDTimePicker
from kivymd.uix.picker import MDDatePicker
from kivy.lang import Builder
from kivy.core.window import Window
from datetime import datetime
from kivy.properties import ObjectProperty
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen
from employee_class import Employee, ZSqlite
from UsefulFunctions import *
import random
import time
from threading import Thread



db_path = "../employee_time_clock.db"
c = ZSqlite(db_path)

