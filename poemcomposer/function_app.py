import random
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
Barometric pressure maps to a sensor that measures %s, increasing with pressure, with your ideal range from 25 - 30 inHg. 
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
    tastes = ['sweetness', 'sourness', 'bitternes', 'saltiness', 'umami']
    # turn prompt from json to a string
    prompt_as_string = json.dumps(prompt)

    response = "test poem from ChatGPT"
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt % random.choice(tastes)},
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


# @app.route(route="PoemComposer/{id:guid}", methods=['POST'], auth_level=func.AuthLevel.ANONYMOUS)
# @app.queue_trigger(arg_name="azqueue", queue_name="weatherdata", connection="VIDEO_POETRY_STORAGE") 
# @app.blob_output(arg_name='outputBlobPoem', path='poems/{id}.txt', connection='VIDEO_POETRY_STORAGE')
# @app.queue_output(arg_name='queuePoem', queue_name='weathermessages', connection='VIDEO_POETRY_STORAGE')
# def PoemComposer(azqueue: func.QueueMessage, outputBlobPoem: func.Out[str], queuePoem: func.Out[str]):
#     logging.info('Python Queue trigger function processed a request.')
    
#     # create variable to hold message body
#     message_body = json.loads(azqueue.get_body().decode('utf-8'))
    

#     id = message_body['id']
    
#     poem, color_scheme = get_poem_from_chatgpt(message_body)

#     response = { "id": id, "poem": poem, "color_scheme": color_scheme, "weather_data": message_body}

#     # save the poem to a text file
#     with open(f"tmp_poem.txt", "w") as f:
#         f.write(poem)

#     # output the poem to blob storage
#     poem_file = open("tmp_poem.txt", "rb")
#     outputBlobPoem.set(poem_file.read())

#     print(f"saved poem as: {id}.txt")
    
#     # ouput the poem message to the queue
#     queuePoem.set(json.dumps(response))


@app.queue_trigger(arg_name="azqueue", queue_name="weatherdata",
                               connection="VIDEO_POETRY_STORAGE") 
@app.blob_output(arg_name='outputBlobPoem', path='poems/{id}.txt', connection='VIDEO_POETRY_STORAGE')
@app.queue_output(arg_name='queuePoem', queue_name='weathermessages', connection='VIDEO_POETRY_STORAGE')
def PoemComposer(azqueue: func.QueueMessage, outputBlobPoem: func.Out[str], queuePoem: func.Out[str] ):
    logging.info('Python Queue trigger processed a message: %s',
                azqueue.get_body().decode('utf-8'))
    
    # create variable to hold message body
    message_body = json.loads(azqueue.get_body().decode('utf-8'))
    

    id = message_body['id']
    
    poem, color_scheme = get_poem_from_chatgpt(message_body)

    response = { "id": id, "poem": poem, "color_scheme": color_scheme, "weather_data": message_body}

    # save the poem to a text file
    with open(f"tmp_poem.txt", "w") as f:
        f.write(poem)

    # output the poem to blob storage
    poem_file = open("tmp_poem.txt", "rb")
    outputBlobPoem.set(poem_file.read())

    print(f"saved poem as: {id}.txt")
    
    # ouput the poem message to the queue
    queuePoem.set(json.dumps(response))
