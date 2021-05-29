from numpy.core.arrayprint import str_format
from telegram import frames
import cv2
import mediapipe as mp
import time
import math
import pickle


class poseDetector():

    def __init__(self, mode=False, upBody=False, smooth=True,
                 detectionCon=0.7, trackCon=0.7):

        self.mode = mode
        self.upBody = upBody
        self.smooth = smooth
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        self.mpDraw = mp.solutions.drawing_utils
        self.mpPose = mp.solutions.pose
        self.pose = self.mpPose.Pose(self.mode, self.upBody, self.smooth,
                                     self.detectionCon, self.trackCon)

    def findPose(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.pose.process(imgRGB)
        if self.results.pose_landmarks:
            print(self.results.pose_landmarks)
            with open("Outfile.txt","w") as fp:
                fp.write(str_format(self.results.pose_landmarks))
            if draw:
                self.mpDraw.draw_landmarks(img, self.results.pose_landmarks,
                                           self.mpPose.POSE_CONNECTIONS)
        return img

    def findPosition(self, img, draw=True):
        self.lmList = []
        if self.results.pose_landmarks:
            for id, lm in enumerate(self.results.pose_landmarks.landmark):
                h, w, c = img.shape
                # print(id, lm)
                cx, cy = int(lm.x * w), int(lm.y * h)
                self.lmList.append([id, cx, cy])
                if draw:
                    cv2.circle(img, (cx, cy), 5, (255, 0, 0), cv2.FILLED)
        return self.lmList

    def findAngle(self, img, p1, p2, p3, draw=True):

        # Get the landmarks
        x1, y1 = self.lmList[p1][1:]
        x2, y2 = self.lmList[p2][1:]
        x3, y3 = self.lmList[p3][1:]

        # Calculate the Angle
        angle = math.degrees(math.atan2(y3 - y2, x3 - x2) -
                             math.atan2(y1 - y2, x1 - x2))
        if angle < 0:
            angle += 360

        # print(angle)

        # Draw
        if draw:
            cv2.line(img, (x1, y1), (x2, y2), (255, 255, 255), 3)
            cv2.line(img, (x3, y3), (x2, y2), (255, 255, 255), 3)
            cv2.circle(img, (x1, y1), 10, (0, 0, 255), cv2.FILLED)
            cv2.circle(img, (x1, y1), 15, (0, 0, 255), 2)
            cv2.circle(img, (x2, y2), 10, (0, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), 15, (0, 0, 255), 2)
            cv2.circle(img, (x3, y3), 10, (0, 0, 255), cv2.FILLED)
            cv2.circle(img, (x3, y3), 15, (0, 0, 255), 2)
            cv2.putText(img, str(int(angle)), (x2 - 50, y2 + 50),
                        cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)
        return angle

    def relative(self,lists,filename):
        with open(filename,"wb") as fp:
            pickle.dump(lists,fp)

    def difference(self,frame1,frame2):
        diff=[]
        for i,each in enumerate(frame1):
            diff.append([each[0],frame2[i][1]-each[1],frame2[i][2]-each[2]])
        return diff
    
    def encode(self,frame):
        val=[]
        normalizex=frame[12][1]-frame[11][1]
        normalizey=frame[12][2]-frame[11][2]
        for i,point in frame:
            val.append([point[0],(point[1]-frame[12][1])/normalizex,(point[2]-frame[12][1])/normalizey])
        return val

    def encoder(self,lists):
        val=[]
        for list in lists:
            val.append(self.encode(list))
        return val

    def gesture(self,inname,outfile):
        with open(inname,"rb") as fp:
            lists=pickle.load(fp)
        fp.close

        diff=[]
        for i,frame in enumerate(lists[1:]):
            diffframe=[]
            for points in frame:
                diffframe.append([points[0],lists[i-1][points[0]][1]-points[1],lists[i-1][points[0]][2]-points[2]])
            diff.append(diffframe)
        with open(outfile,"wb") as fp:
            pickle.dump(diff,fp)

def main():
    cap = cv2.VideoCapture(0)
    pTime = 0
    detector = poseDetector()
    lists=[]
    try:
        while True:
            success, img = cap.read()
            img = detector.findPose(img)
            lmList = detector.findPosition(img, draw=False)
            if len(lmList) != 0:
                print(lmList[14])
                cv2.circle(img, (lmList[14][1], lmList[14][2]), 15, (0, 0, 255), cv2.FILLED)
                lists.append(lmList)
            cTime = time.time()
            fps = 1 / (cTime - pTime)
            pTime = cTime

            cv2.putText(img, str(int(fps)), (70, 50), cv2.FONT_HERSHEY_PLAIN, 3,
                        (255, 0, 0), 3)

            cv2.imshow("Image", img)
            cv2.waitKey(1)
    finally:
        detector.relative(lists,"poses.txt")


if __name__ == "__main__":
    main()