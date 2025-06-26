import cv2 as cv
import datetime
import pyttsx3
from multiprocessing.dummy import Pool as ThreadPool
import os


def record_stream(connection_info):
    stream_string = connection_info[0]
    record_time = connection_info[1]
    frames_per_second = connection_info[2]
    video_name = connection_info[3]

    print('Starting Camera ' + video_name)

    os.system('ffmpeg -t ' + str(datetime.timedelta(seconds=record_time)) +
                   ' -i "' + stream_string + '" ' +
                   '-b 900k -r ' + str(frames_per_second) + ' -vcodec copy ' +
                   '-y ' + video_name + '.avi -loglevel panic')


# make the Pool of workers
pool = ThreadPool(9)

# speech to hear when video is starting and finishing
engine = pyttsx3.init()
rate = engine.getProperty('rate')
engine.setProperty('rate', rate-30)

local_path = '~/Desktop/'  # directory it saves videos to before uploading

base_video_name = 'P22_post_TUG3'

camera_ip_1 = '10.4.255.53'
camera_ip_2 = '10.4.255.54'
camera_ip_3 = '10.4.255.55'
camera_ip_4 = '10.4.255.57'
camera_ip_5 = '10.4.255.58'
camera_ip_6 = '10.4.255.60'
camera_ip_7 = '10.4.255.56'
camera_ip_8 = '10.4.255.59'

number_of_minutes = 0.5

perceived_start_delay = 5  # in seconds the amount of delay that the video starts with
record_time = number_of_minutes * 60 + perceived_start_delay  # in seconds

frames_per_second = 20

# rtsp://10.4.255.5x/cam/realmonitor?channel=1&subtype=00&authbasic=YWRtaW46YWRtaW4=
connection_info = [('rtsp://' + camera_ip_1 + '/cam/realmonitor?channel=1&subtype=00&authbasic=YWRtaW46YWRtaW4=', record_time, frames_per_second, local_path + base_video_name + "_camera_1"),
                     ('rtsp://' + camera_ip_2 + '/cam/realmonitor?channel=1&subtype=00&authbasic=YWRtaW46YWRtaW4=', record_time, frames_per_second, local_path + base_video_name + "_camera_2"),
                     ('rtsp://' + camera_ip_3 + '/cam/realmonitor?channel=1&subtype=00&authbasic=YWRtaW46YWRtaW4=', record_time, frames_per_second, local_path + base_video_name + "_camera_3"),
                     ('rtsp://' + camera_ip_4 + '/cam/realmonitor?channel=1&subtype=00&authbasic=YWRtaW46YWRtaW4=', record_time, frames_per_second, local_path + base_video_name + "_camera_4"),
('rtsp://' + camera_ip_5 + '/cam/realmonitor?channel=1&subtype=00&authbasic=YWRtaW46YWRtaW4=', record_time, frames_per_second, local_path + base_video_name + "_camera_5"),
('rtsp://' + camera_ip_6 + '/cam/realmonitor?channel=1&subtype=00&authbasic=YWRtaW46YWRtaW4=', record_time, frames_per_second, local_path + base_video_name + "_camera_6"),
('rtsp://' + camera_ip_7 + '/cam/realmonitor?channel=1&subtype=00&authbasic=YWRtaW46YWRtaW4=', record_time, frames_per_second, local_path + base_video_name + "_camera_7"),
('rtsp://' + camera_ip_8 + '/cam/realmonitor?channel=1&subtype=00&authbasic=YWRtaW46YWRtaW4=', record_time, frames_per_second, local_path + base_video_name + "_camera_8")]

print('Beginning to record for ' + str(record_time) + ' seconds')
engine.say('Beginning to record for ' + str(record_time) + ' seconds')
engine.say('On the count of 5')
engine.runAndWait()

# record
pool.map(record_stream, connection_info)

print("Recording Completed")
# engine.say("Recording Completed")
# engine.runAndWait()

# clean-up
cv.destroyAllWindows()
pool.close()
pool.join()