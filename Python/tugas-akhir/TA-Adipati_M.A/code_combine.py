# import the necessary packages
from scipy.spatial import distance as dist
from imutils.video import VideoStream
from imutils.video import FPS
from imutils import face_utils
from Adafruit_IO import *
from gps import *
from subprocess import check_output
import signal
# import sys
import threading
import numpy as np
import RPi.GPIO as GPIO
import BlynkLib
import argparse
import imutils
import time
import dlib
import cv2
# import playsound

# def sound_alarm(path):
# 	# play an alarm sound
# 	playsound.playsound(path)

def eye_aspect_ratio(eye):
	# compute the euclidean distances between the two sets of
	# vertical eye landmarks (x, y)-coordinates
	A = dist.euclidean(eye[1], eye[5])
	B = dist.euclidean(eye[2], eye[4])
	# compute the euclidean distance between the horizontal
	# eye landmark (x, y)-coordinates
	C = dist.euclidean(eye[0], eye[3])
	# compute the eye aspect ratio
	ear = (A + B) / (2.0 * C)
	# return the eye aspect ratio
	return ear


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
# ap.add_argument("-p", "--shape-predictor", required=True,
# 	help="path to facial landmark predictor")
# ap.add_argument("-a", "--alarm", type=str, default="",
# 	help="path alarm .WAV file")
ap.add_argument("-w", "--webcam", type=int, default=0,
	help="index of webcam on system")
args = vars(ap.parse_args())

# define two constants, one for the eye aspect ratio to indicate
# blink and then a second constant for the number of consecutive
# frames the eye must be below the threshold for to set off the
# alarm
EYE_AR_THRESH = 0.3
EYE_AR_CONSEC_FRAMES = 3 # utk Raspi 4.5 FPS (0.5 detik)
# EYE_AR_CONSEC_FRAMES = 11 # utk Raspi 4.5 FPS
# EYE_AR_CONSEC_FRAMES = 48 # utk Laptop

# third constant for level 2 number of consecutive frames
# pertambahan 0.5 detik = 3 frames --> 11 + 3 = 14
# EYE_AR_2ND_CONSEC_FRAMES = 14
EYE_AR_2ND_CONSEC_FRAMES = 6 # 3+3

# initialize the frame counter as well as a boolean used to
# indicate if the alarm is going off
COUNTER = 0
ALARM_ON = False

# variable for indicating level 2 alarm is on
ALARM_L2 = False

# variable for thread needs
tBeepCreated = False
tBeepRunning = False
tSendCreated1 = False
tSendRunning1 = False
tSendCreated2 = False
tSendRunning2 = False
sendCounter1 = 0
sendCounter1 = 0
sendCounter2 = 0

# GPIO Buzzer
signal1PIN = 27
signal2PIN = 17
GreenLED = 22
RedLED = 23
# Set PIN to output
GPIO.setmode(GPIO.BCM)
GPIO.setup(signal1PIN,GPIO.OUT)
GPIO.setup(signal2PIN,GPIO.OUT)
GPIO.setup(GreenLED,GPIO.OUT)
GPIO.setup(RedLED,GPIO.OUT)

# Initialize Blynk, Adafruit IO, & State for GPS (IoT)
blynk = BlynkLib.Blynk('1EWSq_x7ATOX7ejvCMx5OwNVF9RtOFIe')
# aio = Client('USERNAME', 'AIO_KEY')
aio = Client('adipati27ma', 'aio_dFvr06uGjYiEJ6VOMdz1dxE5nRzZ')
sendingData = False
sentAdafruit = False
# End of Initialize for IoT


# Functions
def beep_beep_buzzer(pin):
	global ALARM_L2
	while ALARM_L2:
		GPIO.output(pin,1)
		GPIO.output(RedLED,1)
		time.sleep(0.1)
		GPIO.output(pin,0)
		GPIO.output(RedLED,0)
		time.sleep(0.1)

def level_2_buzzer_active(signal):
	global tBeepCreated
	global tBeepRunning
	global ALARM_L2
	if signal == 0:
		GPIO.output(signal2PIN,0)
		ALARM_L2 = False
		tBeepCreated = False
		tBeepRunning = False
	if signal == 1:
		ALARM_L2 = True
		GPIO.output(signal1PIN,0)
		if not tBeepCreated:
			beep_thread = threading.Thread(target=beep_beep_buzzer, args=[signal2PIN])
			tBeepCreated = True
		if not tBeepRunning:
			beep_thread.start()
			tBeepRunning = True

# GPS Function
def getPositionData(gps):
  nx = gps.next()
	
  # For a list of all supported classes and fields refer to:
  # https://gpsd.gitlab.io/gpsd/gpsd_json.html
  if nx['class'] == 'TPV':
    latitude = getattr(nx,'lat', "Unknown")
    longitude = getattr(nx,'lon', "Unknown")
    positionData = [latitude, longitude]

    return positionData

# Function sendToBlynk & sendToAdafruit
def sendToBlynk(dataGps, dataLevel):
  blynk.virtual_write(5, 1, dataGps[0], dataGps[1], "value")
  blynk.virtual_write(2, str(dataGps))
  blynk.virtual_write(3, str(dataLevel))

