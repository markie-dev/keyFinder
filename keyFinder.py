import yt_dlp
import urllib.request
import re
import os
import warnings
import sys
import colorama
import argparse
from colorama import Fore
import essentia

essentia.log.infoActive = False
essentia.log.warningActive = False
import essentia.standard as es

warnings.filterwarnings("ignore", category=UserWarning) 

# argument parsing
parser = argparse.ArgumentParser()
parser.add_argument('-c', '--clean', action='store_true', help='delete all songs in the songs folder')
args = parser.parse_args()

# if the -c option is used, delete all songs in the songs folder
if args.clean:
    folder = 'songs'
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        # print the deleted file
        print(Fore.RED + f'Deleted {file_path}' + Fore.WHITE)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')
    sys.exit()

flag = True

while flag:
    val = input("Song name + Artist: ")
    if val.lower() == "exit":
        sys.exit()
    elif val.lower() == "quit":
        sys.exit()
    val = val.replace(" ", "+")
    SAVE_PATH = 'songs'

    search_keyword=val
    html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + search_keyword)
    video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
    vidurls = ["https://www.youtube.com/watch?v=" + video_id for video_id in video_ids[:3]]

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl':SAVE_PATH + '/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,  
        'no_warnings': True, 
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        video_infos = [ydl.extract_info(vidurl, download=False) for vidurl in vidurls]

    for i, video_info in enumerate(video_infos, start=1):
        print(f"{i}: {video_info['title']}")
    choice = int(input(Fore.WHITE + "Choose the song to download: ")) - 1

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([vidurls[choice]])

    song_path = os.path.join(SAVE_PATH, video_infos[choice]['title'] + '.mp3')

    # load audio file
    loader = es.MonoLoader(filename=song_path)
    audio = loader()

    # extract the predominant melody
    pitch_extractor = es.PredominantPitchMelodia(frameSize=2048, hopSize=512)
    pitch_values, pitch_confidence = pitch_extractor(audio)

    # compute the Harmonic Pitch Class Profile (HPCP)
    hpcp_computer = es.HPCP()
    hpcp_values = hpcp_computer(pitch_values, pitch_confidence)

    # estimate the key using the HPCP
    key_computer = es.Key(profileType='edma')
    key, scale, strength, first_to_second = key_computer(hpcp_values)

    # print the estimated key
    print(Fore.GREEN + video_infos[choice]["title"] + ' - ' + Fore.YELLOW + f'{key} {scale} ({strength*100:.0f}%)' + Fore.WHITE)