import tkinter as tk
import can
import threading
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random
import time
import datetime

class CANBusApp:
    def __init__(self, master):        
        self.master = master
        master.title("CAN Bus Communication")
        master.geometry("850x900")         
        self.check_flag = tk.IntVar()
        self.check_btn = tk.Checkbutton(master, text="Teaching Mode", variable=self.check_flag, command=self.on_checkbutton_change)    
        self.check_btn.grid(row=0, column=3, columnspan=1)
        self.label = tk.Label(master, text="CANID")
        self.label.grid(row=2, column=0)
        self.can_id_entry = tk.Entry(master)
        self.can_id_entry.grid(row=3, column=0)
        self.parameter_label = tk.Label(master, text="Param")       
        self.parameter_label.grid(row=2, column=2)
        self.alarm_threshold_label = tk.Label(master, text="Alarm")
        self.alarm_threshold_label.grid(row=2, column=4)
        self.alarm_threshold_entry = tk.Entry(master)
        self.alarm_threshold_entry.grid(row=3, column=4)
        self.status_label = tk.Label(master, text="Status")
        self.status_label.grid(row=2, column=6)
        self.status_entry = tk.Entry(master)
        self.status_entry.grid(row=3, column=6)           
        self.id_button = tk.Button(master, text="Start", width=6, height=1, command=self.transceive_message)
        self.id_button.grid(row=3, column=1)
        self.received_messages = tk.Text(master, height=5, width=15)
        self.received_messages.grid(row=3, column=2, rowspan=2)  
        self.parameter_button = tk.Button(master, text="Update", width=6, height=1, command=self.transceive_message)
        self.parameter_button.grid(row=3, column=3)
        self.alarm_button = tk.Button(master, text="Update", width=6, height=1,command=self.transceive_message)
        self.alarm_button.grid(row=3, column=5)        
        self.canvas_width = 800
        self.canvas_height = 400
        self.canvas = tk.Canvas(master, width=self.canvas_width, height=self.canvas_height, bg="white")
        self.canvas.grid(row=6, columnspan=7)
        self.start_button = tk.Button(self.master, text="Start", command=self.start_simulation)
        self.start_button.grid(row=7, column=1)
        self.bus = can.interface.Bus(channel='can0', interface='socketcan') 
        self.start_threads()
        self.can_values = [0 for _ in range(100)]
        self.max_values = 100
        self.simulation_running = False        
        self.event = threading.Event()
        self.slave_ID = ""        
        self.can_message = CANMSG()
        self.start_simulation()
    def on_checkbutton_change(self):
        #This function is invoked when the checkbox is checked/unchecked
        if self.check_flag.get():
            print("Checkbox is checked")
        else:
            print("Checkbox is unchecked")  

    def start_simulation(self):
        self.simulation_running = True
        self.update_graph()

    def update_graph(self):
        if self.simulation_running:
            # Simulate receiving a new CAN bus value (0-100)
            #new_value = random.randint(0, 100)
            #self.can_values.append(new_value)

            # Keep the list size within max_values
            if len(self.can_values) > self.max_values:
                self.can_values.pop(0)

            # Redraw the graph
            self.draw_graph()

            # Repeat every 500ms
            self.master.after(500, self.update_graph)

    def draw_graph(self):
        # Clear the canvas before drawing
        self.canvas.delete("all")

        # Define the canvas drawing area
        margin = 20
        width = self.canvas_width - 2 * margin
        height = self.canvas_height - 2 * margin

        # Draw axes
        self.canvas.create_line(margin, margin, margin, self.canvas_height - margin, width=2)  # Y-axis
        self.canvas.create_line(margin, self.canvas_height - margin, self.canvas_width - margin, self.canvas_height - margin, width=2)  # X-axis

        # Check if there are any values to plot
        if len(self.can_values) > 1:
            max_value = max(self.can_values)
            min_value = min(self.can_values)
            value_range = max_value - min_value if max_value != min_value else 1

            # Scale the values to fit within the canvas
            scaled_values = [
                ((value - min_value) / value_range) * (height - margin)
                for value in self.can_values
            ]

            # Calculate X-axis spacing for each value
            x_step = width / (len(scaled_values) - 1)

            # Plot the values as lines
            for i in range(1, len(scaled_values)):
                x1 = margin + (i - 1) * x_step
                y1 = self.canvas_height - margin - scaled_values[i - 1]
                x2 = margin + i * x_step
                y2 = self.canvas_height - margin - scaled_values[i]

                # Draw the line connecting the two points
                self.canvas.create_line(x1, y1, x2, y2, fill="blue", width=2)
    def start_threads(self):
        self.sender_thread = threading.Thread(target=self.transceive_message)
        self.sender_thread.daemon = True
        self.sender_thread.start() 

    def transceive_message(self):
        while True:
            if self.can_id_entry.get() != "":
                can_id = int(self.can_id_entry.get(), 16)  # Getting CAN ID in hex format
                print(f"Entry checking")
            self.can_message.create_message(self.can_message.msg_type_dict["status"])   
            smsg = self.can_message.can_msg_data
            if smsg:
                msg = can.Message(arbitration_id=0x01, data=smsg)
                #time.sleep(0.01)
                try:
                    print(f"Message {msg} sent with CAN ID {11}")
                    self.bus.send(msg)
                except can.CanError:
                    print("Message NOT sent", can.CanError)
                    print("msg", msg)
            #self.event.wait()
            rmsg = self.bus.recv(1)
            if rmsg is None:
                print("No message received")
                continue
                #rmessage = self.bus.recv() 
            rmsg_id = rmsg.arbitration_id - 0xf00
            if rmsg_id == 0x01:                    
                received_message = f"Received message: ID: {hex(rmsg.arbitration_id)}, Data: {rmsg.data}\n"
                print("received message", received_message)
                self.can_values.append(self.can_message.analyze_message(rmsg.data))
    
    def open_parameter_popup(self):
        self.popup = ParameterSetting(self.master, self)

