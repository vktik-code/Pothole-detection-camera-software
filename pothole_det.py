import cv2
import tkinter
import json
import random
import numpy
import time
import folium
from PIL import Image, ImageTk
import onnxruntime
import spidev
import pyautogui
import tkintermapview
from luma.core.interface.serial import spi
from luma.lcd.device import ili9486
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageGrab, ImageOps

GPIO.setmode(GPIO.BCM)
GPIO.setup(24, GPIO.OUT)
GPIO.setup(24, GPIO.LOW)
time.sleep(0.1)
GPIO.output(24, GPIO.HIGH)
pyautogui.FAILSAFE=False
serial =spi(port=0, device=0, gpio_DC=24, gpio_RST=25, bus_speed_hz=8000000, mode=3)
device = ili9486(serial, rotate=1)
spi=spidev.SpiDev()
spi.open(0,1)
spi.max_speed_hz=1000000
import tkinterweb
from tkinterweb import HtmlFrame

root=tkinter.Tk()
root.title("Pothole Detection")
root.config(bg="maroon",relief="ridge",bd=10)
root.state('normal')
root.attributes('-fullscreen', True)
canvas=tkinter.Canvas(height="960",width="1280",bg="black")
canvas.grid(row=0, column=0,columnspan=2,rowspan=2)
canvas.rowconfigure(0,weight=1)
canvas.columnconfigure(0,weight=1)

global cap, frame
camera=tkinter.PhotoImage(file=r"/home/gimfil/Desktop/pothole másolata/cam.png")
mapimg=tkinter.PhotoImage(file=r"/home/gimfil/Desktop/pothole másolata/map.png")
frame=None
a=0
session = onnxruntime.InferenceSession(r"/home/gimfil/Desktop/pothole másolata/runs/detect/train3/weights/best.onnx")
url = "http://10.3.92.254qqqq:8080/video"

cap = cv2.VideoCapture(0,cv2.CAP_V4L2)
time.sleep(5)
print(cap.getBackendName())
    
cap.set(cv2.CAP_PROP_FOURCC,cv2.VideoWriter_fourcc(*'MJPG'))
cap.set(cv2.CAP_PROP_FRAME_WIDTH,640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT,480)

global event,quality,more_conf, lat_min, lat_max, lon_min, lon_max, event_id
event_id=None
quality="Nan"
event=None
ret=None
more_conf=None
lat_min=48.276747
lat_max=48.258884
lon_min=19.807773
lon_max=19.646457

def websearch():
    global event, frame
    canvas.grid_remove()
    if event is not None:
        canvas.after_cancel(event)
    frame = HtmlFrame(root,height=768,width=1024)
    frame.load_website(str(entry.get()))
    frame.grid(row=0, column=0, rowspan=2)
def map_mod():
    global event_id
    if event_id is not None:
        canvas.after_cancel(event_id)
    canvas.grid_forget()
    map_widget=tkintermapview.TkinterMapView(root,width=1280,height=960)
    map_widget.grid(row=0,column=0,rowspan=2,columnspan=2)
    map_widget.set_position(48.276747,19.807773)
    map_widget.set_zoom(15)
    
    
    
'''
def connect():
    global url, cap, frame
    url = "http://192.168.1.41:8080/video"
    cap = cv2.VideoCapture(url)
    if frame is not None:
        frame.destroy()
    canvas.grid(row=0, column=0,columnspan=2)
    update_frame()
'''
global press_time
press_time=0
def get_touch():
    resp_y =spi.xfer2([0x90,0,0])
    y=((resp_y[1] << 8) | resp_y[2])
    resp_x =spi.xfer2([0xD0,0,0])
    x=((resp_x[1] << 8) | resp_x[2])
    resp_z=spi.xfer2([0xB0,0,0])
    z=((resp_z[1] << 8) | resp_z[2]) >> 3
    return x,y,z
