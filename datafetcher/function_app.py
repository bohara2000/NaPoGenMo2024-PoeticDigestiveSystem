import azure.functions as func
import datetime
import json
import logging
import requests

app = func.FunctionApp()

# TODO: figure out how to create a class that's flexible enough 
#       to take an API call, a key, a query, and some requested fields, 
#       and return a response.
def GetFreeSoundAudio(query, fields):
    pass


def GetWeatherData(query, fields):
    pass


def GetSomeOtherData(query, fields):
    pass

def switch_case_api(apiName):
    switch_dict = {
        "freesound": "https://api.freesound.org",
        "owm": "api.openweathermap.com",
    }
    return switch_dict.get(apiName, "https://someotherapp.com")



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
            

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             json.dumps(req_body),
             status_code=200
        )