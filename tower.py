#!/usr/bin/python3
"""
Simply display the contents of the webcam with optional mirroring using OpenCV 
via the new Pythonic cv2 interface.  Press <esc> to quit.
"""
import os
import cv2
import time
import argparse
import io
import socket
import struct
import numpy as np

# Pretrained classes in the model
classNames = {0: 'background',
              1: 'person', 2: 'bicycle', 3: 'car', 4: 'motorcycle', 5: 'airplane', 6: 'bus',
              7: 'train', 8: 'truck', 9: 'boat', 10: 'traffic light', 11: 'fire hydrant',
              13: 'stop sign', 14: 'parking meter', 15: 'bench', 16: 'bird', 17: 'cat',
              18: 'dog', 19: 'horse', 20: 'sheep', 21: 'cow', 22: 'elephant', 23: 'bear',
              24: 'zebra', 25: 'giraffe', 27: 'backpack', 28: 'umbrella', 31: 'handbag',
              32: 'tie', 33: 'suitcase', 34: 'frisbee', 35: 'skis', 36: 'snowboard',
              37: 'ball', 38: 'kite', 39: 'baseball bat', 40: 'baseball glove',
              41: 'skateboard', 42: 'surfboard', 43: 'tennis racket', 44: 'bottle',
              46: 'wine glass', 47: 'cup', 48: 'fork', 49: 'knife', 50: 'spoon',
              51: 'bowl', 52: 'banana', 53: 'apple', 54: 'sandwich', 55: 'orange',
              56: 'broccoli', 57: 'carrot', 58: 'hot dog', 59: 'pizza', 60: 'donut',
              61: 'cake', 62: 'chair', 63: 'couch', 64: 'potted plant', 65: 'bed',
              67: 'dining table', 70: 'toilet', 72: 'tv', 73: 'laptop', 74: 'mouse',
              75: 'remote', 76: 'keyboard', 77: 'cellphone', 78: 'microwave', 79: 'oven',
              80: 'toaster', 81: 'sink', 82: 'refrigerator', 84: 'book', 85: 'clock',
              86: 'vase', 87: 'scissors', 88: 'teddy bear', 89: 'hair drier', 90: 'toothbrush'}


def id_class_name(class_id, classes):
    for key, value in classes.items():
        if class_id == key:
            return value

client_ip = '137.112.101.245'

resolution = (300, 300)
#resolution = (640, 480)


def show_webcam(model, desired_obj):
    if model == 'caffe':
        model = cv2.dnn.readNetFromCaffe('models/MobileNetSSD_deploy.prototxt.txt', 'models/MobileNetSSD_deploy.caffemodel')

    elif model == 'resnet':
        model = cv2.dnn.readNetFromTensorflow('models/frozen_inference_graph_resnet.pb',
                                              'models/faster_rcnn_resnet50_coco_2018_01_28.pbtxt')
    elif model == 'mobilenet':
        model = cv2.dnn.readNetFromTensorflow('models/frozen_inference_graph_mobilenet.pb',
                                              'models/ssd_mobilenet_v2_coco_2018_03_29.pbtxt')
    elif model == 'inception':
        model = cv2.dnn.readNetFromTensorflow('models/frozen_inference_graph_inception.pb',
                                              'models/ssd_inception_v2_coco_2017_11_17.pbtxt')
    else:
        print("Invalid model")
        return

    print("--> Model Loaded")

    if desired_obj not in classNames.values():
        print("Invalid object")
        return
    
    from_tracker_socket = socket.socket()
    from_tracker_socket.bind(('0.0.0.0', 5000))
    from_tracker_socket.listen(0)
    from_tracker = from_tracker_socket.accept()[0].makefile('rb')
    print("image connection made")

    time.sleep(1)

    to_tracker_socket = socket.socket()
    to_tracker_socket.connect((client_ip, 9000))
    to_tracker = to_tracker_socket.makefile('wb')
    image_center = (int(resolution[0]/2), int(resolution[1]/2))
    box_center = image_center

    try:
        while True:
            # Read the length of the image as a 32-bit unsigned int. If the
            # length is zero, quit the loop
            start_t = time.time()

            image_len = struct.unpack('<L', from_tracker.read(struct.calcsize('<L')))[0]
            if not image_len:
                break

            read_buf = from_tracker.read(image_len)

            image = cv2.imdecode(np.frombuffer(read_buf, dtype=np.uint8), cv2.IMREAD_COLOR)
            image = cv2.flip(image, 1)

            #image = cv2.resize(image, resolution)
            
            image_height, image_width, _d = image.shape

            model.setInput(cv2.dnn.blobFromImage(image, size=(300, 300), swapRB=True))
            output = model.forward()

            desired_objs = []
            desired_objs_confidences = []
            for detection in output[0, 0, :, :]:
                class_id = detection[1]
                # find people
                confidence = detection[2]
                if confidence > .55:
                    class_name=id_class_name(class_id,classNames)
                    box_x = detection[3] * image_width
                    box_y = detection[4] * image_height
                    box_width = detection[5] * image_width
                    box_height = detection[6] * image_height
                    cv2.rectangle(image, (int(box_x), int(box_y)), (int(box_width), int(box_height)), (255, 255, 0), thickness=1)

                    cv2.putText(image,class_name ,(int(box_x), int(box_y+.05*image_height)),cv2.FONT_HERSHEY_SIMPLEX,(.01*image_width*(confidence-.55)+.0005),(0, 0, 255))
                    if class_name == desired_obj:
                        desired_objs.append(detection)
                        desired_objs_confidences.append(confidence)


            if(desired_objs_confidences):
                best_obj = desired_objs[desired_objs_confidences.index(max(desired_objs_confidences))]
                box_x = best_obj[3] * image_width
                box_y = best_obj[4] * image_height
                box_width = best_obj[5] * image_width
                box_height = best_obj[6] * image_height
                #if box_y <= 5:
                #    box_y = -10
                box_center = (int((box_x + box_width)/2) ,int(1*(box_y + box_height)/2))
                cv2.line(image, image_center, box_center, (0,255,0), 2)


            
            to_tracker.write(struct.pack('<i', box_center[0]))
            to_tracker.flush()
            to_tracker.write(struct.pack('<i', box_center[1]))
            to_tracker.flush()
            #print(str(box_center[0]), ", ", str(box_center[1]))

            #cv2.imshow('image', image)

            img_buf = cv2.imencode('.jpg', image)[1]
            to_tracker.write(struct.pack('<L', len(img_buf)))
            to_tracker.flush()
            to_tracker.write(img_buf)
            to_tracker.flush()
            
            if cv2.waitKey(1) == 27: 
                break  # esc to quit
        to_tracker.write(struct.pack('<i', 0))
    finally:
        print("Closing socket")
        from_tracker.close()
        from_tracker_socket.close()

        to_tracker.close()
        to_tracker_socket.close()

    cv2.destroyAllWindows()
            

def main():
    parser = argparse.ArgumentParser(description='Enter the model to use and the object to detect.')
    parser.add_argument('model')
    parser.add_argument('object')
    args = parser.parse_args()
    show_webcam(args.model, args.object)


if __name__ == '__main__':
    main()
