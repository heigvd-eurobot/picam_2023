##########################################################
#                   CAKE DETECTOR                        #
##########################################################
import numpy as np
import matplotlib.pyplot as plt
import cv2
from cv2 import aruco
import imutils
from skimage import color, measure, morphology, feature, filters

class CakeDetector:
    """
    Class for detecting cake on table

    Attributes
    ----------
    resolutionData : list
        resolution of camera
    size_of_marker : float
        size of arucoTag of table in meter
    offset_x : int
        offset of reconstruct frame in x
    warpMatrix : list
        matrix for perspective transformation
    f : float
        factor for resize frame
    pink : list
        pink tresholded frame
    yellow : list
        yellow tresholded frame
    brown : list
        brown tresholded frame
    y_pos : list
        position of yellow arucoTag
    p_pos : list
        position of pink arucoTag
    b_pos : list
        position of brown arucoTag
    frame : list
        frame for detection

    Methods
    -------
    initPerspective(frame)
        initialize perspective of frame
    tresh(frame)
        treshold frame
    detectCake()
        detect cake on table
    """
    def __init__(self):
        """
        Init the class
        """
        self.resolutionData = [1920, 1080]
        self.size_of_marker = 0.1  # size of arucoTag of table in meter
        self.offset_x = 100  # offset of reconstruct frame in x
        self.offset_y = 100  # offset of reconstruct frame in x
        self.table_size_x = 3000 + self.offset_x  # size of table in x
        self.table_size_y = 2000 + self.offset_y  # size of table in y
        self.f = 0.25 # factor for resize frame

        self.warpMatrix = []
        self.pink = []
        self.yellow = []
        self.brown = []
        self.y_pos = []
        self.p_pos = []
        self.b_pos = []
        self.posCenter = []
        self.posGround = []
        self.cakeLayer = []
        self.frame_x = self.table_size_x * self.f
        self.frame_y = self.table_size_y * self.f
        self.frame = []
        self.initialized = False

        # self.parameters =  aruco.DetectorParameters_create()
        # self.parameters.adaptiveThreshWinSizeMin = 10
        # self.parameters.adaptiveThreshWinSizeMax = 21
        # self.parameters.adaptiveThreshWinSizeStep=1
        pass

    def initDetector(self, frame):
        """
        This method will initiate the perspective.

        Attributes
        ----------
        frame : list
            frame used for calibration

        """
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        grayFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Aruco detection
        try:
            dictionary = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
            parameters = aruco.DetectorParameters()
            detector = aruco.ArucoDetector(dictionary, parameters)
            markerCorners, markerIds, rejectedCandidates = detector.detectMarkers(
                grayFrame
            )

            # Subpixel refinement
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.0001)
            for corner in markerCorners:
                cv2.cornerSubPix(
                    grayFrame,
                    corner,
                    winSize=(3, 3),
                    zeroZone=(-1, -1),
                    criteria=criteria,
                )

            # Draw detected markers
            ar = np.array(markerCorners)

            # Corner extern of referenc arucoTag
            a0 = ar[markerIds == 20, 0, 0]
            a1 = ar[markerIds == 20, 0, 1]
            b0 = ar[markerIds == 21, 1, 0]
            b1 = ar[markerIds == 21, 1, 1]
            c0 = ar[markerIds == 22, 3, 0]
            c1 = ar[markerIds == 22, 3, 1]
            d0 = ar[markerIds == 23, 2, 0]
            d1 = ar[markerIds == 23, 2, 1]

            # Perspective transformation
            pts1 = np.float32([[a0, a1], [b0, b1], [c0, c1], [d0, d1]])
            pts2 = np.float32(
                [
                    [(1480 + 50) * self.f, (2475 + self.offset_x) * self.f],
                    [(520 + 50) * self.f, (2475 + self.offset_x) * self.f],
                    [(1480 + 50) * self.f, (525 + self.offset_x) * self.f],
                    [(520 + 50) * self.f, (525 + self.offset_x) * self.f],
                ]
            )

            matrix = cv2.getPerspectiveTransform(pts1, pts2)
            self.warpMatrix = matrix
            frame = cv2.warpPerspective(
                frame, matrix, (int(2000 * self.f), int(3100 * self.f))
            )

            # split image 3x2
            splitx = 3
            splity = 2
            marge = 100

            (w, h, p) = frame.shape
            offsetx = int(w / splitx)
            offsety = int(h / splity)

            # Aruco detection
            dictionary = aruco.getPredefinedDictionary(aruco.DICT_4X4_250)
            parameters = aruco.DetectorParameters()
            detector = aruco.ArucoDetector(dictionary, parameters)

            pos = []
            for i in range(splitx):
                for j in range(splity):
                    cutframe = frame[
                        i * offsetx : min((i + 1) * offsetx + marge, w),
                        j * offsety : min((j + 1) * offsety + marge, h),
                        :,
                    ]
                    try:
                        (
                            markerCorners,
                            markerIds,
                            rejectedCandidates,
                        ) = detector.detectMarkers(cutframe)
                        for k in range(len(markerIds)):
                            c = markerCorners[k][0]
                            pos.append(
                                [
                                    markerIds[k, 0],
                                    c[:, 0].mean() + j * offsety,
                                    c[:, 1].mean() + i * offsetx,
                                ]
                            )
                    except:
                        print(f"no marker found at {i} {j}")
                        pass
        except Exception as e:
            print(e)
            return
        self.initialized = True

    def detectAruco(self, frame):
        """
        This method will treshold the frame.

        Attributes
        ----------
        frame : list
            frame used for tresholding
        """
        if not self.initialized:
            return

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.warpPerspective(
            frame, self.warpMatrix, (int(2000 * self.f), int(3100 * self.f))
        )
        ksize = (int(10 * self.f), int(10 * self.f))
        self.frame = frame.copy()
        frameB = cv2.blur(frame, ksize)
        frameHSV = cv2.cvtColor(frameB, cv2.COLOR_RGB2HSV)

        self.yellow = cv2.inRange(frameHSV, (15, 100, 20), (30, 255, 255))
        self.pink = cv2.inRange(frameHSV, (120, 50, 0), (180, 150, 255))
        self.brown = cv2.inRange(frameHSV, (0, 30, 0), (15, 80, 100))

        kernel = np.ones((int(10 * self.f), int(60 * self.f)), np.uint8)
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (int(60 * self.f), int(60 * self.f))
        )
        self.pink = cv2.morphologyEx(self.pink, cv2.MORPH_CLOSE, kernel)
        self.yellow = cv2.morphologyEx(self.yellow, cv2.MORPH_CLOSE, kernel)
        self.brown = cv2.morphologyEx(self.brown, cv2.MORPH_CLOSE, kernel)
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (int(90 * self.f), int(90 * self.f))
        )
        self.pink = cv2.morphologyEx(self.pink, cv2.MORPH_OPEN, kernel)
        self.yellow = cv2.morphologyEx(self.yellow, cv2.MORPH_OPEN, kernel)
        self.brown = cv2.morphologyEx(self.brown, cv2.MORPH_OPEN, kernel)

        frame_YBP = cv2.bitwise_or(self.yellow, self.brown)
        frame_YBP = cv2.bitwise_or(frame_YBP, self.pink)

    def labeltruc(self):
        """
        This method will label the tresholded frame.
        """

        self.y_pos = []
        self.p_pos = []
        self.b_pos = []

        label_img = measure.label(self.yellow)
        regions = measure.regionprops(label_img)
        for k, prop in enumerate(regions):
            if prop.area > 1600 or prop.area < 450:
                label_img[label_img == k + 1] = 0
            else:
                self.y_pos.append(prop.centroid)
        self.y_pos = np.array(self.y_pos)

        label_img = measure.label(self.pink)
        regions = measure.regionprops(label_img)
        for k, prop in enumerate(regions):
            if prop.area > 1600 or prop.area < 450:
                label_img[label_img == k + 1] = 0
            else:
                self.p_pos.append(prop.centroid)
        self.p_pos = np.array(self.p_pos)

        label_img = measure.label(self.brown)
        regions = measure.regionprops(label_img)
        for k, prop in enumerate(regions):
            if prop.area > 1600 or prop.area < 450:
                label_img[label_img == k + 1] = 0
            else:
                self.b_pos.append(prop.centroid)
        self.b_pos = np.array(self.b_pos)

        y = self.y_pos.copy()
        y[:, 0] = np.round((3000 - y[:, 0] / 0.25 - 100) / 1000, 3)
        y[:, 1] = np.round((2000 - y[:, 1] / 0.25) / 1000, 3)
        b = self.b_pos.copy()
        b[:, 0] = np.round((3000 - b[:, 0] / 0.25 - 100) / 1000, 3)
        b[:, 1] = np.round((2000 - b[:, 1] / 0.25) / 1000, 3)

        p = self.p_pos.copy()
        p[:, 0] = np.round((3000 - p[:, 0] / 0.25 - 100) / 1000, 3)
        p[:, 1] = np.round((2000 - p[:, 1] / 0.25) / 1000, 3)
        return y, p, b

    def detectCakes(self, frame):
        """
        This method will detect the cake and return the coordinates of each cakes in meters.

        Attributes
        ----------
        frame : list
            frame used for detecting the cake

        Returns
        -------
        y : list
            coordinates of the yellow cakes
        p : list
            coordinates of the pink cakes
        b : list
            coordinates of the brown cakes
        """

        if self.initialized == False:
            self.initDetector(frame)
            return
        else:
            self.detectAruco(frame)
            return self.labeltruc()

    def plotfinal(self):
        fig, ax = plt.subplots(figsize=(20, 20))
        plt.imshow(self.frame)
        plt.plot(self.y_pos[:, 1], self.y_pos[:, 0], "oy")
        plt.plot(self.p_pos[:, 1], self.p_pos[:, 0], "o", color="pink")
        plt.plot(self.b_pos[:, 1], self.b_pos[:, 0], "o", color="brown")
        for i in range(len(self.y_pos[:, 0])):
            plt.text(
                self.y_pos[i, 1] + 15,
                self.y_pos[i, 0] - 9,
                "Yellow",
                fontsize=11,
                color="w",
                bbox=dict(facecolor="black", alpha=0.6),
            )
            pass
        for i in range(len(self.p_pos[:, 0])):
            plt.text(
                self.p_pos[i, 1] + 15,
                self.p_pos[i, 0] - 9,
                "Pink",
                fontsize=11,
                color="w",
                bbox=dict(facecolor="black", alpha=0.6),
            )
            pass
        for i in range(len(self.b_pos[:, 0])):
            plt.text(
                self.b_pos[i, 1] + 15,
                self.b_pos[i, 0] - 9,
                "Brown",
                fontsize=11,
                color="w",
                bbox=dict(facecolor="black", alpha=0.6),
            )
            pass
        plt.show()
