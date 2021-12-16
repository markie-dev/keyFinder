import yt_dlp
import urllib.request
import re
import os
import warnings
import sys
import essentia
from essentia.streaming import *
import colorama
from colorama import Fore


warnings.filterwarnings("ignore", category=UserWarning) 
flag = True

while flag:
    val = input("Song name + Artist: ")
    if val == "quit":
        exit()
    val = val.replace(" ", "+")
    SAVE_PATH = '/home/markie/Songs'

    search_keyword=val
    html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + search_keyword)
    video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
    # Get URL for the first search result in Youtube that matches our search
    vidurl = "https://www.youtube.com/watch?v=" + video_ids[0]

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl':SAVE_PATH + '/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(vidurl, download=True)
        filename = ydl.prepare_filename(info)
    shortFileName = os.path.splitext(filename)[0]
    realFileName = shortFileName + ".mp3"

    loader = MonoLoader(filename=realFileName)
    framecutter = FrameCutter()
    windowing = Windowing(type="blackmanharris62")
    spectrum = Spectrum()
    spectralpeaks = SpectralPeaks(orderBy="magnitude",
                                magnitudeThreshold=1e-05,
                                minFrequency=40,
                                maxFrequency=5000, 
                                maxPeaks=10000)
    hpcp = HPCP()
    key = Key()

    # use pool to store data
    pool = essentia.Pool() 

    # connect algorithms together
    loader.audio >> framecutter.signal
    framecutter.frame >> windowing.frame >> spectrum.frame
    spectrum.spectrum >> spectralpeaks.spectrum
    spectralpeaks.magnitudes >> hpcp.magnitudes
    spectralpeaks.frequencies >> hpcp.frequencies
    hpcp.hpcp >> key.pcp
    key.key >> (pool, 'tonal.key_key')
    key.scale >> (pool, 'tonal.key_scale')
    key.strength >> (pool, 'tonal.key_strength')

    # network is ready, run it
    print("Finding Key...")
    essentia.run(loader)
    
    shortName = realFileName.split("/home/markie/Songs/",1)[1]
    print("")
    print(Fore.CYAN + shortName + Fore.WHITE + " - " + Fore.GREEN + pool['tonal.key_key'] + " " + pool['tonal.key_scale'] + Fore.WHITE)
    print("")

