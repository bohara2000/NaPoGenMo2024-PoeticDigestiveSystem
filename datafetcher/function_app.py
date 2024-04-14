import os
import random
import azure.functions as func
import json
import logging
import requests

# importing weather libraries
from geopy.geocoders import Nominatim

# importing audio libraries
import freesound

app = func.FunctionApp()

# Helper method for finding values within complex JSON objects
def find_value(json_obj, target_key):
    def item_generator(json_input, lookup_key):
        if isinstance(json_input, dict):
            for k, v in json_input.items():
                if k == lookup_key:
                    yield v
                else:
                    yield from item_generator(v, lookup_key)
        elif isinstance(json_input, list):
            for item in json_input:
                yield from item_generator(item, lookup_key)
                
                
    result_list = [i for i in item_generator(json_obj,target_key)]    
    return result_list
    


# TODO: figure out how to create a class that's flexible enough 
#       to take an API call, a key, a query, and some requested fields, 
#       and return a response.
def GetFreeSoundAudio(query, fields):
    # search freeesound.org for the search term
    client = freesound.FreesoundClient()
    client.set_token(os.environ['FREESOUND_API_KEY'],"token")

    results = client.text_search(query=query,fields=fields, filter="license:\"Creative Commons 0\"")
    resultlist = [result for result in results]
    # print (resultlist[0].duration)
    

    # pick a random audio file from the search results
    random_index = random.randint(0, len(resultlist) - 1)
    audio_file = resultlist[random_index]


    # download the audio file
    audio_file.retrieve_preview('.', audio_file.name)
    # print (audio_file)

    # TODO: place the audio file in blob storage, renaming it to something you can retrieve later
    #       or...pass the path from blob storage in the JSON results
    
    
    # create JSON file containing the name of the file, the username, and the license
    freesound_metadata = {
        "audio_file": audio_file.name,
        "username": audio_file.username,
        "license": audio_file.license,
        "duration": audio_file.duration
    }
    # freesound_metadata = f"Audio file: {audio_file.name}\nUsername: {audio_file.username}\nLicense: {audio_file.license}"

    # print(freesound_metadata)


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
    
    # convert pressure from hPa to inHg
    # because pyOWM requires a dictionary that I no longer retrieve
    def convert_hPa2inHg(pascal_value):
        return round(pascal_value * 0.02953, 2)

    try:
        # get location data based on city, state, and country
        geolocator = Nominatim(timeout=4, user_agent=os.environ["GEOPY_USER_AGENT_NAME"])
        
        # get the weather data for the specified location using the api key defined in the environment variables
        result = {}
        
        # get the city, state, and country of the location from the query string
        city = query["city"]
        state = query["state"]
        country = query["country"] 
        # print(json.dumps(query))
        
        # print(fields)
        
        max_retries = 3
        attempts = 0
        success = False
        location = ''
        
        while not success and attempts < max_retries:
            try:
                # Code block that may throw an exception
                location = geolocator.geocode(f"{city},{state}  {country}")
                # Imagine some code here that might fail
                success = True
            except Exception as e:
                attempts += 1
                # sleep(3)
                # print(f'Attempt {attempts}: {e}')
                location = geolocator.geocode(f"{city},{state}  {country}")
                # Log error or take corrective measures
        
        if success == False:
            raise Exception("no location found, possibly due to timeout issue ")
        
        weather_api_call = f"https://api.openweathermap.org/data/3.0/onecall?lat={location.latitude}&lon={location.longitude}&units=imperial&exclude=hourly,minutely,daily,alerts&appid={ os.environ['OWM_API_KEY'] }" 
        response = requests.get(weather_api_call)
        weather_data = response.json()
       
        # print(json.dumps(weather_data))
        
        for field in fields.split(','):
            # print(f"- {field}")
            value = find_value(weather_data, field)
            if isinstance(value, list) and len(value) > 0:
                result[field] = find_value(weather_data, field)[0]
            else:
                result[field] = find_value(weather_data, field)
                        
            if result[field] == None or (isinstance(result[field], list) and len(result[field]) == 0):
                    result[field] = query[field]
            # print(f"result - {result[field]}")
                    
        # adjust pressure
        # print(f"result = {json.dumps(result)}") 
        result["pressure"] = convert_hPa2inHg(result["pressure"])
        
        # print(result)
    except Exception as e:
        result = {
            "error": f"An error occurred: {str(e)}"
        }
        logging.info(json.dumps(result))
        raise e
    finally:
        return result


def GenerateSpeechFromTextElevenlabs(text, filename):
    # result = {}
    # try:       
    #     CHUNK_SIZE = 1024
    #     url = "https://api.elevenlabs.io/v1/text-to-speech/GBv7mTt0atIp3Br8iCZE"

    #     headers = {
    #     "Accept": "audio/mpeg",
    #     "Content-Type": "application/json",
    #     "xi-api-key": os.environ["ELEVENLABS_API_KEY"]
    #     }

        
    #     data = {
    #         "text": text,
    #         "model_id": "eleven_monolingual_v1",
    #         "voice_settings": {
    #             "stability": 0.5,
    #             "similarity_boost": 0.5
    #         }
    #     }
    
    #     response = requests.post(url, json=data, headers=headers)
    #     with open(filename, 'wb') as f:
    #         for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
    #             if chunk:
    #                 f.write(chunk)
                    
    #     result = {
    #         "audio_file": filename,
    #         "status": "success"
    #     }
    # except Exception as e:
    #     result = {
    #         "status": "error",
    #         "error": f"An error occurred: {str(e)}"
    #     }
    #     logging.info(json.dumps(result))
    #     raise e
    # finally:
    #     return result
    return None
    
def GetSomeOtherData(query, fields):
    return "nothing defined"

def switch_case_api(apiName, query, fields):
    # create a dictionary of the API names and the functions to call
    logging.info(f"apiName: {apiName}")
    switch_dict = {
        "freesound": GetFreeSoundAudio,
        "owm": GetWeatherData,
        "elevenlabs": GenerateSpeechFromTextElevenlabs
    }
    return switch_dict.get(apiName, GetSomeOtherData)(query, fields)



@app.route(route="DataFetcher/{id:guid}", methods=['POST'], auth_level=func.AuthLevel.ANONYMOUS)
@app.blob_output(arg_name='outputBlobMp3', path='weathervids/{id}.mp3', connection='VIDEO_POETRY_STORAGE')
def DataFetcher(req: func.HttpRequest, outputBlobMp3: func.Out[str]) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    id = req.route_params.get('id')
    print(f"id is {id}")
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
            logging.info(f"response: {json.dumps(response)}")
            response["id"] = id
            
    if api_to_call == 'freesound':
        preview_file = f"{response['audio_file']}.mp3"
        audio_file = open(preview_file, "rb")
        outputBlobMp3.set(audio_file.read())
        print(f"name: {id}.mp3")
        
        response['audio_blob_file'] =  f"{id}.mp3"
            
        
        # # remove temporary video file
        # if os.path.exists(preview_file):
        #     logging.info('removing temp file: %s', preview_file)
        #     os.remove(preview_file)
        #     # set audio file name to new file
        #     response['audio_file'] = outputBlobMp3.BlobName 
       
            

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             json.dumps(response),
             mimetype="application/json"
        )