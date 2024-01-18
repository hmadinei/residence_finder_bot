import os
import replicate
import re
import math

os.environ['REPLICATE_API_TOKEN'] = ''
token = os.environ.get('REPLICATE_API_TOKEN')


def request_llama(query):
    
    print("Start Requesting....")
    output = replicate.run(
        "meta/llama-2-70b-chat:2d19859030ff705a87c746f7e96eea03aefb71f166725aee39692f1476566d48",
        input={
            "debug": False,
            "top_p": 1,
            "temperature": 0.5,
            "prompt":f"Process the following user query and extract specific information to answer predefined filter questions. Ensure the answers conform to the specified formats. If the query does not provide enough information for a particular filter, respond with 'Not specified'. User quesry: {query}. Based on the query, answer these filter questions: People Capacity: 'How many people should be in your house? 'Answer Format: A number (e.g., 2, 4). If not specified in the query, respond with 'Not specified'. Rate Score: 'Is it appropriate to have a residence rating of above?' Answer Format: A number representing the rating (e.g., 4.5, 5). If the rating criteria are not mentioned in the query, respond with 'Not specified'. Area Size: 'How many meters should the residence be between?' Answer Format: Start with 'BETWEEN', followed by a number, the word 'and', and another number or 'infinity' (e.g., 'BETWEEN 50 and 100', 'BETWEEN 30 and infinity'). If the area size is not specified, respond with 'Not specified'.",
            # "prompt": f"User querys this: {query}. Try to find these filters from it: capacity, rate score and area size. Please assign just a number to each filter and use above and below and between if necessary. Some filter may not be mentioned in the query. Feel fre to assign N/A to them.",
            # "system_prompt": "You are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe. Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. Please ensure that your responses are socially unbiased and positive in nature.\n\nIf a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information.",
            "system_prompt": "This prompt guides the user to provide their requirements in a structured way that makes it easier to parse the desired information using regex or other text processing methods. By specifying the expected format, you increase the likelihood of receiving the information in a consistent and usable form.",
            "max_new_tokens": 500,
            "min_new_tokens": -1,
        }
    )
    
    print("request fininshed.")
    full_response = ""
    for item in output:
        full_response += item
        
    print(full_response)
    return full_response



def parse_request(query_response):
    query_response = query_response.lower()
    
    # patterns
    capacity_pattern = r"capacity:.*?(\d+(\.\d+)?)"
    rate_score_pattern = r"rate score:.*?(\d+(\.\d+)?)"
    area_size_pattern = r"area size:.*?between (\d+(\.\d+)?)( and (\d+(\.\d+)?)| and infinity)?"

    # search and extract
    capacity_match = re.search(capacity_pattern, query_response)
    rate_score_match = re.search(rate_score_pattern, query_response)
    area_size_match = re.search(area_size_pattern, query_response)

    # assign values or NaN
    capacity = float(capacity_match.group(1)) if capacity_match else float('nan') 
    rate_score = float(rate_score_match.group(1)) if rate_score_match else float('nan')

    # assign values to Area Size
    if area_size_match:
        start_area_size = float(area_size_match.group(1))
        end_area_size = float(area_size_match.group(4)) if area_size_match.group(4) else 10000
    else:
        start_area_size, end_area_size = float('nan'), float('nan')

    # output
    print("Capacity:", capacity)
    print("Rate Score:", rate_score)
    print("Area Size:", start_area_size, end_area_size)
    
    result = {}
    if not math.isnan(capacity):
        result['CapacityBase'] = int(capacity)
        
    if not math.isnan(rate_score):
        result['RateScore'] = float(rate_score)
        
    if not math.isnan(start_area_size):
        start_area_size = int(start_area_size)
        end_area_size= int(end_area_size)
        result['AreasSize'] = (start_area_size, end_area_size)
        
    return result

    
if __name__=='__main__':
    # for test
    res = request_llama('A house below 300 meters and for 2 people')
    parse_request(res)
    
    # parse_request(""" Sure! Here are the answers to the filter questions based on the user query:

    #                 Capacity: The query specifies that the house should accommodate 2 people. Therefore, the answer to this filter question is 2.      

    #                 Rate Score: The query does not mention anything about the residence rating, so the answer to this filter question is Not specified.
    #                 Area Size: The query mentions that the house should be below 300 meters. Therefore, the answer to this filter question is BETWEEN 300""")
    




