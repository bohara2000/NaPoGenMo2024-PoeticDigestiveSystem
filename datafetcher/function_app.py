import os
import random
import azure.functions as func
import datetime
import json
import logging
import requests

# importing weather libraries
from pyowm import OWM
from pyowm.utils import measurables

# importing audio libraries
import freesound
import glob

app = func.FunctionApp()

# TODO: figure out how to create a class that's flexible enough 
#       to take an API call, a key, a query, and some requested fields, 
#       and return a response.
def GetFreeSoundAudio(query, fields):
    # search freeesound.org for the search term
    client = freesound.FreesoundClient()
    client.set_token(os.environ['FREESOUND_API_KEY'],"token")

    results = client.text_search(query=query,fields=fields, filter="license:\"Creative Commons 0\"")
    resultlist = [result for result in results]
    #print (resultlist[0].duration)
    

    # pick a random audio file from the search results
    random_index = random.randint(0, len(resultlist) - 1)
    audio_file = resultlist[random_index]


    # download the audio file
    audio_file.retrieve_preview('.', audio_file.name)
    # print (audio_file)

    # create JSON file containing the name of the file, the username, and the license
    freesound_metadata = {
        "audio_file": audio_file.name,
        "username": audio_file.username,
        "license": audio_file.license,
        "duration": audio_file.duration
    }
    # freesound_metadata = f"Audio file: {audio_file.name}\nUsername: {audio_file.username}\nLicense: {audio_file.license}"

    print(freesound_metadata)


    # create a loop of the downloaded audio file until it is the same duration as the video file
    # get the duration of the downloaded audio file
    audio_file_duration = audio_file.duration

    # # create a new audio file that is the concatenation of the original audio file repeated the number of times calculated above
    # # append mp3 to the end of the audio file name if it is not already there
    # if not audio_file.name.endswith(".mp3"):
    #   audio_file.name += ".mp3"
    # newaudio_file = mp.AudioFileClip(audio_file.name)
    # # reduce the volume of the new audio file
    # newaudio_file = newaudio_file.fx(mp.afx.volumex, 0.5)

    # audio = mp.afx.audio_loop(newaudio_file, duration=duration)
    
    # # remove the original audio file
    # os.remove(audio_file.name)

    # return the path to the downloaded audio file
    return (freesound_metadata)


def GetWeatherData(query, fields):
    # get the weather data for the specified location using the api key defined in the environment variables
    owm = OWM(os.environ["OWM_API_KEY"])
    mgr = owm.weather_manager()
    observation = mgr.weather_at_place(query)

    # get the city, state, and country of the location from the query string
    city = fields["city"]
    state = fields["state"]
    country = fields["country"]

    response = {
        "city": city,
        "state": state,
        "country": country,
        "latitude": observation.location.lat,
        "longitude": observation.location.lon,
        "temperature": observation.weather.temperature("fahrenheit")["temp"],
        "barometric_pressure": measurables.metric_pressure_dict_to_inhg(
            observation.weather.pressure
        )["press"],
        "wind_speed": round(measurables.metric_wind_dict_to_imperial(
            observation.weather.wind()
        )["speed"],1),
    }

    return response


def GetSomeOtherData(query, fields):
    pass

def switch_case_api(apiName, query, fields):
    # create a dictionary of the API names and the functions to call
    switch_dict = {
        "freesound": GetFreeSoundAudio,
        "owm": GetWeatherData,
    }
    return switch_dict.get(apiName, GetSomeOtherData)(query, fields)



@app.route(route="DataFetcher", auth_level=func.AuthLevel.ANONYMOUS)
def DataFetcher(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            api_to_call = req_body.get('api_name')
            query = req_body.get('query')
            fields = req_body.get('fields')
            response = switch_case_api(api_to_call, query, fields)
            

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             json.dumps(response),
             status_code=200
        )