##########################################################
#                   CAKE DETECTOR 2                      #
##########################################################
import numpy as np
import matplotlib.pyplot as plt
import cv2
from cv2 import aruco
import os
import PIL
from PIL import Image

from skimage import color, measure, morphology, feature, filters
import imutils


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

    resolutionData = [1920, 1080]
    size_of_marker = 0.1  # size of arucoTag of table in meter
    offset_x = 100  # offset of reconstruct frame in x
    offset_y = 100  # offset of reconstruct frame in x
    table_size_x = 3000 + offset_x
    table_size_y = 2000 + offset_y
    f = 1

    warpMatrix = []
    pink = []
    yellow = []
    brown = []
    y_pos = []
    p_pos = []
    b_pos = []
    posCenter = []
    posGround = []
    cakeLayer = []
    frame_x = table_size_x * f
    frame_y = table_size_y * f

    frame = []

    # parameters = aruco.DetectorParameters_create()
    # parameters.adaptiveThreshWinSizeMin = 10
    # parameters.adaptiveThreshWinSizeMax = 21
    # parameters.adaptiveThreshWinSizeStep = 1

    def __init__(self):
        pass

    def initDetector(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        grayFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Aruco detection
        # aruco_dict = aruco.Dictionary_get(aruco.DICT_4X4_50)
        # markerCorners, markerIds, rejectedImgPoints = aruco.detectMarkers(
        #     frame, aruco_dict, parameters=self.parameters
        # )
        dictionary = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
        parameters = aruco.DetectorParameters()
        detector = aruco.ArucoDetector(dictionary, parameters)
        markerCorners, markerIds, rejectedCandidates = detector.detectMarkers(grayFrame)

        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.0001)
        for corner in markerCorners:
            cv2.cornerSubPix(
                grayFrame, corner, winSize=(3, 3), zeroZone=(-1, -1), criteria=criteria
            )

        frame_markers = aruco.drawDetectedMarkers(frame.copy(), markerCorners, markerIds)
        """
        plt.figure(figsize=(20,20))
        plt.imshow(frame_markers)
        plt.show()"""
        imaxis = aruco.drawDetectedMarkers(frame.copy(), markerCorners, markerIds)
        ar = np.array(markerCorners)
        # Corner extern of reference arucoTag
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
            frame,
            matrix,
            (
                int((2000 + self.offset_y) * self.f),
                int((3000 + self.offset_x) * self.f),
            ),
        )
        # -------------------------------------------------------------------------------------------------------

        (w, h, p) = frame.shape
        # split image 3x2
        splitx = 3
        splity = 2
        marge = 100

        offsetx = int(w / splitx)
        offsety = int(h / splity)

        # Aruco detection
        aruco_dict = aruco.Dictionary_get(aruco.DICT_4X4_1000)
        # parameters =  aruco.DetectorParameters_create()

        pos = []
        for i in range(splitx):
            for j in range(splity):
                cutframe = frame[
                    i * offsetx : min((i + 1) * offsetx + marge, w),
                    j * offsety : min((j + 1) * offsety + marge, h),
                    :,
                ]
                try:
                    # markerCorners, markerIds, rejectedImgPoints = aruco.detectMarkers(
                    #     cutframe, aruco_dict, parameters=self.parameters
                    # )
                    # frame_markers = aruco.drawDetectedMarkers(
                    #     frame.copy(), markerCorners, markerIds
                    # )
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
                        # pos.append([markerIds[k,0],c[1, 0]+j*offsety,c[1, 1]+i*offsetx])
                except:
                    print("error")
                    pass
        pos = np.asarray(pos)
        y = pos[:, 1]
        x = pos[:, 2]

        # Center coordinates
        center_coordinates = (120, 50)

        # Radius of circle
        radius = 50

        # Blue color in BGR
        color = (255, 0, 0)

        # Line thickness of 2 px
        thickness = 2

        # Using cv2.circle() method
        # Draw a circle with blue line borders of thickness of 2 px

        # plt.figure(figsize=(20,20))
        # plt.imshow(frame)
        # plt.plot(y,x,'o')
        # plt.show()

        return frame

    def detectAruco(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.warpPerspective(
            frame,
            self.warpMatrix,
            (
                int((2000 + self.offset_y) * self.f),
                int((3000 + self.offset_x) * self.f),
            ),
        )
        (w, h, p) = frame.shape
        # split image 3x2
        splitx = 3
        splity = 2
        marge = 100

        offsetx = int(w / splitx)
        offsety = int(h / splity)

        aruco_dict = aruco.Dictionary_get(aruco.DICT_4X4_1000)
        # parameters =  aruco.DetectorParameters_create()

        pos = []
        pos_corners = []
        for i in range(splitx):
            for j in range(splity):
                cutframe = frame[
                    i * offsetx : min((i + 1) * offsetx + marge, w),
                    j * offsety : min((j + 1) * offsety + marge, h),
                    :,
                ]
                try:
                    markerCorners, markerIds, rejectedImgPoints = aruco.detectMarkers(
                        cutframe, aruco_dict, parameters=self.parameters
                    )
                    frame_markers = aruco.drawDetectedMarkers(
                        frame.copy(), markerCorners, markerIds
                    )
                    for k in range(len(markerIds)):
                        c = markerCorners[k][0]
                        pos.append(
                            [
                                markerIds[k, 0],
                                c[:, 0].mean() + j * offsety,
                                c[:, 1].mean() + i * offsetx,
                            ]
                        )
                        pos_corners.append(
                            [markerIds[k, 0], c[:, 0] + j * offsety, c[:, 1] + i * offsetx]
                        )
                        # pos.append([markerIds[k,0],c[1, 0]+j*offsety,c[1, 1]+i*offsetx])
                except:
                    print("error")
                    pass

        pos = np.asarray(pos)

        l = 15
        s = 18
        h = np.sqrt(s * s + l * l)
        a = np.arctan(l / s)

        pos_center = []
        for i in range(len(pos[:, 0])):
            if pos[i, 0] == 36 or pos[i, 0] == 13 or pos[i, 0] == 47:
                b = np.arctan(
                    (pos_corners[i][2][1] - pos_corners[i][2][0])
                    / (pos_corners[i][1][1] - pos_corners[i][1][0])
                )
                t = np.pi - a - b
                dx = np.cos(t) * h
                dy = np.sin(t) * h
                if pos_corners[i][2][0] > pos_corners[i][2][3]:
                    pos_center.append(
                        [
                            pos[i, 0],
                            pos_corners[i][2][0] - dx,
                            pos_corners[i][1][0] - dy,
                        ]
                    )
                else:
                    pos_center.append(
                        [
                            pos[i, 0],
                            pos_corners[i][2][0] + dx,
                            pos_corners[i][1][0] + dy,
                        ]
                    )

        pos_center = np.asarray(pos_center)

        """
        plt.figure(figsize=(20,20))
        plt.imshow(frame)
        TagId = [13, 36, 47]
        colorPlot = ['oy', 'ob', 'or']
        for i in range(0,3):
            y = pos[pos[:,0]==TagId[i],1]
            x = pos[pos[:,0]==TagId[i],2]
            plt.plot(y,x,colorPlot[i])

        plt.plot(pos_center[:,2],pos_center[:,1],'o')
        plt.plot(pos_center[:,2],pos_center[:,1]+55,'x')    
        plt.show()"""

        self.frame = frame
        self.posCenter = pos_center
        return pos_center

        pass

    def determinNumberOfLayer(self):
        wide = 100
        height = 100
        plt.figure(figsize=(10, 10))
        # plt.imshow(self.frame)
        for k in range(self.posCenter.shape[0]):
            frameLayer = self.frame[
                round(self.posCenter[k, 1] + 55) : round(
                    self.posCenter[k, 1] + 55 + height
                ),
                round(self.posCenter[k, 2] - wide / 2) : round(
                    self.posCenter[k, 2] + wide / 2
                ),
                :,
            ]

            # frame
            plt.imshow(frameLayer)
            plt.show()

        pass

    def determinNumberOfLayer2(self):
        color_map = ["Y", "P", "B"]
        self.posGround = self.posCenter.copy()
        np.asanyarray(self.posGround)
        squareBB = 180
        bb_h = 100
        bb_w = 10
        offset_h = 60
        frame = self.frame.copy()
        frame = cv2.GaussianBlur(frame, (7, 7), 0)
        cakeColor = []
        j = -1
        pos = self.posCenter
        # print(len(pos))
        for k in range(len(pos)):
            # if(pos[k,0] == 36 or pos[k,0] == 13 or pos[k,0] == 47):
            # if(pos[k,0] == 36):
            # j += 1
            """
            if(pos[k,0] == 13):
                cakeColor.append(['Y','x','x'])
            elif(pos[k,0] == 36):
                cakeColor.append(['B','x','x'])
            elif(pos[k,0] == 47):
                cakeColor.append(['P','x','x'])
            else:
                cakeColor.append(['x','x','x'])
            """
            markerBox = frame[
                max(int(pos[k, 1] + offset_h), 0) : int(pos[k, 1] + bb_h + offset_h),
                max(int(pos[k, 2] - bb_w / 2), 0) : int(pos[k, 2] + bb_w / 2),
                :,
            ]
            markerBox = frame[
                max(int(pos[k, 1] - squareBB), 0) : int(pos[k, 1] + squareBB),
                max(int(pos[k, 2] - squareBB), 0) : int(pos[k, 2] + squareBB),
                :,
            ]
            pix_x, pix_y = self.cvtPosPixel(0, 0.85)
            angle_rad = np.arctan2(
                (3100 - self.posCenter[k, 1]), (pix_y) - self.posCenter[k, 2]
            )
            angle_deg = angle_rad * 180 / 3.14
            markerBox = imutils.rotate(markerBox, angle=-90 + angle_deg)
            markerBox = markerBox[
                squareBB + offset_h :, squareBB - bb_w : squareBB + bb_w, :
            ]
            # markerBox = frame[max(int(pos[k,1]+offset_h),0):int(pos[k,1]+bb_h+offset_h), max(int(pos[k,2]-bb_w/2),0):int(pos[k,2]+bb_w/2),:]

            markerBox_HSV = cv2.cvtColor(markerBox, cv2.COLOR_RGB2HSV)

            BB_yellow = cv2.inRange(markerBox_HSV, (15, 100, 20), (30, 255, 255))
            BB_pink = cv2.inRange(markerBox_HSV, (130, 100, 20), (180, 255, 255))
            # BB_brown = cv2.inRange(markerBox_HSV,(0, 20, 5), (20, 255, 100) )
            # BB_brown = cv2.inRange(markerBox_HSV,(100, 10, 40), (180, 120, 160) )
            BB_brown = cv2.inRange(markerBox, (30, 30, 30), (80, 80, 80))

            BB = [BB_yellow, BB_pink, BB_brown]

            cakeSort = []
            cakeLayer = []
            height = 0
            for i, c in enumerate(BB):
                # input_mask = BB[c]
                input_mask = c
                # labels_mask = measure.label(input_mask[-int(bb_h*2/3):,:])
                labels_mask = measure.label(input_mask)
                regions = measure.regionprops(labels_mask)
                regions.sort(key=lambda x: x.area, reverse=True)
                if len(regions) > 1:
                    for rg in regions[1:]:
                        labels_mask[rg.coords[:, 0], rg.coords[:, 1]] = 0
                labels_mask[labels_mask != 0] = 1
                BB[i] = labels_mask

                region = measure.regionprops(labels_mask)
                if region:
                    minr, minc, maxr, maxc = region[0].bbox
                    width = maxc - minc
                    if width >= 10:
                        heightLayer = maxr - minr
                        height += heightLayer
                        cakeSort.append([color_map[i], region[0].centroid[0]])
            cakeSort.sort(key=lambda a: a[1])

            try:
                non = list(zip(*cakeSort))[0]
            except:
                non = []
            cakeColor.append(non)

            if k == 2:
                # plt.imsave('result/brown2.png', markerBox)
                pass

            self.cakeLayer = cakeColor.copy()
            dy = np.cos(angle_rad) * height
            dx = np.sin(angle_rad) * height
            self.posGround[k, 1] = self.posCenter[k, 1] + dx
            self.posGround[k, 2] = self.posCenter[k, 2] + dy
            """
            print(k)
            print(self.posCenter[0,1])
            print(self.posGround[0,1])
            print('y: ', self.posCenter[k,1],' ¦  x: ', self.posCenter[k,2])

            print(angle_deg)
            print(cakeColor[j])
            
            print("height : ", height)
            plt.figure(figsize=(15,5))
            plt.title("Y / P / B")
            plt.subplot(1,4,1)
            plt.imshow(markerBox)
            plt.subplot(1,4,2)
            plt.imshow(BB[0], cmap='gray')
            plt.subplot(1,4,3)
            plt.imshow(BB[1], cmap='gray')
            plt.subplot(1,4,4)
            plt.imshow(BB[2], cmap='gray')
            plt.show()"""

        # self.plotFrame()
        # print(cakeColor)

    def plotFrame(self):
        plt.figure(figsize=(20, 20))
        plt.imshow(self.frame)
        TagId = [13, 36, 47]
        colorPlot = ["oy", "ob", "or"]
        for i in range(0, 3):
            x = self.posCenter[self.posCenter[:, 0] == TagId[i], 1]
            y = self.posCenter[self.posCenter[:, 0] == TagId[i], 2]
            plt.plot(y, x, colorPlot[i])
        plt.plot(self.posGround[:, 2], self.posGround[:, 1], "x")
        plt.plot(self.posCenter[:, 2], self.posCenter[:, 1] + 55, "x")
        plt.show()

    def cvtPixelPos(self, x_pix, y_pix):

        x_pos = (self.frame_x - x_pix) * 3.1 / self.frame_x
        y_pos = (self.frame_y - y_pix - self.offset_y / 2) * 2.1 / self.frame_y
        return [x_pos, y_pos]

    def cvtPosPixel(self, x_pos, y_pos):

        x_pix = round((3.1 - x_pos) * self.frame_x / 3.1)
        y_pix = round((2.1 - y_pos) * self.frame_y / 2.1)

        y_pix = -(y_pos * self.frame_y / 2.1 + self.offset_y / 2 - self.frame_y)

        return [x_pix, y_pix]

    def detectCakes(self, frame):
        self.detectAruco(frame)
        self.determinNumberOfLayer2()
        positions = self.posGround[:, 1:]
        layers = self.cakeLayer

        map = {
            "B": 0,
            "Y": 1,
            "P": 2,
        }

        return [
            dict(
                x=cake[0][0],
                y=cake[0][1],
                layers=[map.get(l) for l in cake[1]],
                hasCherry=False,
            )
            for cake in zip(positions, layers)
        ]
