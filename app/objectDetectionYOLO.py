"""
YOLO Code is adapted from:
https://docs.ultralytics.com/models/yolo11/#usage-examples
https://docs.ultralytics.com/modes/train/

"""
### Author: Edric Lay
### Date Created: 17/03/2025
############################################################################
### Library Imports
from ultralytics import YOLO
import numpy as np
import cv2 as cv
from result import Result
from PIL import Image

class ObjectDetectorYOLO():
    ############################
    # Values used for annotating on the image. Values taken from: 
    # https://colab.research.google.com/github/googlesamples/mediapipe/blob/main/examples/hand_landmarker/python/hand_landmarker.ipynb#scrollTo=s3E6NFV-00Qt&uniqifier=1
    MARGIN = 10  # pixels
    FONT_SIZE = 1
    FONT_THICKNESS = 1
    HANDEDNESS_TEXT_COLOR = (88, 205, 54) # vibrant green
    COLORS = {
    0: (203, 192, 255),  # Pink
    1: (255, 255, 0),    # Cyan
    2: (255, 0, 255),    # Magenta
    3: (0, 255, 255),    # Yellow
    4: (0, 165, 255),    # Orange
    5: (0, 255, 0),      # Green
    6: (0, 0, 255),      # Red
    7: (255, 0, 0),      # Blue
    8: (128, 0, 128),    # Purple
    9: (42, 42, 165)     # Brown
}
    ############################
    def __init__(self, modelPath: str = "runs/detect/train6/weights/best.pt"):
        """Used to create Object Detector 

        Args:
            modelPath (str): Path for the model
        """
        self.model = YOLO(model = modelPath, verbose=False)
        self.model.to('cpu')
        self.classNames = self.model.names

    ################################ Video Analysis ############################################ 
    def analyseVideo(self, videoName: str):
        """Perform a object detection analysis of a full video

        Args:
            videoName (str): File name of the video

        Returns:
            videoAnalysis (list): List of results of each frame analyzed
        """
        footage = cv.VideoCapture(videoName)
        videoAnalysis = []

        while True:
            try:
                ret, frame = footage.read()
                if ret:
                    timeStamp = footage.get(cv.CAP_PROP_POS_MSEC)
                    frameResult = self.detect(frame, timeStamp)
                    videoAnalysis.append(frameResult)

                if not ret or cv.waitKey(1) == ord('q'):
                    break
            except:
                break

        footage.release()

        return videoAnalysis
    
    def detect(self, frame, timeStamp):
        """Method used to detect all objects in a frame

        Args:
            frame: Frame in which we will be running the detector on
            timeStamp: Timestamp of frame
        
        Returns:
            result (Result): Result of the frame analyzed
        """
        result = self.model.predict(frame, verbose = False)
        return Result(timeStamp, result[0])
    
    ############################### Drawing Tools #############################################
    def updateSpecificItemFrames(self, resultList: list, itemName: str):
        """Updates the resultList frames to show a specific item tracking based off a list of results

        Args:
            result (List(Result)): List of Result objects created after analysing a video 
            itemName (str): Specific name of item being looked for

        Returns:
            videoName (str): Name of the video with annotations
            count (int): Number of times that item has been removed
        """
        prevItemFound = False
        count = 0

        for analysis in resultList:
            annotated_image, status = self.visualiseSpecificItem(analysis, itemName)
            analysis.frame = annotated_image
            curItemFound = status
            if curItemFound != True and prevItemFound != True:
                count += 1
                analysis.status = False

            prevItemFound = curItemFound

        return count        

    def visualiseSpecificItem(self, frame, analysis: Result, itemName: str):
        """ Annotates frame when a specific item is detected

        Args:
            analysis (Result): Result object which is a frame which has been analysed
            itemName (str): Specific name of item being looked for

        Returns:
            annotated_image: Image with specific item labelled
            found (bool): Status if item is found
        """
        annotated_image = frame
        result = analysis.result
        boxes = result.boxes
        cls = result.boxes.cls
        found = False
        size = 6
        thickness = 1
        color = (0,255,0)
        for i, box in enumerate(boxes.xyxy):  
            className = result[0].names[int(cls[i])]
            if className == itemName:
                found = True
                xB = int(box[2])
                xA = int(box[0])
                yB = int(box[3])
                yA = int(box[1])
                xMid = int((xA + xB)/2)
                yMid = int((yA + yB)/2)

                # Horizontal line
                cv.line(annotated_image, (xMid + size, yMid + size), (xMid - size, yMid - size), color, thickness)
                # Vertical line
                cv.line(annotated_image, (xMid + size, yMid - size), (xMid - size, yMid + size), color, thickness)
                cv.putText(annotated_image, className, (xA,yA), fontFace = cv.FONT_HERSHEY_COMPLEX, fontScale = 1, color = color)
        
        if found:
            cv.putText(annotated_image, f"Object Detection: {itemName} found",
            (0, 50), cv.FONT_HERSHEY_DUPLEX,
            ObjectDetectorYOLO.FONT_SIZE/2, (0,0,0), ObjectDetectorYOLO.FONT_THICKNESS, cv.LINE_AA)
        
        else:
            cv.putText(annotated_image, f"Object Detection: {itemName} not found",
            (0, 50), cv.FONT_HERSHEY_DUPLEX,
            ObjectDetectorYOLO.FONT_SIZE/2, (0,0,0), ObjectDetectorYOLO.FONT_THICKNESS, cv.LINE_AA)
        
        # cv.putText(annotated_image, f"Found {itemName}: {str(found)}",
        # (0, 50), cv.FONT_HERSHEY_DUPLEX,
        # ObjectDetectorYOLO.FONT_SIZE/2, ObjectDetectorYOLO.HANDEDNESS_TEXT_COLOR, ObjectDetectorYOLO.FONT_THICKNESS, cv.LINE_AA)

        return annotated_image, found

    def updateAllItemFrames(self, resultList: list):
        """Updates the resultList frames to show all items based off a list of results

        Args:
            result (List(Result)): List of Result objects created after analysing a video 

        Returns:
            videoName (str): Name of the video with annotations
        """

        for analysis in resultList:
            annotated_image, status = self.visualiseAll(analysis)
            analysis.frame = annotated_image

        return None        

    def visualiseAll(self, frame, analysis: Result):
        """ Annotates frame with all detected items

        Args:
            analysis (Result): Result object which is a frame which has been analysed

        Returns:
            annotated_image: Image with all known items labelled
        """
        annotated_image = np.copy(frame)
        result = analysis.result
        boxes = result.boxes
        cls = result.boxes.cls
        size = 6
        thickness = 2

        for i, box in enumerate(boxes.xyxy):  
            color = ObjectDetectorYOLO.COLORS[int(cls[i])]
            className = result[0].names[int(cls[i])]
            xB = int(box[2])
            xA = int(box[0])
            yB = int(box[3])
            yA = int(box[1])
            xMid = int((xA + xB)/2)
            yMid = int((yA + yB)/2)
            
            (text_width, text_height), _ = cv.getTextSize(className, cv.FONT_HERSHEY_DUPLEX, 0.5, thickness)
            textX = xMid - text_width // 2
            textY = yMid + text_height // 2
            cv.putText(annotated_image, className, (textX, textY - 3 * size), fontFace = cv.FONT_HERSHEY_COMPLEX, fontScale = 0.5, color = color) # add text so it centres on object


            # Add a crosshair into centre of detected object
            cv.line(annotated_image, (xMid + size, yMid), (xMid - size, yMid), color, thickness)
            cv.line(annotated_image, (xMid, yMid - size), (xMid, yMid + size), color, thickness)
            

        cv.putText(annotated_image, "Performing Object Detection",
        (0, 25), cv.FONT_HERSHEY_DUPLEX,
        ObjectDetectorYOLO.FONT_SIZE/2, (0,0,0), ObjectDetectorYOLO.FONT_THICKNESS, cv.LINE_AA)

        items = self.count(analysis)
        count = sum(items.values())

        cv.putText(annotated_image, f"Items found: {count}",
        (0, 50), cv.FONT_HERSHEY_DUPLEX,
        ObjectDetectorYOLO.FONT_SIZE/2, (0,0,0), ObjectDetectorYOLO.FONT_THICKNESS, cv.LINE_AA)

        return annotated_image, items, count

    #################################### Object Detection ########################################
    def count(self, analysis: Result):
        """ Get all classes detected and the amount of them

        Returns:
            countDict (dict): dictionary containing all present classes and the count of each
        """
        countDict = dict()
        detectedObjects = analysis.result.boxes.cls.numpy().astype(int) # get all classes as int

        for objectID in detectedObjects:
            className = self.classNames[objectID]
            if className in countDict:
                countDict[className] += 1
            else:
                countDict[className] = 1

        return countDict
    
    # def findItem(self,desiredObject: str):
    #     """Finds all instances of a desired object

    #     Args:
    #         desiredObject (str): Name of class we are looking for

    #     Returns:
    #         False, if desired object not in frame
    #         List of coordinates, if desired objects are present in frame
    #     """
    #     detectedObjects = self.result.boxes.cls.numpy().astype(int)
    #     foundObjects = np.where(detectedObjects == desiredObject)[0]
    #     if len(foundObjects) == 0:
    #         return False
    #     else:
    #         return self.result.boxes.xyxy.numpy()[foundObjects]
    #         # TODO: figure out how to return coordinates of all instances of specific object
    
    def checkCorrectItems(self, currentItems: dict, neededItems: dict) -> dict:
        """ Determines what items (and how many) are missing from the current frame

        Args:
            neededItems (dict): Dictionary of items needed with quantities

        Returns:
            missingItems (dict): Dictionary of missing items and quantities left need for them
        """
        missingItems = dict()
        for item in neededItems:
            try:
                currentAmount = currentItems[item]
                neededAmount = neededItems[item]
                if currentAmount < neededAmount:
                    missingItems[item] = neededAmount - currentAmount
            except:
                missingItems[item] = neededItems[item]

        return missingItems, bool(missingItems)

    def checkEmpty(self, resultList: list):
        """Checks to see when the frame is empty of consumables. Will return a list where elements represent the frames where it is empty.

        Returns:
            frameStamps: List(int)

        """
        frameStamps = []
        for index, analysis in enumerate(resultList):
            if len(analysis.result.boxes.cls) == 0:
                frameStamps.append(index)

        return frameStamps
    #################################### Report Saver ########################################

    def saveObjectLocations(self, frame, analysis: Result, folder: str):
        result = analysis.result
        boxes = result.boxes
        cls = result.boxes.cls
        size = 1
        thickness = 2
        blank = np.ones_like(frame, dtype=np.uint8)*255
        legendItems = set() # Only want to save unique items

        for i, box in enumerate(boxes.xyxy):  
            color = ObjectDetectorYOLO.COLORS[int(cls[i])]
            className = result[0].names[int(cls[i])]
            item = (color,className)
            xB = int(box[2])
            xA = int(box[0])
            yB = int(box[3])
            yA = int(box[1])
            xMid = int((xA + xB)/2)
            yMid = int((yA + yB)/2)
            
            # Add a crosshair into centre of detected object
            cv.line(blank, (xMid + size, yMid), (xMid - size, yMid), color, thickness)
            cv.line(blank, (xMid, yMid - size), (xMid, yMid + size), color, thickness)

            legendItems.add(item)

        # Adding legend
        legend_x, legend_y = 5, 10
        font_scale = 0.35
        line_height = 14  # Adjusted for smaller text

        for i, (color, name) in enumerate(legendItems):
            y = legend_y + i * line_height
            cv.rectangle(blank, (legend_x, y - 6), (legend_x + 10, y + 2), color, -1)
            cv.putText(blank, name, (legend_x + 18, y + 2), cv.FONT_HERSHEY_SIMPLEX, font_scale, color, 1, cv.LINE_AA)
            
        img = Image.fromarray(cv.copyMakeBorder(blank, 
                                                top=10, bottom=10, left=10, right=10, 
                                                borderType=cv.BORDER_CONSTANT, value=[0, 0, 0]))
        img.save(f'{folder}/process/2.png')

############################################################################

if __name__ == "__main__":
    testModel = ObjectDetectorYOLO()
    video = cv.VideoCapture(0)
    if not video.isOpened():
        print("Error opening camera")
    
    else:
        while True:
            ret, frame = video.read()        
            if ret:
                result = testModel.detect(frame, 0)
                testModel.saveObjectLocations(frame, result, "a")
                cv.imshow('frame', frame)
            
            if cv.waitKey(1) == ord('q'):
                break

    video.release()