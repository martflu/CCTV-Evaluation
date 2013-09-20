import cherrypy
import os

file_path = os.getcwd()

class Home:

    HTML_DIR = 'html'
    
    @cherrypy.expose
    def index(self):
        return open(os.path.join(self.HTML_DIR, u'index.html'))


import os.path
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
