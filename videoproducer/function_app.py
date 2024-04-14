import glob
import json
import random
import azure.functions as func
import logging
import os

# importing movie py and its supporting libraries
from PIL import Image, ImageDraw
import numpy as np
import moviepy.editor as mp
from moviepy.editor import TextClip, CompositeVideoClip, ColorClip, ImageClip
import requests

# importing audio libraries
import freesound
import glob

app = func.FunctionApp()

def paulstretch_audio(stretchpercentage):
    
    return None


# searches for and downloads a Freesound.org audio file
def download_freesound_audio(search_term, duration):
    # search freeesound.org for the search term
    client = freesound.FreesoundClient()
    client.set_token(os.environ['FREESOUND_API_KEY'],"token")

    results = client.text_search(query=search_term,fields="id,name,duration,username,license,previews", filter="license:\"Creative Commons 0\"")
    resultlist = [result for result in results]
    #print (resultlist[0].duration)
    

    # pick a random audio file from the search results
    random_index = random.randint(0, len(resultlist) - 1)
    audio_file = resultlist[random_index]


    # download the audio file
    audio_file.retrieve_preview('.', audio_file.name)
    print (audio_file.name)

    # create an TextClip containing the name of the file, the username, and the license
    freesound_metadata = f"Audio file: {audio_file.name}\nUsername: {audio_file.username}\nLicense: {audio_file.license}"

    print(freesound_metadata)


    # create a loop of the downloaded audio file until it is the same duration as the video file
    # get the duration of the downloaded audio file
    audio_file_duration = audio_file.duration

    # create a new audio file that is the concatenation of the original audio file repeated the number of times calculated above
    # append mp3 to the end of the audio file name if it is not already there
    if not audio_file.name.endswith(".mp3"):
      audio_file.name += ".mp3"
    newaudio_file = mp.AudioFileClip(audio_file.name)
    # reduce the volume of the new audio file
    newaudio_file = newaudio_file.fx(mp.afx.volumex, 0.5)

    audio = mp.afx.audio_loop(newaudio_file, duration=duration)
    
    # remove the original audio file
    os.remove(audio_file.name)

    # return the path to the downloaded audio file
    return (audio, freesound_metadata)


def generate_speech_from_text_elevenlabs(text, filename):
    CHUNK_SIZE = 1024
    url = "https://api.elevenlabs.io/v1/text-to-speech/GBv7mTt0atIp3Br8iCZE"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": os.environ["ELEVENLABS_API_KEY"],
    }

    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
    }

    response = requests.post(url, json=data, headers=headers)
    with open(filename, "wb") as f:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            if chunk:
                f.write(chunk)


def get_gradient_2d(start, stop, width, height, is_horizontal):
    if is_horizontal:
        return np.tile(np.linspace(start, stop, width), (height, 1))
    else:
        return np.tile(np.linspace(start, stop, height), (width, 1)).T

def get_gradient_3d(width, height, start_list, stop_list, is_horizontal_list):
    result = np.zeros((height, width, len(start_list)), dtype=float)

    for i, (start, stop, is_horizontal) in enumerate(zip(start_list, stop_list, is_horizontal_list)):
        result[:, :, i] = get_gradient_2d(start, stop, width, height, is_horizontal)

    return result


# Create a function to generate a gradient clip


def create_gradient_clip(size, start_color, end_color):
    width, height = size
    # img = Image.new("RGB", size, color=start_color)
    # draw = ImageDraw.Draw(img)

    # # Add a gradient to the background
    # for x in range(width):
    #     for y in range(height):
    #         color = tuple(
    #             int(start_color[i] + (end_color[i] - start_color[i]) * x / width)
    #             for i in range(3)
    #         )
    #         draw.point((x, y), fill=color)
    array = get_gradient_3d(width, height, start_color, end_color, (True, False, False))
    Image.fromarray(np.uint8(array)).save('text_image.png', quality=95)
    
    # Save the image
    # img.save("text_image.png")

    # Create a video clip from the image
    return ImageClip("text_image.png", duration=1)