def update_mouse():
    global is_touching, touches, last_touch_time, press_time
    raw_y, raw_x , raw_z = get_touch()
    current_time=time.time()
    pixel_x=int(raw_x*(240/4095))
    pixel_y=int(1280-(raw_y*(160/4095)))
    if raw_x > 100:
        pyautogui.moveTo(pixel_x,pixel_y)
    if raw_z > 50 :
        press_time=press_time+1
    if press_time>4:
        press_time=0
        pyautogui.click()
    if press_time>1:
        pyautogui.mouseDown(button="left")
        pyautogui.dragRel()
    
        
def update_frame():
    global event_id, event, url, cap, quality, more_conf, lat_min, lat_max, lon_min, lon_max
    canvas.grid(row=0, column=0,columnspan=2,rowspan=2)
    ret, frame = cap.read()
    if frame is not None:
        img=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img=cv2.resize(img,(640,640))
        img=img.transpose(2,0,1)
        img=numpy.expand_dims(img, axis=0)
        img=img.astype("float32")/255.0
        
        quality=100
        all_conf=[]   
        results = session.run(None, {"images": img})     
        cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(cv2image)
        new_size=(img.width *2 ,img.height *2)
        img=img.resize(new_size,Image.Resampling.LANCZOS)
        imgtk = ImageTk.PhotoImage(image=img)
        canvas.create_image(0, 0, image=imgtk, anchor=tkinter.NW)
        predictions = numpy.squeeze(results[0]).T
        for pred in predictions:
            confidence = pred[4:]
            class_id =numpy.argmax(confidence)
            conf_score = confidence[class_id]
            if conf_score > 0.5:
                all_conf.append(conf_score)
                x_center, y_center, h, w = pred[0:4]
                x1 = int(int(x_center - w/2)*(frame.shape[1]/640))
                y1 = int(int(y_center - h/2)*(frame.shape[0]/640))
                x2 = int(int(x_center + w/2)*(frame.shape[1]/640))
                y2 = int(int(y_center + h/2)*(frame.shape[0]/640))

                canvas.create_rectangle(x1, y1, x2, y2, outline="green")
                canvas.create_text(x1, y1 - 10 , text=f"Pothole, Conf: {conf_score:.2f}", font="arial 30", fill="blue")
        
        if len(all_conf)>0:
            quality=1-((sum(all_conf)/len(all_conf)))
            more_conf={"confidence":quality,"latitude":random.uniform(lat_min,lat_max),"longitude":random.uniform(lon_min,lon_max)}
            label.config(text=f"Quality: {quality*100:2f}%")
        
    
    
    
        
        
            
            
    
    
    '''
        with open("pothole.json", "a") as f:
            json.dump(more_conf, f)
            f.write("\n")
    '''
    
    
    
    canvas.scale("all",0,0,2,2)
    canvas.update_idletasks()
    event_id=canvas.after(10, update_frame)
    



    
def deviceu():
    update_mouse()
    img = ImageGrab.grab()

    img =img.resize((device.width,device.height), Image.NEAREST)
    img= ImageOps.invert(img)
    device.display(img)
    canvas.after(10,deviceu)
def ex():
    exit()

deviceu()
button=tkinter.Button(root,text="Web Search",command=lambda: websearch(),fg="white",bg="maroon",font="Courier 30 bold")
button.grid(row=2,column=0)
button.rowconfigure(1, weight=1)
entry=tkinter.Entry(root,font="Courier 15 bold",bg="white",fg="maroon")
entry.insert(0,"Enter URL")
entry.grid(row=3,column=0)
button1=tkinter.Button(root,image=camera,command=lambda: update_frame(),fg="white",bg="maroon",font="Courier 50 bold")
button1.grid(row=0,column=2,rowspan=1)
button3=tkinter.Button(root,image=mapimg, bg="maroon",fg="white",command=lambda: map_mod())
button3.grid(row=1,column=2,rowspan=1)
label=tkinter.Label(root,text=f"Quality: {quality}%",font="Courier 30 bold",bg="maroon",fg="white")
label.grid(row=2,column=1)
button2=tkinter.Button(root,text="Exit",command=lambda: ex(),width="20",height="2", font="Courier 30 bold",bg="maroon",fg="white")
button2.grid(row=2,column=2,rowspan="1")

root.mainloop()


