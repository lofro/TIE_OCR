import cv2
import tkinter #python quick user interface
import tkinter.scrolledtext as tkscrolledtext
import PIL.Image, PIL.ImageTk
import time
import sys
import datetime
import threading
import queue


#My libs
import serial_rx_tx
import Img_to_Word

#Initialize serial out port (will be COM3 at 9600 but can be changed)
serialPort = serial_rx_tx.SerialPort()


#Initialize log file
logFile = None

#Main app class
class App:

    # Inital code steps up all the user interface
    def __init__(self, window, window_title, video_source=0):
        self.thread_queue = queue.Queue() #queue for thread    
        self.window = window # tkinter 
        self.window.title(window_title)
        self.video_source = video_source
        self.outtext="Start"

        # open video source (by default this will try to open the computer webcam)
        self.vid = MyVideoCapture(self.video_source)  
        # Create a canvas that can fit the above video source size
        self.canvas = tkinter.Canvas(window, width = self.vid.width, height = self.vid.height)
        self.canvas.grid(row=0,column=0, rowspan=10)
        # Comport
        self.label_comport = tkinter.Label(window,width=8,height=2,text="COM Port:")
        self.label_comport.grid(column=1, row=0)
        self.label_comport.config(font="bold")
        #COM Port entry box
        self.comport_edit = tkinter.Entry(window,width=8)
        self.comport_edit.grid(column=2, row=0)
        self.comport_edit.config(font="bold")
        self.comport_edit.insert(tkinter.END,"COM3")
        # COM Port open/close button
        self.button_openclose = tkinter.Button(window,text="Open COM Port",width=15,command=self.OpenCommand)
        self.button_openclose.config(font="bold")
        self.button_openclose.grid(column=3, row=0)
        #Clear Rx Data button
        self.button_cleardata = tkinter.Button(window,text="Clear Rx Data",width=15,command=self.ClearDataCommand)
        self.button_cleardata.config(font="bold")
        self.button_cleardata.grid(column=4, row=0)
        #Baud Rate label
        self.label_baud = tkinter.Label(window,width=8,height=2,text="Baud Rate:")
        self.label_baud.grid(column=1, row=1)
        self.label_baud.config(font="bold")
        #Baud Rate entry box
        self.baudrate_edit = tkinter.Entry(window,width=8)
        self.baudrate_edit.grid(column=2, row=1)
        self.baudrate_edit.config(font="bold")
        self.baudrate_edit.insert(tkinter.END,"9600")
        #Refresh label
        self.label_refresh = tkinter.Label(window,width=15,height=2,text="Refresh Rate:")
        self.label_refresh.grid(column=3, row=1)
        self.label_refresh.config(font="bold")
        #Picture refresh button
        self.button_senddata = tkinter.Button(window,text="Refresh Rate (s)",width=15,command=self.Refresh_Rate)
        self.button_senddata.config(font="bold")
        self.button_senddata.grid(column=5, row=1)
        #Refresh Rate entry box
        self.senddata_edit = tkinter.Entry(window,width=8)
        self.senddata_edit.grid(column=4,row=1)
        self.senddata_edit.config(font="bold")
        self.senddata_edit.insert(tkinter.END,"10")
        self.refresh_r=10
        # Textbox
        self.textbox=tkscrolledtext.ScrolledText(master=window, wrap='word', width=50, height=15) #width=characters, height=lines
        self.textbox.grid(column=1, row=3,columnspan=5)
        self.textbox.config(font="bold")
        # Button that lets the user take a snapshot
        self.btn_snapshot=tkinter.Button(window, text="Snapshot", width=50, command=self.snapshot)
        self.btn_snapshot.grid(column=0,row=10)

        ##### start multithread
        self.new_thread1 = threading.Timer(self.refresh_r,
            function=self.pic_to_text,
            kwargs={})
        self.new_thread1.daemon=True
        self.new_thread1.start()

        self.window.after(200, self.update_Image)

