# ECE434: Sauron - All Seeing Eye

## Introduction:

## Requirements:  


## Setup:  
### Models:
To download the DNN models that this project uses run:  
```
./download_models <model name>
```

With the name of the model you want to download from the following list:  
* inception -- Inception-SSD v2  
* mobilenet -- MobileNet-SSD v2  
* resnet -- Faster-RCNN ResNet50  
* caffe -- CaffeNet  
* all -- all of the above 

### IP Address setup:
First get the IP addresses of both the compute server and the SBC client. Note if these devices are not on the same local area network, the server must be globally port forwarded to allow for access over the network.  
Upon doing so, enter the server's IP address in eye.py for the value of server_ip. And similarily enter the SBC client's IP in tower.py for the value of client_ip.  

## Running:   

First on server run: 
```
./tower.py <model_name> <object to track>
```
Then on the SBC client:  
```
./eye.py
```



