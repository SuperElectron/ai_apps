from openai import OpenAI
from base64 import b64encode
from os import getenv
from json import loads

api_key = getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError("OPENAI_API_KEY not found")

client = OpenAI(api_key=api_key)


# Define the function to analyze an image with GPT-4
def analyze_image(image_path, img_type: str='image/jpg'):
    # Read the image file in binary mode
    with open(image_path, 'rb') as image_file:
        image_data = image_file.read()

    # Encode the image to base64
    img_b64_str = b64encode(image_data).decode('utf-8')

    # Create the prompt for analysis
    prompt = (
        "Can you find a face in this image?  Are the people smiling?  \n"
        "Your response should be in JSON format. \n"
        "Please structure your reply in dict format as follows:\n"
        "{ 'n_people': 'add number here', 'n_smiling': 'add number here'}"
    )

    # Send the request to OpenAI

    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{img_type};base64,{img_b64_str}"
                        },
                }
            ],
        }],
        response_format={"type": "json_object"}
    )

    # Extract and return the response content
    r = response.choices[0].message.content
    return loads(r)

if __name__ == "__main__":
    # Example usage
    file_path = "images/smile.jpg"
    _ret = analyze_image(file_path)
    print(_ret)
    print(type(_ret))

    file_path = "images/not_smile.jpg"
    _ret = analyze_image(file_path)
    print(_ret)
    print(type(_ret))
