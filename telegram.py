from contextlib import suppress
from numpy.core.fromnumeric import reshape
import telepot
import time
from telepot.loop import MessageLoop
import signal
import cv2
import os
from multiprocessing import Pool,Process,shared_memory,Array
from contextlib import suppress
import face_recognition
import imutils
import pickle
from contextlib import suppress
import ctypes
import numpy as np
from stream import stream

#Inter-process communication data
peoples=[] 
counter=[0,0]
camprocess=Array('i',[0,0,0,0,0,0])
streamprocess=Array('i',[0,0,0,0,0,0])

#For sharing the frames between this and streaming program
width  = cv2.VideoCapture(0).get(cv2.CAP_PROP_FRAME_WIDTH)   # float `width`
height = cv2.VideoCapture(0).get(cv2.CAP_PROP_FRAME_HEIGHT)  # float `height`
shape=(int(height),int(width),3)
framelist=Array(ctypes.c_uint8, shape[0] * shape[1] * shape[2], lock=False)
b=np.frombuffer(framelist,dtype=ctypes.c_uint8)
b=b.reshape(shape)

#For Port Forwarding
tunnel=Array(ctypes.c_wchar_p,1)

def frames(streamprocess,framelist):
    try:
        peoples=[]
        facesfound=[]
        start_time=time.time()
        #find path of xml file containing haarcascade file 
        cascPathface = os.path.dirname(
        cv2.__file__) + "/data/haarcascade_frontalface_alt2.xml"
        # load the harcaascade in the cascade classifier
        faceCascade = cv2.CascadeClassifier(cascPathface)

        cascPathbody = os.path.dirname(
        cv2.__file__) + "/data/haarcascade_upperbody.xml"
        bodyCascade = cv2.CascadeClassifier(cascPathbody)

        # load the known faces and embeddings saved in last file
        data = pickle.loads(open('face_enc', "rb").read())


        print("Streaming started")
        fourcc = cv2.VideoWriter_fourcc(*'MP4V')
        video_capture = cv2.VideoCapture(0)
        out = cv2.VideoWriter("Output.mp4", fourcc,20,(640,480))

        # loop over frames from the video file stream

        while True:
            # grab the frame from the threaded video stream
            if(time.time()-start_time>=50000):
                peoples=[]
                facesfound=[]
            ret, frame = video_capture.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = faceCascade.detectMultiScale(gray,
                                                scaleFactor=1.1,
                                                minNeighbors=5,
                                                minSize=(30, 30),
                                                flags=cv2.CASCADE_SCALE_IMAGE)
            if ret:
                b[:]=frame
            # convert the input frame from BGR to RGB 
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # the facial embeddings for face in input
            encodings = face_recognition.face_encodings(rgb)
            names = []
            # loop over the facial embeddings incase
            # we have multiple embeddings for multiple fcaes
            for encoding in encodings:
            #Compare encodings with encodings in data["encodings"]
            #Matches contain array with boolean values and True for the embeddings it matches closely
            #and False for rest
                matches = face_recognition.compare_faces(data["encodings"],
                encoding)
                #set name =inknown if no encoding matches
                name = "Unknown"
                # check to see if we have found a match
                if True in matches:
                    #Find positions at which we get True and store them
                    matchedIdxs = [i for (i, b) in enumerate(matches) if b]
                    counts = {}
                    # loop over the matched indexes and maintain a count for
                    # each recognized face face
                    for i in matchedIdxs:
                        #Check the names at respective indexes we stored in matchedIdxs
                        name = data["names"][i]
                        #increase count for the name we got
                        counts[name] = counts.get(name, 0) + 1
                    #set name which has highest count
                    name = max(counts, key=counts.get)


                # update the list of names
                names.append(name)
                if(len(facesfound)==0 and len(names)>len(facesfound)):
                    for i in names:
                        if(i not in peoples and i=="Unknown"):
                            facesfound.append(i)

                # loop over the recognized faces
                if(name!="Unknown" and (name not in [i[0] for i in peoples])):
                    #out.write(frame)
                    #telegram.sendNotification(name+" has entered the room .")
                    peoples.append([name,1])
                    facesfound.pop(0) if len(facesfound)>0 else 0
                    sendNotification(name+" has entered the room")
                    print(name+" has entered the room")

                for ((x, y, w, h), name) in zip(faces, names):
                    # rescale the face coordinates
                    # draw the predicted face name on the image
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(frame, name, (x, y), cv2.FONT_HERSHEY_SIMPLEX,
                    0.75, (0, 255, 0), 2)

            if(len(facesfound)>0):
                if(counter[0]<len(facesfound)):
                    if(len(facesfound)==1):
                        sendNotification("1 person has entered the room")
                        counter[1]=time.time()

                    else:
                        sendNotification(str(len(facesfound))+" have entered the room")
                        counter[1]=time.time()
                    counter[0]+=len(facesfound)
                if((time.time()-counter[1])>=10 and list(streamprocess)==[0 for i in streamprocess]):
                    print("Stream has started")
                    Process(target=startstream,args=(streamprocess,framelist,tunnel,)).start()
                    #sendalarm()
            cv2.imshow("Frame", frame)


            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        video_capture.release()
        cv2.destroyAllWindows()
    except:
        pass

