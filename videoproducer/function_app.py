import azure.functions as func
import logging
import os
import moviepy.editor as mp
from moviepy.editor import TextClip, CompositeVideoClip


app = func.FunctionApp()

def paulstretch_audio(stretchpercentage):
    
    return None
    

def build_video(poem_text):
     # Define text for each line
    lines = [line.strip() for line in poem_text.split('\n\n')]

    # Create TextClip for each line of text
    text_clips = [TextClip(line, fontsize=70, color='white', bg_color='black').set_duration(3)
                  for line in lines]

    # Composite text clips into a single video clip
    final_clip = mp.concatenate_videoclips([clip.set_position(('center', 'center')) for clip in text_clips])

    # Write the video clip to BytesIO buffer
    audio_buffer = final_clip.write_videofile("tmp_vid.mp4", fps=24, codec='libx264')

    # Get the video bytes from the buffer
    #audio_bytes = audio_buffer.getvalue()

    # return bytes from buffer
    return "tmp_vid.mp4"



@app.queue_trigger(arg_name="azqueue", queue_name="weathermessages", connection="MyLocalStorage") 
@app.blob_output(arg_name='outputBlob', path='weathervids/{id}.mp4', connection='MyLocalStorage')
@app.blob_output(arg_name='outputBlobMp3', path='weathervids/{id}.mp3', connection='MyLocalStorage')
@app.blob_output(arg_name='outputPoem', path='poems/{id}.mp4', connection='MyLocalStorage')
def QueueExample(azqueue: func.QueueMessage, outputBlob: func.Out[str], outputBlobMp3: func.Out[str], outputPoem: func.Out[str]):
    logging.info('Python Queue trigger processed a message: %s',
                azqueue.get_body().decode('utf-8'))
    
    audio_tmp_filename = paulstretch_audio(1.5)

    if audio_tmp_filename != None:
        audio_file = open(audio_tmp_filename, "rb")
        outputBlobMp3.set(audio_file.read())
    
    video_tmp_filename = build_video(azqueue.get_body().decode('utf-8'))

    video_file = open(video_tmp_filename, "rb")
    outputBlob.set(video_file.read())
    
    outputPoem.set(azqueue.get_body().decode('utf-8'))
    
    # remove temporary video file
    if os.path.exists(audio_tmp_filename):
        logging.info('removing temp file: %s', audio_tmp_filename)
        os.remove(audio_tmp_filename)