def sendToAdafruit(dataLevel, metaData):
  aio.send("sleepy-driver-data-history", dataLevel, metaData)

def resetBlynk():
	# blynk.virtual_write(2, str(' '))
	blynk.virtual_write(3, str(' '))
	# Turn off Danger LED
	blynk.virtual_write(0, 0)

# Function send Pos Data
def sendPositionData(gpsd, level):
	global sendingData
	global sentAdafruit
	global sendCounter1
	global sendCounter2
	dataLevel = level
  
	start = time.perf_counter() # for response time debugging
	finish = False
	try:
		print('Application Started')
		for x in range(10) :
			dataGps = getPositionData(gpsd)
			print(dataGps)

			if dataGps :
				if dataGps[0] is not 'Unknown' and dataGps[1] is not 'Unknown':
					if(dataLevel == 1 or dataLevel == 0):
						sendCounter1 += 1
					if(dataLevel == 2):
						sendCounter2 += 1
					metaData = {
						'lat': dataGps[0],
						'lon': dataGps[1],
						'ele': 0,
						'created_at': None,
					}
					
					sendBlynk = threading.Thread(target=sendToBlynk, args=[dataGps, dataLevel])
					sendBlynk.start()
					if (sentAdafruit == False):
						sendAdafruit = threading.Thread(target=sendToAdafruit, args=[dataLevel, metaData])
						sendAdafruit.start()
						sentAdafruit = True
					
					if(dataLevel == 1 or dataLevel == 0):
						if(sendCounter1 == 1):
							finish = time.perf_counter() # for response time debugging
					if(dataLevel == 1 or dataLevel == 0):
						if(sendCounter1 == 2):
							sendCounter1 = 0
							break
					if(dataLevel == 2):
						if(sendCounter2 == 2):
							sendCounter2 = 0
							break
			time.sleep(1)
	except:
		print('Application Closed')

	blynk.virtual_write(1, 0)
	sendingData = False
	sentAdafruit = False
	finishAll = time.perf_counter()
	print("Data transfer stopped.")
	if(finish):
		print(f'Get first data in {round(finish-start, 5)} second(s)') # for response time debugging
	print(f'Finished ALL in {round(finishAll-start, 5)} second(s)') # for response time debugging

# Send Thread Function
def createStartSendThread(dataLevel):
	global sendingData
	global tSendCreated1
	global tSendRunning1
	global tSendCreated2
	global tSendRunning2
	gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)
	
	if (dataLevel == 1):
			if not tSendCreated1:
				sendThread = threading.Thread(target=sendPositionData, args=[gpsd, dataLevel])
				tSendCreated1 = True
			if not tSendRunning1:
				sendThread.start()
				tSendRunning1 = True
	
	if (dataLevel == 2):
			if not tSendCreated2:
				sendThread = threading.Thread(target=sendPositionData, args=[gpsd, dataLevel])
				tSendCreated2 = True
			if not tSendRunning2:
				sendThread.start()
				tSendRunning2 = True

# Input from Blynk (will send data gps to Blynk)
@blynk.VIRTUAL_WRITE(1)
def my_write_handler(value) :
  global sendingData
  intValue = int(value[0])
  if sendingData :
    blynk.virtual_write(1, 1)
    return
  if intValue == 0 : return

  gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)
  print("Sending data...")
  sendingData = True

  sendThread = threading.Thread(target=sendPositionData, args=[gpsd, 0])
  sendThread.start()

# def signal_handler(signal, frame):
#     print('You pressed Ctrl+C!')
#     sys.exit(0)

# signal.signal(signal.SIGINT, signal_handler)
# forever = threading.Event()
# forever.wait()

def keyboardInterruptHandler(signal, frame):
		print("KeyboardInterrupt (ID: {}) has been caught. Cleaning up...".format(signal))
		# tampilkan info FPS
		fps.stop()
		print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
		print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

		# do a bit of cleanup
		GPIO.output(GreenLED,0)
		cv2.destroyAllWindows()
		GPIO.cleanup()
		vs.stop()
		exit(0)

signal.signal(signal.SIGINT, keyboardInterruptHandler)


# Start Program-----
wifi_ip = check_output(['hostname', '-I'])
# initialize dlib's face detector (HOG-based) and then create
# the facial landmark predictor
print("[INFO] loading facial landmark predictor...")
detector = dlib.get_frontal_face_detector()
# predictor = dlib.shape_predictor(args["shape_predictor"])
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

