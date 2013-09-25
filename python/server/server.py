import cherrypy
import subprocess
import os
import shutil
import time

file_path = os.getcwd()

HTML_DIR = 'html'
UPLOAD_DIR = 'upload'

class Home:

    upload_progress = 0
    
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
        filepath = os.path.join(UPLOAD_DIR, filename)
        
        self.start_conversion(filepath)


    def start_conversion(self, input_path):
        output_path = 'frames'
        if os.path.exists(output_path):
            shutil.rmtree(output_path)
            time.sleep(5)

        os.makedirs(output_path)
        input_path = os.path.abspath(input_path)
        output_path = os.path.abspath(output_path)
        ffmpeg = os.path.abspath(os.path.join('ffmpeg', 'bin', 'ffmpeg.exe'))
        process = subprocess.Popen([ffmpeg, '-i', input_path, '-r', '5', os.path.join(output_path, 'frame-%6d.jpg')], stdout=subprocess.PIPE)
        process.wait()

    
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