class CANMSG:
    def __init__(self):
        # Can Flag byte
        self.msg_type_dict = { 
            "status": 0x01, 
            "alarm_threshold": 0x02, 
            "rw_setting": 0x04,
            "RTC": 0x08, 
            "history":0x10
        }

        self.can_msg_data = []
        self.received_msg_data = []
        self.alarm_threshold_current = 2234
        self.ralarm_threshold_current = 1234

        self.rw_dict = {    
            "P":10,
            "I":10,
            "D":10,
            "T":10,
            "Calibration":20,
            "RW":False
            }

        self.dict_history = {
            "max_current":1234,
            "min_current":1056,
            "average":1642
            }

    def create_message( self, msg_type ):
        self.can_msg_data.clear()
        self.can_msg_data.append(msg_type)
        if msg_type == self.msg_type_dict["status"]:
            print("status")
        
        elif msg_type == self.msg_type_dict["alarm_threshold"]:
            print("alarm_threshold")
            self.can_msg_data.append(self.alarm_threshold_current / 100)
            self.can_msg_data.append(self.alarm_threshold_current % 100)
        elif msg_type == self.msg_type_dict["rw_setting"]:
            print("rw_setting")
            self.can_msg_data.append(self.rw_dict["P"])
            self.can_msg_data.append(self.rw_dict["I"])
            self.can_msg_data.append(self.rw_dict["D"])
            self.can_msg_data.append(self.rw_dict["T"])
            self.can_msg_data.append(self.rw_dict["Calibration"])
            self.can_msg_data.append(self.rw_dict["RW"])
        elif msg_type == self.msg_type_dict["RTC"]:
            print("RTC")
            current_time = datetime.datetime.now()
            self.can_msg_data.append(current_time.hour)
            self.can_msg_data.append(current_time.minute)
            self.can_msg_data.append(current_time.second)
            self.can_msg_data.append(current_time.day)
            self.can_msg_data.append(current_time.month)
            self.can_msg_data.append(current_time.year % 100)
        elif msg_type == self.msg_type_dict["history"]:
            print("History")
            self.can_msg_data.append(self.dict_history["max_current"] / 100)
            self.can_msg_data.append(self.dict_history["max_current"] % 100)
            self.can_msg_data.append(self.dict_history["min_current"] / 100)
            self.can_msg_data.append(self.dict_history["min_current"] % 100)
            self.can_msg_data.append(self.dict_history["average"] / 100)
            self.can_msg_data.append(self.dict_history["average"] % 100)
        
    def analyze_message(self, received_msg):
        print("analyze_message")
        if received_msg[0] == self.msg_type_dict["status"]:
            print("status message from Adafruit")
            current = received_msg[1] + received_msg[2] / 100
            print("current", current)
            return current
        elif received_msg[0] == self.msg_type_dict["alarm_threshold"]:
            print("alarm_threshold")
        elif received_msg[0] == self.msg_type_dict["rw_setting"]:
            print("rw_setting")
        elif received_msg[0] == self.msg_type_dict["RTC"]:
            print("RTC")
        elif received_msg[0] == self.msg_type_dict["history"]:
            print("history")


class ParameterSetting:
    def __init__(self, master, parent):
        self.master = master
        self.parent = parent
        self.popup_window = tk.Toplevel(master)
        self.popup_window.title("Parameter Setting")

        self.popup_entry = tk.Entry(self.popup_window)
        self.popup_entry.pack(pady=10)

        self.close_button = tk.Button(self.popup_window, text="Close", command=self.close_popup_window)
        self.close_button.pack(pady=5)
    def close_popup_window(self):
        self.parameter = self.popup_entry.get()
        self.parent.alarm_threshold_entry.delete(0, tk.END)
        self.parent.alarm_threshold_entry.insert(0, self.parameter)
        self.parent.send_message(self.parameter)
        self.popup_window.destroy()

def main():
    root = tk.Tk()
    can_bus_app = CANBusApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()