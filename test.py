#coding=utf-8
import sys
import importlib
importlib.reload(sys)
import RPi.GPIO as GPIO
import base64
import time
import binascii
import serial
import serial.tools.list_ports
from mfrc522 import SimpleMFRC522
import threading
import operator
import vlc

Sys_Run=True
Test_Num=0
door_set=['1','2','3','4'] # set keypad passcode
door_input=[] # input passcode
door_order=0
error_count=0
p2 = vlc.MediaPlayer("/home/pi/hello/alarm.mp3") # mp3 file for alarm
LED=5


def Signal_Init(): # initialize GPIO
  GPIO.cleanup()
  GPIO.setmode(GPIO.BCM)
  GPIO.setup(LED,GPIO.OUT)
  GPIO.output(LED,GPIO.HIGH)  # lock electromagnatic lock by defaul

# keypad
class keypad(object):
  KEYPAD=[
    ['1','2','3','A'],
    ['4','5','6','B'],
    ['7','8','9','C'],
    ['*','0','#','D']]
 
  ROW    =[12,16,20,21]
  COLUMN =[6,13,19,26]
 
# initialize GPIO
def init_GPIO():
  GPIO.cleanup()
  GPIO.setmode(GPIO.BCM)
  
# get key
def getkey():
  GPIO.setmode(GPIO.BCM)
  for i in range(len(keypad.COLUMN)):
    GPIO.setup(keypad.COLUMN[i],GPIO.OUT)
    GPIO.output(keypad.COLUMN[i],GPIO.LOW)
  for j in range(len(keypad.ROW)):
    GPIO.setup(keypad.ROW[j],GPIO.IN,pull_up_down=GPIO.PUD_UP)
  RowVal=-1
  for i in range(len(keypad.ROW)):
    RowStatus=GPIO.input(keypad.ROW[i])
    if RowStatus==GPIO.LOW:
       RowVal=i
       #print('RowVal=%s' % RowVal)
  if RowVal<0 or RowVal>3:
    exit()
    return

  GPIO.setup(keypad.ROW[RowVal],GPIO.OUT)
  GPIO.output(keypad.ROW[RowVal],GPIO.HIGH)

  for j in range(len(keypad.COLUMN)):
    GPIO.setup(keypad.COLUMN[j],GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
 
  ColumnVal=-1
  for i in range(len(keypad.COLUMN)):
    ColumnStatus=GPIO.input(keypad.COLUMN[i])
    if ColumnStatus==GPIO.HIGH:
      ColumnVal=i
      while GPIO.input(keypad.COLUMN[i])==GPIO.HIGH:
        time.sleep(0.05)
        #print ('ColumnVal=%s' % ColumnVal)
  if ColumnVal<0 or ColumnVal>3:
    exit()
    return
 
  exit()
  return keypad.KEYPAD[RowVal][ColumnVal]
 
 
def recv(serial):
    while True:
        data = serial.read_all()
        if data == '':
            continue
        else:
            break
    return data

# find & match fingerprint
def finger_find():
    search = 'EF 01 FF FF FF FF 01 00 08 04 01 00 00 00 64 00 72'
    search = bytes.fromhex(search)
    serial.write(search)
    time.sleep(1)
    search_data = recv(serial)
    print("Please scan your fingerprint")
    search_con = str(binascii.b2a_hex(search_data))[20:22]
    if (search_con == '09'):
        print("Fingerprint does not match our record. Please try again")
        return 0
    elif(search_con == '00'):
        print ('Correct fingerprint. Door open.')
        GPIO.output(LED,GPIO.LOW)
        time.sleep(5)
        GPIO.output(LED,GPIO.HIGH)
        return 1 

def finger_input():
    a = 'EF 01 FF FF FF FF 01 00 03 01 00 05' # get fingerprint image
    d = bytes.fromhex(a)
    serial.write(d)
    time.sleep(1)
    data =recv(serial)
    print(data)
    if data != b'' :
        data_con = str(binascii.b2a_hex(data))[20:22]
        if(data_con == '02'):
            print("Please scan your fingerprint")
        elif(data_con == '00'):
            print("Scan Successful")
            buff = 'EF 01 FF FF FF FF 01 00 04 02 01 00 08'  # place image in buffer
            buff = bytes.fromhex(buff)
            serial.write(buff)
            time.sleep(1)
            buff_data = recv(serial)
            buff_con = str(binascii.b2a_hex(buff_data))[20:22]
            if(buff_con == '00'):
                print("Record Successful")  
        else:
            print("Scan unsuccessful")

 
def exit():
  for i in range(len(keypad.ROW)):
    GPIO.setup( keypad.ROW[i],GPIO.IN,pull_up_down=GPIO.PUD_UP)
  for j in range(len( keypad.COLUMN)):
    GPIO.setup( keypad.COLUMN[j],GPIO.IN,pull_up_down=GPIO.PUD_UP)


# keypad
def rc522_write():
  text = input('New data:')
  print("write")
  reader.write(text)
  print("write success")

def rc522_read():
  id, text = reader.read()
  print(id)
  if id == 288092824153:
    print ('Password correct. Door open.')
    GPIO.output(LED,GPIO.LOW)
    time.sleep(5)
    GPIO.output(LED,GPIO.HIGH)

def Key_Deal():
    global door_order
    global door_input
    global error_count
    global p2
    key=None
    key=getkey()
    if not key==None:
        print ('You enter the key:',key)
        if key=='*': # confirm password
            if operator.eq(door_input,door_set)==True: # passcode correct
                print ('Password correct. Door open')
                p2.stop()
                GPIO.output(LED,GPIO.LOW)
                time.sleep(5)
                GPIO.output(LED,GPIO.HIGH)
                door_input=[]
                door_order=0
            else: # passcode incorrect
                print ('Password error. Door remain locked')
                if error_count<2:
                    error_count+=1
                    p = vlc.MediaPlayer("/home/pi/hello/incorrect.mp3") # play alarm
                    p.play()
                else:
                    error_count=0
                    p2.play()
                door_input=[]
                door_order=0
        else:    
            if door_order < 4:
                door_input.append(key)
                door_order=door_order+1

def job1():  # function for thread 1
  while True:
    Key_Deal()
    time.sleep(0.1)

def job2():  # function for thread 2
  while True:    
    finger_find()
    #finger_input()
    time.sleep(0.1)

def job3():  # function for thread 3
  while True:
    print("test3")
    rc522_read()
    time.sleep(0.1)


# main function
if __name__ == '__main__':
    print('Systerm start.')
    Signal_Init()
    reader = SimpleMFRC522()
    serial = serial.Serial('/dev/ttyUSB0', 57600, timeout=0.5)
    if serial.isOpen() :
        print("open success.")
    else :
        print("open failed.")

    thread1 = threading.Thread(target = job1, args = ())
    thread2 = threading.Thread(target = job2, args = ())
    thread3 = threading.Thread(target = job3, args = ())
    thread1.start()
    thread2.start()
    thread3.start()

    print('Systerm exit.')