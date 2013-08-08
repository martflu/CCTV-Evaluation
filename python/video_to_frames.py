import subprocess
import os
import argparse
import shutil

script_path = os.path.dirname(os.path.realpath(__file__))
test_dir = 'Test Data'
default_output_dir = 'frames'
movie = 'sample.mov'
 
input_path = os.path.join(script_path, os.pardir, test_dir, movie)

output_path = os.path.join(script_path, os.pardir, test_dir, default_output_dir, movie)

print input_path
print output_path

#parser = argparse.ArgumentParser(description='Extract frames from video.')
#parser.add_argument('input', help='input video', default=input_path)
#parser.add_argument('output', help='output directory', default=output_path)
#args = parser.parse_args()

if os.path.exists(output_path):
    shutil.rmtree(output_path)
   
os.makedirs(output_path)

vlc = 'C:/Program Files/VideoLAN/VLC/vlc.exe'
process = subprocess.Popen([
                            vlc,
                            input_path,
                            '--video-filter=scene',
                            '-Idummy',
                            '--vout=dummy',
                            '--scene-ratio=1',
                            '--scene-prefix=img-',
                            '--scene-path=' + output_path,
                            'vlc://quit'
                            ], stdout=subprocess.PIPE)
process.wait()
print 'finished'
