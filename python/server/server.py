import cherrypy
import subprocess
import json
import cv2
import cv2.cv as cv
import os
import shutil
from pprint import pprint
import time
from threading import Thread
import re
from decimal import Decimal
from os import listdir
from os.path import isfile, join


file_path = os.getcwd()

HTML_DIR = 'html'
UPLOAD_DIR = 'upload'

class Home:

    upload_progress = 0
    frames_per_second = 5
    video_length_seconds = 0
    conversion_thread = None
    evaluation_data = {}
    
    @cherrypy.expose
    def index(self):
        return open(os.path.join(HTML_DIR, u'index.html'))

    @cherrypy.expose
    def upload(self, video_file):
            self.upload_progress = 0
            all_data = ''
            size = 0
            
            while True:
                data = video_file.file.read(10240)
                all_data += data
                if not data:
                    break
                size += len(data)
                self.upload_progress = size
            with open(os.path.join(UPLOAD_DIR, video_file.filename), 'wb') as f:
                f.write(all_data)
                
    @cherrypy.expose
    def uploadprogress(self):
        return str(self.upload_progress)

    @cherrypy.expose
    def convert(self, filename):
        input_path = os.path.join(UPLOAD_DIR, filename)
        self.conversion_thread = Thread(target=self.start_conversion, args=(input_path,))
        self.video_length_seconds = self.get_video_length_seconds(input_path)
        self.get_video_format(input_path)
        self.get_stream_data(input_path)
        self.conversion_thread.start()

 
    def get_video_length_seconds(self, input_path):
        ffmpeg = os.path.abspath(os.path.join('ffmpeg', 'bin', 'ffmpeg.exe'))
        process = subprocess.Popen([ffmpeg, '-i', input_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = process.communicate()
        matches = re.search(r"Duration:\s{1}(?P<hours>\d+?):(?P<minutes>\d+?):(?P<seconds>\d+\.\d+?),", stdout, re.DOTALL).groupdict()
        hours = Decimal(matches['hours'])
        minutes = Decimal(matches['minutes'])
        seconds = Decimal(matches['seconds'])
        total = 0
        total += 60 * 60 * hours
        total += 60 * minutes
        total += seconds
        return total
    
    def get_video_format(self, input_path):
        import ConfigParser
        import StringIO
        ffprobe = os.path.abspath(os.path.join('ffmpeg', 'bin', 'ffprobe.exe'))
        process = subprocess.Popen([ffprobe, '-show_format', '-loglevel', 'quiet', input_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = process.communicate()
        format_list = stdout.split('\r\n')
        for entry in format_list:
            try:
                key, value = entry.split('=')
                if len(entry.split('=')) == 2:
                    self.evaluation_data[key] = value
            except:
                print
        
    def get_stream_data(self, input_path):
        import ConfigParser
        import StringIO
        ffprobe = os.path.abspath(os.path.join('ffmpeg', 'bin', 'ffprobe.exe'))
        process = subprocess.Popen([ffprobe, '-show_streams', '-loglevel', 'quiet', input_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = process.communicate()
        streams = stdout.split('[/STREAM]')[0:-1]
        self.evaluation_data['streams'] = []
        for stream in streams:
            stream_list = stream.split('\r\n')
            stream_data = {}
            for entry in stream_list:
                try:
                    key, value = entry.split('=')
                    if len(entry.split('=')) == 2:
                        stream_data[key] = value
                except:
                    print
            self.evaluation_data['streams'].append(stream_data)

    def start_conversion(self, input_path):
        output_path = 'frames'
        if os.path.exists(output_path):
            shutil.rmtree(output_path)
            time.sleep(5)

        os.makedirs(output_path)
        input_path = os.path.abspath(input_path)
        output_path = os.path.abspath(output_path)
        
        ffmpeg = os.path.abspath(os.path.join('ffmpeg', 'bin', 'ffmpeg.exe'))
        process = subprocess.Popen([ffmpeg, '-i', input_path, '-r', str(self.frames_per_second), os.path.join(output_path, 'frame-%8d.jpg')], stdout=subprocess.PIPE)
        process.wait()
        
    @cherrypy.expose
    def conversionprogress(self):
        output_path = 'frames'
        if os.path.exists(output_path):
            if self.conversion_thread.isAlive():
                path, dirs, files = os.walk(output_path).next()
                number_of_frames = len(files)
                percent = (number_of_frames / (self.video_length_seconds * self.frames_per_second)) * 100
                return str(percent)
            else:
                return "100"
        else:
            return "0"
    
    @cherrypy.expose
    def evaluationprogress(self):
        path = 'frames'
        all_files = [f for f in listdir(path) if isfile(join(path, f))]
        frames_count = 0
        evaluation_count = 0
        for filename in all_files:
            if any(str in filename for str in ['true', 'false']):
                evaluation_count += 1
            else:
                frames_count += 1
        percent = int(evaluation_count / float(frames_count) * 100)
        print frames_count, evaluation_count, evaluation_count / frames_count, percent
        return str(percent)
    
    @cherrypy.expose
    def evaluate(self):
        self.evaluation_data['detected'] = []
        output_path = 'frames'
        if os.path.exists(output_path):
            for root, dirs, files in os.walk(output_path):
                for file in files:
                    file_name = os.path.join(root, file)
                    if file.endswith(".jpg"):
                        image = cv2.imread(file_name)
                        image = cv2.cvtColor(image, cv.CV_BGR2GRAY)
                        image = cv2.equalizeHist(image)
                        rects = self.detect(image)
                        img_out = image.copy()
                        img_out = cv2.cvtColor(img_out, cv.CV_GRAY2RGB)
                        success = len(rects) != 0
                        self.draw_rects(img_out, rects, (0, 255, 0))
                        success_string = str(success).lower()
                        self.evaluation_data['detected'].append(success)
                        cv2.imwrite(file_name[:-4] + '_' + success_string + '.jpg', img_out)
        else:
            return "error"   
        return "evaluation"

    def draw_rects(self, img, rects, color):
        for x1, y1, x2, y2 in rects:
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

    def detect(self, img):
        scale_factor = 1.3
        min_neighbors = 3
        min_size = (20, 20)
        flags = cv.CV_HAAR_SCALE_IMAGE
        cascade_function = os.path.abspath(os.path.join('classifier', 'haarcascade_frontalface_alt_tree.xml'))
        cascade = cv2.CascadeClassifier(cascade_function)
        rects = cascade.detectMultiScale(img, scaleFactor=scale_factor, minNeighbors=min_neighbors, minSize=min_size, flags=flags)
        if len(rects) == 0:
            return []
        else:
            rects[:, 2:] += rects[:, :2]
            return rects
        
serverconf = os.path.join(os.path.dirname(__file__), 'server.conf')

if __name__ == '__main__':
    cherrypy.server.socket_host = "127.0.0.1"
    cherrypy.server.socket_port = 8080
    config = {"/static":
                        {"tools.staticdir.on": True,
                         "tools.staticdir.dir": file_path,
                        },
                      "/img":
                        {"tools.staticdir.on": True,
                        "tools.staticdir.dir": file_path + "/img"}
                    }

    cherrypy.tree.mount(Home(), "/", config=config)
    cherrypy.engine.start()