# Create a function to generate text clips with padding in specified colors
def create_clip_in_box(
    text, foreground_color, background_color=(140, 140, 140), font_size=24, align="West"
):
    # Create the weather text clip
    # text_clip = create_text_clip(text, width, height, background_color, foreground_color, font_size, align).set_position((20, 20))
    text_clip = TextClip(
        text,
        fontsize=font_size,
        color=foreground_color,
        align=align,
    )

    txt_width, txt_height = text_clip.size
    # Create a gray background for the weather data at 50% opacity
    padding_box_clip = ColorClip(
        size=(int(txt_width + 2*font_size), int(txt_height + 2*font_size)),
        color=background_color,
    )

    # offset the text clip to center it in the padding box
    text_clip = text_clip.set_position((font_size, font_size))

    # Composite the weather data and background clips
    padded_text_clip = mp.CompositeVideoClip([padding_box_clip, text_clip])
    return padded_text_clip


def build_video(poem_data):

    # Define default color palette
    main_box_background = (53, 79, 82)
    main_box_text_color = "#F2EFE9"
    # main_box_accent_color = "#D9BF77"
    # small_box_background = (108, 136, 161)
    weather_text_color = "#FFFFFF"
    # small_box_accent_color = "#BFD9E4"
    background_gradient_start = (53, 79, 82)  # Dark color at the top
    # background_gradient_middle = (108, 136, 161)  # Middle color
    background_gradient_end = (191, 217, 228)  # Light color at the bottom

    # get the id from the poem_data
    id = poem_data['id']

    # Get the poem text, color scheme, and weather data from the message body
    poem_text = poem_data['poem']
    color_scheme = poem_data['color_scheme']
    weather_data = poem_data['weather_data']    
    city = weather_data['city']
    state = weather_data['state']
    country = weather_data['country']

    logging.info("color_scheme: %s", color_scheme)

    # set the color scheme based on the response from ChatGPT
    main_box_background = tuple(color_scheme["main_box_background"])
    main_box_text_color = color_scheme["main_box_text_color"]
    weaather_text_background = tuple(color_scheme["weather_text_background"])
    weather_text_color = color_scheme["weather_text_color"]
    background_gradient_start = tuple(color_scheme["background_gradient_start"])
    background_gradient_end = tuple(color_scheme["background_gradient_end"])

    # Define video dimensions
    width = 1080
    height = 768

    # Log the poem generated by ChatGPT
    logging.info("Color scheme: %s", color_scheme)

    # split the poem into lines using the newline character
    verses = poem_text.split("\n\n")

    # print the last verse
    logging.info("Last verse: %s", verses[-1])

    # Define default text for each line
    lines = [
        "Line 1: Text for line 1",
        "Line 2: Text for line 2",
        "Line 3: Text for line 3",
    ]

    # if the poem has lines in it, replace the default lines with the lines from the poem
    if len(verses) > 0:
        lines = verses

    # create a background clip for the video
    # bg_clip = mp.ColorClip(size=(1920, 1080), color=(0, 0, 0), duration=3 * len(lines))
    # Create a gradient clip (NOTE: NEED TO WAIT UNTIL A DOCKER CONTAINER IS AVAILABLE TO TEST THIS)
    bg_clip = create_gradient_clip(
        (width, height), background_gradient_end, background_gradient_start
    ).set_duration(3 * len(lines))

    # Create small box text clip
    weather_text = f"Location: {city}, {state}  {country}\nLat: {weather_data['lat']}, Lon: {weather_data['lon']}\nTemperature: {weather_data['temp']} F\nBarometric Pressure: {weather_data['pressure']} inHg\nWind Speed: {weather_data['wind_speed']} mph"
    weather_clip = create_clip_in_box(weather_text, weather_text_color, weaather_text_background)

    # loop through the lines and create text clips with audio for each line
    text_clips = []
    for i, line in enumerate(lines):

        # skip empty lines
        if len(line.strip()) == 0:
            continue

        # Generate speech from text for each line
        speech_filename = f"speech_{id}_{i}.wav"

        # NOTE (4/11/2024 BKO) - looks like I need to call the Eleven Labs API from this function to generate the speech, 
        #                        otherwise I have to store it in the blob storage and pass the filename to the function
        #                        I will most likely do that later, but for now, I will generate the speech here
        generate_speech_from_text_elevenlabs(line.strip(), speech_filename)

        # Load the speech clip
        speech_clip = mp.AudioFileClip(speech_filename)

        text_clip = create_clip_in_box(
            line, main_box_text_color, main_box_background, font_size=48
        )

        # set the duration to the length of the speech clip and add crossfade effects plus two seconds of padding
        text_clip = (
            text_clip.set_duration(speech_clip.duration + 2)
            .set_position((100, 100))            
            .crossfadein(0.5)
            .crossfadeout(0.5)
        )

        # Add the speech clip to the text clip
        text_clip = text_clip.set_audio(speech_clip)

        # Add the text clip to the list of text clips
        text_clips.append(text_clip)

    # Composite text clips into a single video clip
    total_txt_clips = (
        mp.concatenate_videoclips(text_clips, method="compose")
        .set_position((50, height/4))
    )    

    weather_clip = (
        weather_clip.set_position(("right", "top"))
        .set_duration(total_txt_clips.duration)
        .crossfadein(0.5)
        .crossfadeout(0.5)
    ).set_position((width - weather_clip.size[0] - 50, 50))

    # set the duration of the background clip and weather clip to match the total text clip
    # bg_clip = bg_clip.set_duration(total_txt_clips.duration)
    bg_clip = (
        bg_clip.set_duration(total_txt_clips.duration)
        .set_opacity(0.4)
        .crossfadein(0.5)
        .crossfadeout(0.5)
    )

    # generate a background audio clip for the video using the make_bg_audio_clip function
    # bg_audio_clip = make_bg_audio_clip(total_txt_clips.duration)
    # NOTE (4/11/2024 BKO) - Let's try using DataFetcher to get the audio clip
    # NOTE (4/12/2024 BKO) - Well, that didnt work. The call saved the audio file to the directory of 
    #                        the function app and to blob storage. 
    #                        Given my time constraint, I'm going to reuse my earlier download_freesound_audio function
    bg_audio_clip, cc_attributes = download_freesound_audio("natural-soundscape,ambient", total_txt_clips.duration)

    # set the audio for the background clip
    bg_clip = bg_clip.set_audio(bg_audio_clip)

    # Create a clip for the Creative Commons attributes
    cc_clip = create_clip_in_box(cc_attributes, weather_text_color, font_size=16)

    # Add the Creative Commons clip
    cc_clip = (
        cc_clip.set_position((width - cc_clip.size[0] - 50, height - cc_clip.size[1] - 50))
        .set_duration(total_txt_clips.duration)
        .crossfadein(0.5)
        .crossfadeout(0.5)
    )

    # Composite the background clip, text clip, and weather clip
    final_clip = mp.CompositeVideoClip(
        [bg_clip, total_txt_clips, weather_clip, cc_clip],
        size=(width, height),
        bg_color=(0, 0, 0),
    )

    # save video to blob storage
    tmp_filename = f"tmp_vid_{id}.mp4"
    final_clip.write_videofile(tmp_filename, fps=24, codec="libx264")

    # return bytes from buffer
    return tmp_filename


