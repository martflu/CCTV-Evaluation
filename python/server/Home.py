import cherrypy
import os

file_path = os.getcwd()

HTML_DIR = 'html'
UPLOAD_DIR = 'upload'

class Home:


    
    @cherrypy.expose
    def index(self):
        return open(os.path.join(HTML_DIR, u'index.html'))

    @cherrypy.expose
    def upload(self, myFile):
            all_data = ''
            size = 0
            while True:
                data = myFile.file.read(1024)
                all_data += data
                if not data:
                    break
                size += len(data)
            with open(os.path.join(UPLOAD_DIR, myFile.filename), 'w') as f:
                f.write(all_data)

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

    cherrypy.tree.mount(Home(), "/", config = config)
    cherrypy.engine.start()
