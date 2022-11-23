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

#参考：https://blog.csdn.net/qq_44941069/article/details/123590351

Sys_Run=True
Test_Num=0
door_set=['1','2','3','4']
door_input=[]
door_order=0
error_count=0
p2 = vlc.MediaPlayer("/home/pi/hello/alarm.mp3") 

#
LED=5
def Signal_Init():
  GPIO.cleanup()
  GPIO.setmode(GPIO.BCM)
  GPIO.setup(LED,GPIO.OUT)
  GPIO.output(LED,GPIO.HIGH)  #LED灭

#矩阵键盘
class keypad(object):
  KEYPAD=[
    ['1','2','3','A'],
    ['4','5','6','B'],
    ['7','8','9','C'],
    ['*','0','#','D']]
 
  ROW    =[12,16,20,21]#行
  COLUMN =[6,13,19,26]#列
 
#初始化函数
def init_GPIO():
  GPIO.cleanup()
  GPIO.setmode(GPIO.BCM)
#取得键盘数函数
def getkey():
  GPIO.setmode(GPIO.BCM)
    #设置列输出低
  for i in range(len(keypad.COLUMN)):
    GPIO.setup(keypad.COLUMN[i],GPIO.OUT)
    GPIO.output(keypad.COLUMN[i],GPIO.LOW)
    #设置行为输入、上拉
  for j in range(len(keypad.ROW)):
    GPIO.setup(keypad.ROW[j],GPIO.IN,pull_up_down=GPIO.PUD_UP)
    #检测行是否有键按下，有则读取行值
  RowVal=-1
  for i in range(len(keypad.ROW)):
    RowStatus=GPIO.input(keypad.ROW[i])
    if RowStatus==GPIO.LOW:
       RowVal=i
       #print('RowVal=%s' % RowVal)
    #若无键按下,则退出，准备下一次扫描
  if RowVal<0 or RowVal>3:
    exit()
    return
 
    #若第RowVal行有键按下，跳过退出函数，对掉输入输出模式
    #第RowVal行输出高电平，
  GPIO.setup(keypad.ROW[RowVal],GPIO.OUT)
  GPIO.output(keypad.ROW[RowVal],GPIO.HIGH)
    #列为下拉输入
  for j in range(len(keypad.COLUMN)):
    GPIO.setup(keypad.COLUMN[j],GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
 
    #读取按键所在列值
  ColumnVal=-1
  for i in range(len(keypad.COLUMN)):
    ColumnStatus=GPIO.input(keypad.COLUMN[i])
    if ColumnStatus==GPIO.HIGH:
      ColumnVal=i
    #等待按键松开
      while GPIO.input(keypad.COLUMN[i])==GPIO.HIGH:
        time.sleep(0.05)
        #print ('ColumnVal=%s' % ColumnVal)
    #若无键按下，返回
  if ColumnVal<0 or ColumnVal>3:
    exit()
    return
 
  exit()
  return keypad.KEYPAD[RowVal][ColumnVal]
 

# volatile unsigned char FPM10A_RECEICE_BUFFER[32];        //定义接收缓存区
# code unsigned char FPM10A_Pack_Head[6] = {0xEF,0x01,0xFF,0xFF,0xFF,0xFF};  //协议包头
# code unsigned char FPM10A_Get_Img[6] = {0x01,0x00,0x03,0x01,0x00,0x05};    //获得指纹图像
# code unsigned char FPM10A_Img_To_Buffer1[7]={0x01,0x00,0x04,0x02,0x01,0x00,0x08}; //将图像放入到BUFFER1
# code unsigned char FPM10A_Search[11]={0x01,0x00,0x08,0x04,0x01,0x00,0x00,0x00,0x64,0x00,0x72}; //搜索指纹搜索范围0 - 999,使用BUFFER1中的特征码搜索

def recv(serial):
    while True:
        data = serial.read_all()
        if data == '':
            continue
        else:
            break
    return data

def finger_find():
    serch = 'EF 01 FF FF FF FF 01 00 08 04 01 00 00 00 64 00 72'
    serch = bytes.fromhex(serch)
    serial.write(serch)
    time.sleep(1)
    serch_data = recv(serial)
    print(serch_data)
    serch_con = str(binascii.b2a_hex(serch_data))[20:22]
    if (serch_con == '09'):
        print("指纹不匹配")
        return 0
    elif(serch_con == '00'):
        print("指纹匹配成功")   
        print ('password right! door open')
        GPIO.output(LED,GPIO.LOW)
        time.sleep(5)
        GPIO.output(LED,GPIO.HIGH)
        return 1 

def finger_input():
    a = 'EF 01 FF FF FF FF 01 00 03 01 00 05'  #获得指纹图像
    d = bytes.fromhex(a)
    serial.write(d)
    time.sleep(1)
    data =recv(serial)
    print(data)
    if data != b'' :
        data_con = str(binascii.b2a_hex(data))[20:22]
        if(data_con == '02'):
            print("请按下手指")
        elif(data_con == '00'):
            #print("载入成功")
            buff = 'EF 01 FF FF FF FF 01 00 04 02 01 00 08'  #将图像放入buffer
            buff = bytes.fromhex(buff)
            serial.write(buff)
            time.sleep(1)
            buff_data = recv(serial)
            buff_con = str(binascii.b2a_hex(buff_data))[20:22]
            if(buff_con == '00'):
                ##print("生成特征成功")
                print ('password right! door open')
                GPIO.output(LED,GPIO.LOW)
                time.sleep(5)
                GPIO.output(LED,GPIO.HIGH)
        else:
            print("不成功")

 
def exit():
  for i in range(len(keypad.ROW)):
    GPIO.setup( keypad.ROW[i],GPIO.IN,pull_up_down=GPIO.PUD_UP)
  for j in range(len( keypad.COLUMN)):
    GPIO.setup( keypad.COLUMN[j],GPIO.IN,pull_up_down=GPIO.PUD_UP)



#矩阵键盘
def rc522_write():
  text = input('New data:')
  print("write")
  reader.write(text)
  print("write success")

def rc522_read():
  id, text = reader.read()
  print(id)
  if id == 288092824153:
    print ('password right! door open')
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
        print ('You enter the  key:',key)
        if key=='*':  #确认密码
            if operator.eq(door_input,door_set)==True:
                print ('password right! door open')
                p2.stop()
                GPIO.output(LED,GPIO.LOW)
                time.sleep(5)
                GPIO.output(LED,GPIO.HIGH)
                door_input=[]
                door_order=0
            else:
                print ('password error! door close')
                if error_count<2:
                    error_count+=1
                    p = vlc.MediaPlayer("/home/pi/hello/incorrect.mp3") 
                    p.play()
                    #time.sleep(3)
                    #p.stop()
                else:
                    error_count=0
                    p2.play()
                door_input=[]
                door_order=0
        elif key=='A':  #写入RC522
            print ('RC522 Writing...')
            rc522_write()
        elif key=='B':  #录入指纹
            print ('Finger Writing...')
            finger_input()
        else:    
            if door_order < 4:
                door_input.append(key)
                door_order=door_order+1

def job1():
  while True:
    Key_Deal()
    time.sleep(0.1)

def job2():
  while True:    
    #finger_find()
    finger_input()
    time.sleep(0.1)

def job3():
  while True:
    print("test3")
    rc522_read()
    time.sleep(0.1)



#主函数
if __name__ == '__main__':
    print('Systerm start!')
    Signal_Init()
    reader = SimpleMFRC522()
    serial = serial.Serial('/dev/ttyUSB1', 57600, timeout=0.5)  #/dev/ttyUSB0
    if serial.isOpen() :
        print("open success")
    else :
        print("open failed")

    thread1 = threading.Thread(target = job1, args = ())
    thread2 = threading.Thread(target = job2, args = ())
    thread3 = threading.Thread(target = job3, args = ())
    thread1.start()
    thread2.start()
    thread3.start()

        
    print('Systerm exit!')