# grab the indexes of the facial landmarks for the left and
# right eye, respectively
(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

# start the video stream thread
print("[INFO] starting video stream thread...")
vs = VideoStream(src=args["webcam"]).start()
print("[INFO] ok")
time.sleep(1.0)

# Check Wi-Fi Connection
if (wifi_ip is not None):
	print("Wi-Fi Connected")
	print("started!")

	# Penghitung FPS (Frame per Second)
	fps = FPS().start()

	# loop over frames from the video stream
	while True:
		# Run Blyk
		blynk.run()

		# grab the frame from the threaded video file stream, resize
		# it, and convert it to grayscale
		# channels)
		GPIO.output(GreenLED,1)
		frame = vs.read()
		# cv2.normalize(frame, frame, 0, 255, cv2.NORM_MINMAX)
		frame = imutils.resize(frame, width=450)
		frame = cv2.rotate(frame, cv2.ROTATE_180)
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		# detect faces in the grayscale frame
		rects = detector(gray, 0)

		# check if there's face detected/not
		if (len(rects) == 0):
			# Reset counter, thread & alarm variable
			COUNTER = 0
			tSendCreated1 = False
			tSendRunning1 = False
			tSendCreated2 = False
			tSendRunning2 = False
			ALARM_ON = False
			if ALARM_ON == False :
				GPIO.output(signal1PIN,0)
				level_2_buzzer_active(0)
				# GPIO.output(signal2PIN,0)
				GPIO.output(RedLED,0)
				resetBlynk()
				cv2.putText(frame, "Tidak Terdeteksi Wajah", (10, 320),
					cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

		# loop over the face detections
		for rect in rects:
			# determine the facial landmarks for the face region, then
			# convert the facial landmark (x, y)-coordinates to a NumPy
			# array
			shape = predictor(gray, rect)
			shape = face_utils.shape_to_np(shape)
			# extract the left and right eye coordinates, then use the
			# coordinates to compute the eye aspect ratio for both eyes
			leftEye = shape[lStart:lEnd]
			rightEye = shape[rStart:rEnd]
			leftEAR = eye_aspect_ratio(leftEye)
			rightEAR = eye_aspect_ratio(rightEye)
			# average the eye aspect ratio together for both eyes
			ear = (leftEAR + rightEAR) / 2.0



			# compute the convex hull for the left and right eye, then
			# visualize each of the eyes
			leftEyeHull = cv2.convexHull(leftEye)
			rightEyeHull = cv2.convexHull(rightEye)
			cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
			cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)

			# check to see if the eye aspect ratio is below the blink
			# threshold, and if so, increment the blink frame counter
			# if (ear) :
				# print(ear)
			if ear < EYE_AR_THRESH:
				COUNTER += 1
				cv2.putText(frame, "counting...", (10, 320),
					cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
				# if the eyes were closed for a sufficient number of
				# then sound the alarm
				if COUNTER >= EYE_AR_CONSEC_FRAMES:
					# if the alarm is not on, turn it on
					if not ALARM_ON:
						ALARM_ON = True
						if ALARM_ON == True :
							print('ALARM ON LEVEL 1!!!!!!!!!')
							cv2.putText(frame, "Level : 1", (340, 320),
								cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
							GPIO.output(signal1PIN,1)
							level_2_buzzer_active(0)
							# GPIO.output(signal2PIN,0)

							# Turn on notify danger & Send Data GPS Level 1
							blynk.notify('Pengemudi mulai mengantuk!!')
							blynk.virtual_write(0, 255)
							createStartSendThread(1)
							GPIO.output(RedLED,1)
						
						
					# draw an alarm on the frame
					cv2.putText(frame, "DROWNSINESS ALERT!", (10, 30),
						cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
					
					if COUNTER >= EYE_AR_2ND_CONSEC_FRAMES:
						print('ALARM ON~~~~~~~~~~~~~LEVEL 2')
						cv2.putText(frame, "Level : 2", (340, 320),
							cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
						level_2_buzzer_active(1)
						# GPIO.output(signal2PIN,1)
						
						# Send Data GPS Level 2
						createStartSendThread(2)
					

			# otherwise, the eye aspect ratio is not below the blink
			# threshold, so reset the counter and alarm
			else:
				COUNTER = 0
				ALARM_ON = False
				print('ALARM OFF.')
				if ALARM_ON == False :
					cv2.putText(frame, "Level : 0", (340, 320),
						cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
					GPIO.output(signal1PIN,0)
					level_2_buzzer_active(0)
					# GPIO.output(signal2PIN,0)
					GPIO.output(RedLED,0)

					# Reset Blynk Data & Send Thread Variable
					resetBlynk()
					tSendCreated1 = False
					tSendRunning1 = False
					tSendCreated2 = False
					tSendRunning2 = False





			# draw the computed eye aspect ratio on the frame to help
			# with debugging and setting the correct eye aspect ratio
			# thresholds and frame counters
			cv2.putText(frame, "EAR: {:.3f}".format(ear), (300, 30),
				cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)


		# show the frame
		# cv2.imshow("Frame", frame) # comment if don't want debugging
		key = cv2.waitKey(1) & 0xFF

		# if the `q` key was pressed, break from the loop
		if key == 27 or key == ord("q"):
			print("[INFO] exiting...")
			break

		# update FPS
		fps.update()
# End Of While Loop
else:
  print("Not Connected")


# tampilkan info FPS
fps.stop()
print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

# do a bit of cleanup
GPIO.output(GreenLED,0)
cv2.destroyAllWindows()
GPIO.cleanup()
vs.stop()