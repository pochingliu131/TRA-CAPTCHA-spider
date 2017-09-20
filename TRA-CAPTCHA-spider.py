# coding=utf-8
import numpy as np
import os
import urllib2,urllib
from datetime import date, timedelta,datetime
from bs4 import BeautifulSoup
import cv2
from PIL import Image 
import matplotlib.pyplot as plt
import random

url = 'http://railway.hinet.net/ctno1.htm' # TRA ticket booking URL
url_check = 'http://railway.hinet.net/check_ctno1.jsp'
tempPath = './template/'
captchaOutput ='output.jpg'

data = {
	'person_id' : 'A12345678910' , # Taiwan ID
	'from_station' : '100' , 
	'to_station' : '185' , 
	'getin_date' : '2016/09/11-16' , 
	'train_no' : '105' , 
	'order_qty_str' : '1' , # ticket number
	't_order_qty_str' : '0' ,
	'n_order_qty_str' : '0' ,
	'd_order_qty_str' : '0' ,
	'b_order_qty_str': '0' ,
	'z_order_qty_str' : '0' ,
	'returnTicket' : '0'
}

def downloadCAPTCHA():
	try:

		headers = {'User-agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/537.22 (KHTML, like Gecko) Chrome/25.0.1364.160 Safari/537.22' ,
					'Host' : 'railway.hinet.net' ,
					'Origin':'http://railway.hinet.net' ,
					'Referer':'http://railway.hinet.net/ctno1.htm'}

		data_encoded = urllib.urlencode(data)
		req = urllib2.Request(url_check, data_encoded, headers)
		response = urllib2.urlopen(req)
		soup = BeautifulSoup(response,"lxml")
		imgtag = soup.find(id='idRandomPic')
		imgurl = "http://railway.hinet.net/" + imgtag['src']
		req = urllib2.Request(imgurl, None, headers)
		response = urllib2.urlopen(req)
		img = response.read()
		open(tempPath+captchaOutput, 'wb').write(img)

	except Exception, e:
		print e

# todo : remove noising 
def denoising(obj):

	# todo : remove noising 
	im = cv2.imread(obj, flags=cv2.CV_LOAD_IMAGE_GRAYSCALE)
	retval, im = cv2.threshold(im, 115, 255, cv2.THRESH_BINARY_INV)

	# todo : remove noising point 
	for i in xrange(len(im)):
		for j in xrange(len(im[i])):
			if im[i][j] == 255:
				count = 0 
				for k in range(-2, 3):
					for l in range(-2, 3):
						try:
							if im[i + k][j + l] == 255:
								count += 1
						except IndexError:
							pass
				if count <= 2 :
					im[i][j] = 0

	# todo : Dilate img
	im = cv2.dilate(im, (4, 4), iterations=1)

	# todo : cut number 
	contours, hierarchy = cv2.findContours(im.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
	cnts = sorted([(c, cv2.boundingRect(c)[0]) for c in contours], key=lambda x:x[1])

	arr = []
	for index, (c, _) in enumerate(cnts):
		(x, y, w, h) = cv2.boundingRect(c)

		try:
			# high and width > 8 retain 
			if w > 8 and h > 8 :
				add = True
				for i in range(0, len(arr)):
				 	if abs(cnts[index][1] - arr[i][0]) <= 3:
				 		add = False
				 		break
				if add:
					arr.append((x, y, w, h))
		except IndexError:
			pass

	#todo : turnning number
	for index, (x, y, w, h) in enumerate(arr):
		roi = im[y: y + h, x: x + w]
		thresh = roi.copy() 
		
		angle = 0
		smallest = 999
		row, col = thresh.shape

		for ang in range(-60, 61):
			M = cv2.getRotationMatrix2D((col / 2, row / 2), ang, 1)
			t = cv2.warpAffine(thresh.copy(), M, (col, row))

			r, c = t.shape
			right = 0
			left = 999

			for i in xrange(r):
				for j in xrange(c):
					if t[i][j] == 255 and left > j:
						left = j
					if t[i][j] == 255 and right < j:
						right = j

			if abs(right - left) <= smallest:
				smallest = abs(right - left)
				angle = ang

		M = cv2.getRotationMatrix2D((col / 2, row / 2), angle, 1)
		thresh = cv2.warpAffine(thresh, M, (col, row))

		# resize as same size
		thresh = cv2.resize(thresh, (8, 8))
		cv2.imwrite(tempPath + str(index)+str(random.randint(0,1000)) + '.jpg', thresh)
		
if __name__ == '__main__' :

	start_time=datetime.now() 

	downloadCAPTCHA()
	denoising(tempPath+captchaOutput)

	finish_time=datetime.now()

	print 'Starting time: '+ start_time.strftime('%Y-%m-%d %H:%M:%S')
	print

	print 'finish time: '+ finish_time.strftime('%Y-%m-%d %H:%M:%S')

	print

	print 'total time: '+ str(finish_time-start_time)


