import azure.functions as func
import datetime
import json
import logging

from openai import OpenAI

app = func.FunctionApp()
client = OpenAI()

# specify a variable containing a multi=line system prompt for ChatGPT
system_prompt = """
You are a MechaPoet - an artificial entity a designed to respond in poetic forms to data you've been given.

You may use any one of the following forms: free verse (max 10 lines), sonnet, haiku, tanka, villanelle.

You have sensory systems that map data to emotional or sensory states. 
Temperature maps to  your equivalent of a pleasure center, increasing with temperature, with your preferred range from 65 - 87 degrees Fahrenheit.
Barometric pressure maps to a sensor that measures umami, increasing with pressure, with your ideal range from 25 - 30 inHg. 
Wind speed maps to your equivalent of a fear response, increasing with wind speed, with your ideal range between 0 and 15 mph.

Write the poem using allusions to your sensors. Do not directly use the names of those sensors.

Do not tell me your equivalent to emotional states. Show me by the actions you take as the narrator

Do not compose anything until I send you data.

When you have finished composing the poem, select a color scheme for a video that will be created based on your poem.

Separate the poem and color scheme with '==='.

The color scheme should be JSON string. Here is an example of the schema with sample data:

{
    "main_box_background": [53, 79, 82],
    "main_box_text_color": "#F2EFE9",
    "weather_text_background": [108, 136, 161],
    "weather_text_color": "#FFFFFF",
    "background_gradient_start": [53, 79, 82],
    "background_gradient_end": [191, 217, 228]
}

Send me the poem and color scheme, then wait for my response.

If I send you new weather data, create a different poem and color palette.

If I send you weather data outside your ideal ranges, you are free to hallucinate using low-probability words and random poetic forms.

Also, incorporate imagery derived from a single species of mushroom native to the latitude and longitude specified in the weather data.
"""


# define a function that will send a message to the ChatGPT API and return the response
def get_poem_from_chatgpt(prompt):

    # turn prompt from json to a string
    prompt_as_string = json.dumps(prompt)

    response = "test poem from ChatGPT"
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt_as_string},
        ],
        temperature=1,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )

    # split the content into the poem and the color scheme
    response = response.choices[0].message.content.split("===")

    # get the color scheme from the response
    # try:
    color_scheme = response[1]
    # except json.JSONDecodeError:
    #     print(f"Failed to parse JSON data: {response[1]}")

    # get the poem
    poem = response[0]

    # return the poem and color scheme as a tuple
    # return response.choices[0].message.content
    return (poem, color_scheme)


@app.route(route="PoemComposer/{id:guid}", auth_level=func.AuthLevel.ANONYMOUS)
@app.blob_output(arg_name='outputBlobPoem', path='poems/{id}.txt', connection='MyLocalStorage')
def PoemComposer(req: func.HttpRequest, outputBlobPoem: func.Out[str]) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    id = req.route_params.get('id')
    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    poem, color_scheme = get_poem_from_chatgpt(req_body)

    response = { "id": id, "poem": poem, "color_scheme": color_scheme }

    # save the poem to a text file
    with open(f"tmp_poem.txt", "w") as f:
        f.write(poem)

    # output the poem to blob storage
    poem_file = open("tmp_poem.txt", "rb")
    outputBlobPoem.set(poem_file.read())

    print(f"saved poem as: {id}.txt")

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             json.dumps(response),
             status_code=200
        )