############### Take the image and convert it to Text and Send
    def pic_to_text(self):
        #Add new thread to multithread
        self.new_thread1 = threading.Timer(self.refresh_r,
            function=self.pic_to_text,
            kwargs={})
        self.new_thread1.daemon=True
        self.new_thread1.start()

        ##### if com port is open
        if serialPort.IsOpen():
            time_now=str(datetime.datetime.now()) # get time now
            ## convert image to tex
            text1=Img_to_Word.main(self.photo_img)
            
            message=time_now + " " + text1 
            message += '\r\n'
            print(message)
            serialPort.Send(message)
            self.textbox.insert('1.0',message)
        else: ## if comport is closed
            self.textbox.insert('1.0', "Not sent - COM port is closed\r\n")

    ### used for snapshot button to extract text from image at a single moment
    def snapshot(self):
        time_now=str(datetime.datetime.now())
        #### image to text
        text1=Img_to_Word.main(self.photo_img)
        message=time_now+ " " + text1 #+'\r\n'
        
        ### used to save images
        #img =cv2.cvtColor(self.photo_img,cv2.COLOR_RGB2GRAY)
        #ne=time_now.split(".")
        #wr=ne[1]+".jpg"
        #cv2.imwrite(wr,img)

        message += '\r\n'
        print(message)
        
        if serialPort.IsOpen(): # if comport is open send message
            serialPort.Send(message)
            self.textbox.insert('1.0',message)
        else:# closed comport: write message but will not send
            self.textbox.insert('1.0',("WARNING closed comport, message not sent:   " + message))

    # Used to udate video in Tinker
    def update_Image(self):
        # Get a frame from the video source
        ret, frame = self.vid.get_frame()

        ### Get image
        if ret:
            self.photo_img=frame
            self.photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(frame))
            self.canvas.create_image(0, 0, image = self.photo, anchor = tkinter.NW)

        #### Add thread to video queue
        try:
            res = self.thread_queue.get(0)
            self.text_label.config(text=res)
            self.window.after(100, self.update_Image)
        except queue.Empty:
            self.window.after(100, self.update_Image)

    
    ### clear the text box
    def ClearDataCommand(self):
        self.textbox.delete("1.0",tkinter.END)
    
    # # serial data callback function
    def OnReceiveSerialData(self,message):
        str_message = message.decode("utf-8")
        self.textbox.insert('1.0', str_message)

    # Register the callback above with the serial port object
    serialPort.RegisterReceiveCallback(OnReceiveSerialData)

    ## open the serial comport
    def OpenCommand(self):
        if self.button_openclose.cget("text") == 'Open COM Port':
            comport = self.comport_edit.get()
            baudrate = self.baudrate_edit.get()
            serialPort.Open(comport,baudrate)
            self.button_openclose.config(text='Close COM Port')
            self.textbox.insert('1.0', "COM Port Opened\r\n")
        elif self.button_openclose.cget("text") == 'Close COM Port':
            serialPort.Close()
            self.button_openclose.config(text='Open COM Port')
            self.textbox.insert('1.0',"COM Port Closed\r\n")

    ######## Change the refresh rate
    def Refresh_Rate(self):
        plholder=self.senddata_edit.get()
        #### tends to crash if refresh rate is to fast
        if int(plholder)>4.99:
            self.textbox.insert('1.0',("Refresh rate changed: "+plholder+ "\r\n"))
            self.refresh_r = int(plholder)
        else:
            self.textbox.insert('1.0',("Refresh rate WAS NOT changed please choose rate greater then 5s. \r\n"))

####### Create the video capture
class MyVideoCapture:
    def __init__(self, video_source=0):
        # Open the video source
        self.vid = cv2.VideoCapture(video_source)
        if not self.vid.isOpened():
            raise ValueError("Unable to open video source", video_source)

        # Get video source width and height
        self.width = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)

    def get_frame(self):
        if self.vid.isOpened():
            ret, frame = self.vid.read()
            if ret:
                # Return a boolean success flag and the current frame converted to BGR
                return (ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            else:
                return (ret, None)
        else:
            return (None, None)
    # Release the video source when the object is destroyed
    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()

#### multi threading
class ThreadedTask(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.thread_queue = queue
    def run(self):
        time.sleep(5)  # Simulate long running process
        self.thread_queue.put("Task finished")


### initialize tinker
root=tkinter.Tk()
App(root, "Tkinter and OpenCV")

### run system
root.mainloop()
sys.exit()
root.destroy()
