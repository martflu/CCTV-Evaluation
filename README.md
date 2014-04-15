CCTV-Evaluation
===============

CCTV-Evaluation is a simple python webserver for the evaluation of CCTV camera footage. The purpose of the service is to evaluate, if the video quality is good enough for face recognition. The uploaded videos are supposed to be relatively short (> 2 min) and the face should be present in every frame of the video. Once the user uploaded the video, it will be converted into single frames and every frame will be analyzed. For face detection, the OpenCV library is used (Face Detection using Haar Cascades). After evaluation the user can review the evaluation results, which also include suggestions for improvement.

After installing the dependencies, the server can simply be started with
`python server.py`