def startstream(streamprocess,framelist,tunnel):
    i=0
    while(streamprocess[i]!=0):
        i+=1
    if(i==len(streamprocess)):
        print("Overflow of processes")
        exit()
    streamprocess[i]=os.getpid()
    # os.system("python3 stream.py")
    stream(framelist,tunnel)
    sendNotification(tunnel)



API='Your-Bot-API-Key'


motion = 0
motionNew = 0
with suppress(Exception): 
    def handle(msg):
        global telegramText
        global chat_id
        global camstatus
        chat_id = msg['chat']['id']
        telegramText = msg['text']
        camstatus=0
        
        if(chat_id!=634824276):
            bot.sendMessage(chat_id, "Sorry this is a personal bot. Access Denied!")
            exit(1) 

        print('Message received from ' + str(chat_id))
    
        if (telegramText == '/start' or telegramText == '/help'):
            bot.sendMessage(chat_id, 'Hello I am your Intrusion Detection Bot. \nPlease type "/startcam" to start the surveillance process ')

        if telegramText == '/startcam':
            if(camstatus==0 and list(camprocess)==[0 for i in camprocess]):
                bot.sendMessage(chat_id, 'Security camera is activated. \nType "/stopcam" to stop surveillance. ')
                Process(target=main,args=(camprocess,streamprocess,framelist,)).start()
                camstatus=1
            else:
                bot.sendMessage(chat_id, 'Already surveillance is running .')
        
        if telegramText == "/chatid":
            bot.sendMessage(chat_id, 'Security camera is activated. \nType "/stopcam" to stop surveillance. ')
            sendNotification("hello")

        if(telegramText == '/camstatus'):
            if(camstatus==1):
                bot.sendMessage(chat_id, 'Already surveillance is running .')   
            else:
                bot.sendMessage(chat_id, 'Surveillance is stopped \nPlease type "/startcam" to start the surveillance process .')

        if(telegramText == '/startstream'):
            if(list(streamprocess)!=[0 for i in streamprocess]):
                sendNotification("Already streaming")
            else:
                Process(target=startstream,args=(streamprocess,framelist,tunnel,)).start()

        if(telegramText == '/stopstream'):
            if(list(streamprocess)==[0 for i in streamprocess]):
                sendNotification("Already stopped")
            else:
                for i in range(len(streamprocess)):
                    if(streamprocess[i]!=0):
                        os.kill(streamprocess[i],signal.SIGTERM)
                        streamprocess[i]=0
                        os.system("pkill -f stream.py")
        
        if(telegramText == '/stopcam'):
            bot.sendMessage(chat_id, 'Security camera is Deactivated.')
            for i in range(len(camprocess)):
                if(camprocess[i]!=0):
                    os.kill(camprocess[i],signal.SIGTERM)
                    camprocess[i]=0
            for i in range(len(streamprocess)):
                if(streamprocess[i]!=0):
                    os.kill(streamprocess[i],signal.SIGTERM)
                    streamprocess[i]=0
                    os.system("pkill -f stream.py")
            camstatus=0
        
            

     

    def main(camprocess,streamprocess,framelist):
        i=0
        while(camprocess[i]!=0):
            i+=1
        if(i==len(camprocess)):
            print("Overflow of processes")
            exit()
        camprocess[i]=os.getpid()
        sendNotification("Inside frames")
        sendNotification(' '.join(map(str,camprocess)))
        frames(streamprocess,framelist)



    def sendNotification(message):  
        global chat_id
        #bot.sendVideo(chat_id, video = open('output.mp4', 'rb'))
        bot.sendMessage(chat_id, message)

    if __name__== "__main__":

        bot = telepot.Bot(API)
        bot.setWebhook()
        bot.message_loop(handle)   
        while 1:
            time.sleep(10)