@app.queue_trigger(arg_name="azqueue", queue_name="weathermessages", connection="VIDEO_POETRY_STORAGE") 
@app.blob_output(arg_name='outputBlob', path='weathervids/{id}.mp4', connection='VIDEO_POETRY_STORAGE')
@app.queue_output(arg_name='outputPoem', queue_name='videomessages', connection='VIDEO_POETRY_STORAGE')
def QueueExample(azqueue: func.QueueMessage, outputBlob: func.Out[str], outputPoem: func.Out[str]):
    logging.info('Python Queue trigger processed a message: %s',
                azqueue.get_body().decode('utf-8'))
    
    # audio_tmp_filename = paulstretch_audio(1.5)

    # if audio_tmp_filename != None:
    #     audio_file = open(audio_tmp_filename, "rb")
    #     outputBlobMp3.set(audio_file.read())
    
    # create a variable to hold the message body
    message_body = json.loads(azqueue.get_body().decode('utf-8'))
    
    color_scheme = json.loads(message_body['color_scheme'])
    message_body['color_scheme'] = color_scheme
    
    print(f"color scheme: {color_scheme}")

    # 04/11/2024 - for now, let's assume build_video does all the rendering and returns a filename
    video_tmp_filename = build_video(message_body)

    video_file = open(video_tmp_filename, "rb")
    outputBlob.set(video_file.read())
    
    # remove temporary video file
    if os.path.exists(video_tmp_filename):
        logging.info('removing temp file: %s', video_tmp_filename)
        os.remove(video_tmp_filename)

    # create a message to pass to the next queue indicating the video is ready
    message_body['video'] = f"{message_body['id']}.mp4"

    outputPoem.set(json.dumps(message_body))
    
    logging.info('Python Queue trigger function processed a message: %s', message_body)
