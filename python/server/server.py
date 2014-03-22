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
import numpy
from jinja2 import Template, Environment, FileSystemLoader


file_path = os.getcwd()
print file_path

HTML_DIR = 'html'
UPLOAD_DIR = 'upload'

class Home:

    upload_progress = 0
    frames_per_second = 5
    video_length_seconds = 0
    conversion_thread = None
    evaluation_data = {}
    
    env = Environment(loader=FileSystemLoader('html'))
    
    @cherrypy.expose
    def index(self):
        return open(os.path.join(HTML_DIR, u'index.html'))

    @cherrypy.expose
    def upload(self, video_file):
        self.evaluation_data['file_name'] = video_file.filename
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
        process = subprocess.Popen(["ffmpeg", '-i', input_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
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
        process = subprocess.Popen(["ffprobe", '-show_format', '-loglevel', 'quiet', input_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = process.communicate()
        format_list = stdout.split('\n')
        self.evaluation_data['video_format'] = {}
        for entry in format_list:
            try:
                key, value = entry.split('=')
                if len(entry.split('=')) == 2:
                    self.evaluation_data['video_format'][key] = value
            except Exception as e:
                print e
        
    def get_stream_data(self, input_path):
        import ConfigParser
        import StringIO
        process = subprocess.Popen(["ffprobe", '-show_streams', '-loglevel', 'quiet', input_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = process.communicate()
        streams = stdout.split('[/STREAM]')[0:-1]
        self.evaluation_data['streams'] = []
        for stream in streams:
            stream_list = stream.split('\n')
            stream_data = {}
            for entry in stream_list:
                try:
                    key, value = entry.split('=')
                    if len(entry.split('=')) == 2:
                        stream_data[key] = value
                except Exception as e:
                    print e
            self.evaluation_data['streams'].append(stream_data)

    def start_conversion(self, input_path):
        output_path = 'frames'
        if os.path.exists(output_path):
            shutil.rmtree(output_path)
            time.sleep(5)

        os.makedirs(output_path)
        input_path = os.path.abspath(input_path)
        output_path = os.path.abspath(output_path)
        
        process = subprocess.Popen(["ffmpeg", '-i', input_path, '-r', str(self.frames_per_second), os.path.join(output_path, 'frame-%8d.png')], stdout=subprocess.PIPE)
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
        if percent > 99:
            if self.evaluation_thread.isAlive():
                percent -= 1
        return str(percent)
    
    @cherrypy.expose
    def evaluate(self):
        f = 'found'
        m = 'missed'
        a = 'all'
        for key in [f, m, a]:
            self.evaluation_data[key] = {}
            self.evaluation_data[key]['detected'] = []
            self.evaluation_data[key]['faces'] = []
            self.evaluation_data[key]['area'] = []
            self.evaluation_data[key]['min'] = []
            self.evaluation_data[key]['max'] = []
            self.evaluation_data[key]['mean'] = []
        
        output_path = 'frames'
        if os.path.exists(output_path):
            self.evaluation_thread = Thread(target=self.evaluate_video, args=(output_path,))
            self.evaluation_thread.start()
        else:
            return "error"
        return "evaluation"

    def analyze_image(self, image):
        height, width = image.shape
        if not 'height' in self.evaluation_data:
            self.evaluation_data['height'] = height
            self.evaluation_data['width'] = width
        image_min = image[0][0]
        image_max = image[0][0]
        for y in range(0, height):
            for x in range(0, width):
                if image[y][x] < image_min:
                    image_min = image[y][x]
                if image[y][x] > image_max:
                    image_max = image[y][x]
        image_mean = numpy.mean(image)
        return image_min, image_mean, image_max

    def evaluate_video(self, path):
        for root, dirs, files in os.walk(path):
            self.evaluation_data['image_file_names'] = []
            files.sort();
            for file in files:
                file_name = os.path.join(root, file)
                if file.endswith(".png"):
                    image = cv2.imread(file_name)
                    image = cv2.cvtColor(image, cv.CV_BGR2GRAY)
                    rects = self.detect(image)
                    img_out = image.copy()
                    img_out = cv2.cvtColor(img_out, cv.CV_GRAY2RGB)
                    success = len(rects) != 0
                    self.draw_rects(img_out, rects, (0, 255, 0))
                    success_string = str(success).lower()
                    image_file_name = file_name[:-4] + '_' + success_string + '.png'
                    self.evaluation_data['image_file_names'].append(image_file_name)
                    cv2.imwrite(image_file_name, img_out)
                    
                    image_min, image_mean, image_max = self.analyze_image(image)
                    faces = len(rects)
                    area = self.get_average_rect_area(rects)
                    self.evaluation_data['all']['detected'].append(success)
                    self.evaluation_data['all']['faces'].append(faces)
                    self.evaluation_data['all']['area'].append(area)
                    self.evaluation_data['all']['min'].append(int(image_min))
                    self.evaluation_data['all']['mean'].append(int(image_mean))
                    self.evaluation_data['all']['max'].append(int(image_max))
                    if success:
                        self.evaluation_data['found']['detected'].append(success)
                        self.evaluation_data['found']['faces'].append(faces)
                        self.evaluation_data['found']['area'].append(area)
                        self.evaluation_data['found']['min'].append(image_min)
                        self.evaluation_data['found']['mean'].append(image_mean)
                        self.evaluation_data['found']['max'].append(image_max)
                    else:
                        self.evaluation_data['missed']['detected'].append(success)
                        self.evaluation_data['missed']['faces'].append(faces)
                        self.evaluation_data['missed']['area'].append(area)
                        self.evaluation_data['missed']['min'].append(image_min)
                        self.evaluation_data['missed']['mean'].append(image_mean)
                        self.evaluation_data['missed']['max'].append(image_max)
        self.calculate_video_evaluation_data()

    def calculate_video_evaluation_data(self):
        f = 'found'
        m = 'missed'
        a = 'all'
        for key in [f, m, a]:
            self.evaluation_data[key]['mean_detected'] = numpy.mean(self.evaluation_data[key]['detected'])
            self.evaluation_data[key]['mean_faces'] = numpy.mean(self.evaluation_data[key]['faces'])
            self.evaluation_data[key]['mean_area'] = numpy.mean(self.evaluation_data[key]['area'])
            self.evaluation_data[key]['mean_min'] = numpy.mean(self.evaluation_data[key]['min'])
            self.evaluation_data[key]['mean_mean'] = numpy.mean(self.evaluation_data[key]['mean'])
            self.evaluation_data[key]['mean_max'] = numpy.mean(self.evaluation_data[key]['max'])
        all = float(len(self.evaluation_data['all']['detected']))
        self.evaluation_data['found']['percent'] = float("%.2f" % (len(self.evaluation_data['found']['detected']) / all * 100.0))
        self.evaluation_data['missed']['percent'] = float("%.2f" % (len(self.evaluation_data['missed']['detected']) / all * 100.0))
        self.evaluation_data['frame_amount'] = len(self.evaluation_data['all']['detected'])
        self.evaluation_data['frame_percent'] = float(100) / float(self.evaluation_data['frame_amount'])
        
     
    def draw_rects(self, img, rects, color):
        for x1, y1, x2, y2 in rects:
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
    
    def get_average_rect_area(self, rects):
        if len(rects) == 0:
            return 0
        rect_areas = []
        for rect in rects:
            rect_areas.append(self.get_rect_area(rect))
        return numpy.mean(rect_areas)
            
    def get_rect_area(self, rect):
        x1, y1, x2, y2 = rect
        w = x2 - x1
        h = y2 - y1
        return w * h

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
    
    @cherrypy.expose
    def results(self):
        template = self.env.get_template('results.html')
        return template.render(
                               file_name=self.evaluation_data['file_name'],
                               found_percent = self.evaluation_data['found']['percent'],
                               missed_percent = self.evaluation_data['missed']['percent'],
                               frame_percent = self.evaluation_data['frame_percent'],
                               image_filenames = self.evaluation_data['image_file_names'],
                               detected_list = self.evaluation_data['all']['detected'],
                               detected_string = json.dumps(self.evaluation_data['all']['detected']),
                               faces_string = json.dumps(self.evaluation_data['all']['faces']),
                               area_string = json.dumps(self.evaluation_data['all']['area']),
                               min_string = json.dumps(self.evaluation_data['all']['min']),
                               mean_string = json.dumps(self.evaluation_data['all']['mean']),
                               max_string = json.dumps(self.evaluation_data['all']['max']),
                               
                               
                               video_format = self.evaluation_data['video_format'],
                               streams = self.evaluation_data['streams']
                               )
    
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
                "tools.staticdir.dir": file_path + "/img"},
              "/frames":
                {"tools.staticdir.on": True,
                "tools.staticdir.dir": file_path + "/frames"}
            }

    cherrypy.tree.mount(Home(), "/", config=config)
    cherrypy.engine.start()