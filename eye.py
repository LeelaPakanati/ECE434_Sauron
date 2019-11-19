#!/usr/bin/python3
"""
Simply display the contents of the webcam with optional mirroring using OpenCV 
via the new Pythonic cv2 interface.  Press <esc> to quit.
"""

import os
import time
from simple_pid import PID
import numpy as np
print("--> Loading OpenCV module")
from cv2 import VideoCapture, imencode, imdecode, IMREAD_COLOR, imshow, destroyAllWindows, waitKey, resize
print("--> OpenCV modules loaded")
import io
import socket
import struct
import argparse
import wiringpi2 as wiringpi
from multiprocessing import Process, Queue

#resolution = (640, 480)
resolution = (300, 300)

# setup servos
xPin = 13
yPin = 18

wiringpi.wiringPiSetupGpio()

# enable PWM0                                                                 
wiringpi.pinMode(18,2)
wiringpi.pwmSetMode(0)
wiringpi.pwmSetClock(400)
wiringpi.pwmSetRange(1024)
wiringpi.pwmWrite(18, 0)

# enable PWM1                                                                 
wiringpi.pinMode(13,2)
wiringpi.pwmSetMode(0)
wiringpi.pwmSetClock(400)
wiringpi.pwmSetRange(1024)
wiringpi.pwmWrite(13, 0)


img_file = "./img.jpg"
img_ready_file = "./img_ready"
err_file = "./error_val"

server_ip = '137.112.156.222'

P = (.70, .15)
I = (0.05, 0.03)
D = (-0.0005, -0.0005)

pid = (PID(P[0], I[0], D[0], setpoint=resolution[0]/2), PID(P[1], I[1], D[1], setpoint=resolution[1]/2))
#pid = (PID(P[0], I[0], D[0], setpoint=320), PID(P[1], I[1], D[1], setpoint=240))

def control_servos(q):
    maxdX = 1
    control_x = 60
    control_y = 53

    posX = resolution[0]/2
    posY = resolution[1]/2

    while True:
        start_t = time.time()
        
        posX, posY = q.get(True)
        if posX == 'Q':
            break

        target_x = int(pid[0](posX)) + 60
        target_y = int(pid[1](posY)) + 53

        if control_x<target_x:
            control_x += maxdX
        elif control_x>target_x:
            control_x -= maxdX

        if control_y<target_y:
            control_y += maxdX
        elif control_y>target_y:
            control_y -= maxdX

        if control_x > 95:
            control_x = 95
        if control_x < 25:
            control_x = 25

        if control_y > 80:
            control_y = 80
        if control_y < 36:
            control_y = 36
        #print(target_x, ", ", target_y, " : ", control_x, ", ", control_y)
        wiringpi.pwmWrite(xPin, control_x)
        wiringpi.pwmWrite(yPin, control_y)


def show_webcam(q, port):
    print('Streaming webcam to file')
    cam = VideoCapture(0)

    #send image
    client_socket = socket.socket()
    client_socket.connect((server_ip, port))
    image_connection = client_socket.makefile('wb')

    #receive error
    server_socket = socket.socket()
    server_socket.bind(('0.0.0.0', 9000))
    server_socket.listen(0)
    control_connection = server_socket.accept()[0].makefile('rb')

    wiringpi.pwmWrite(xPin, 60)
    wiringpi.pwmWrite(yPin, 53)

    try:
        print("starting stream")
        posX = resolution[0]/2
        posY = resolution[1]/2

        while True:
            #start_t = time.time()
            ret_val, image = cam.read()

            image_send = resize(image, resolution)

            img_buf = imencode('.jpg', image_send)[1]

            image_connection.write(struct.pack('<L', len(img_buf)))
            image_connection.flush()
            image_connection.write(img_buf)

            posX = struct.unpack('<i', control_connection.read(struct.calcsize('<i')))[0]
            posY = struct.unpack('<i', control_connection.read(struct.calcsize('<i')))[0]

            q.put((posX, posY))
            #control_servos(posX, posY)

            image_len = struct.unpack('<L', control_connection.read(struct.calcsize('<L')))[0]
            if not image_len:
                break

            read_buf = control_connection.read(image_len)
            image = imdecode(np.frombuffer(read_buf, dtype=np.uint8), IMREAD_COLOR)
            imshow('image', image)

            #end_t = time.time()
            #print("time = ", end_t - start_t)

            if waitKey(1) == 27: 
                break  # esc to quit

        image_connection.write(struct.pack('<i', 0))

    finally:
        print("Closing socket")
        image_connection.close()
        client_socket.close()

        control_connection.close()
        server_socket.close()
        q.put(('Q', 'Q'))

        wiringpi.pwmWrite(xPin, 0)
        wiringpi.pwmWrite(yPin, 0)

    destroyAllWindows()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('port', type=int)
    args = parser.parse_args()
    q = Queue()
    Process(target=show_webcam, args=(q,args.port,)).start()
    Process(target=control_servos, args=(q,)).start()

if __name__ == '__main__':
    main()
