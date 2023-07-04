from django.shortcuts import render
from django.http import JsonResponse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers

import json
import openai
import urllib.request
import os
import re
import lxml.html
import lxml
from langchain.text_splitter import RecursiveCharacterTextSplitter
from lxml.html.clean import Cleaner
from bs4 import BeautifulSoup


openai.api_key  =  "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"

def index(request):
    return HttpResponse('<h1>Hello World</h1>')

def get_completion(prompt, model="gpt-3.5-turbo"):
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0, # this is the degree of randomness of the model's output
    )
    return response.choices[0].message["content"]
def construct_unique_json(json_array):
    # Create an empty dictionary to hold the combined JSON object
    combined_json = {}

    # Iterate over each JSON string in the array
    for json_str in json_array:
        # Parse the JSON string into a dictionary
        json_obj = json.loads(json_str)
        for key, value in json_obj.items():
            # Drop the key if the value is "unknown" or "unavailable"
            if key in combined_json:
                continue
                
            if isinstance(value, str) and( value.lower() == "unknown" or "unavailable" in value.lower()) :
                continue

            # Add the key-value pair to the combined JSON object
            if isinstance(value, str):
                value = " ".join(value.split())
            
            combined_json[key] = value

    # Convert the combined JSON object back to a JSON string
    combined_json_str = json.dumps(combined_json, indent=2)
    return combined_json_str
@csrf_exempt
def my_api_view(request):
    if request.method == 'POST':
        try:
            cleaner = Cleaner()
            cleaner.javascript = True # This is True because we want to activate the javascript filter
            cleaner.style = True
            webPart = []
            webPartWithoutScript = []
            body = json.loads(request.body)
            url = body.get('url')

            API_KEY = '11155d4f6518c67a2284d3c95e5fbdf3'
            mysite = urllib.request.urlopen("http://api.scraperapi.com/?api_key=%s&url=%s" % (API_KEY,url)).read()
            
            lxml_mysite = lxml.html.fromstring(mysite)
            withoutScript2 = cleaner.clean_html(lxml_mysite)
            wttext = withoutScript2.text_content()
            print(len(wttext))

            page = lxml_mysite.xpath("//div[contains(@id,'centerCol') or contains(@id,'merchant-info') or contains(@id,'detail') or contains(@id,'prodDetails')]") # meta tag description
                
            for x in page:
                webPart.append(x.text_content())
                withoutScript = cleaner.clean_html(x)
                webPartWithoutScript.append(withoutScript.text_content())
                
            webPart1 = " ".join(webPart);
            webPartWithoutScript1 = " ".join(webPartWithoutScript);
            
            print(len(webPart1))
            print(len(webPartWithoutScript1))

            soup = BeautifulSoup(webPartWithoutScript1)
            demo_text = soup.get_text()

            demo_text1 = " ".join(demo_text.split())

            print(len(demo_text))
            print(len(demo_text1))

            regex = re.compile(r'<[^>]+>')
            demo_text2 = regex.sub('', demo_text1)
            print(len(demo_text2))


            text_splitter = RecursiveCharacterTextSplitter(
                # Set a really small chunk size, just to show.
                chunk_size = 10000,
                chunk_overlap  = 10,
                length_function = len,
                add_start_index = True,
            )

            texts = text_splitter.create_documents([demo_text2])

            print(len(texts))

            lst = []
            for i in range(len(texts)):
                prompt = f"""
                Your task is to extract relevant information from \ 
                a product content from an ecommerce site .

                From the page content below, delimited by triple quotes \
                extract the below information relevant to product like. 
                1) product_name
                2) selling price
                3) Asin
                4) rating
                5) number of reviews
                6) product summary
                7) summarize delivery detail
                8) brand_name
                9) product color
                10) seller detail like seller name and location
                11) model number
                12) list price
                13) discount
                14) summarize return and replacement detail
                
                
                Use the following format:
                    list price: <Integer>
                    selling price: <Integer>
                    discount: <percentage>
                    Asin: <Integer>
                    rating: <float>
                    reviews: <Integer>
                    model_number:<Integer>

                
                If the information isn't present, use "unknown" \
                    as the value.
                provide output in json format.
                Make your response as short as possible.


                page content: ```{texts[i].page_content} """
                response = get_completion(prompt)
                if not ('Sorry' in response):
                    lst.append(response)
                print(response, "\n")

            combined_json = construct_unique_json(lst)
            print("Combined JSON:")
            print(combined_json)
            response_data = {'message': 'Post request successful', 'data': eval(combined_json)}
            return JsonResponse(response_data)
        except json.JSONDecodeError:
            response_data = {'message': 'Invalid JSON payload'}
            return JsonResponse(response_data, status=400)
    else:
        # Handle other HTTP methods (optional)
        response_data = {'message': 'Invalid request method'}
        return JsonResponse(response_data)
