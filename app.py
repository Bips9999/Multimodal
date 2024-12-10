import streamlit as st
from PIL import Image
import hashlib
import io
from sentence_transformers import SentenceTransformer
from PIL import Image
import requests
from pathlib import Path
from IPython.display import Image as IPImage, display
import weaviate
import weaviate.classes as wvc
from weaviate.util import generate_uuid5
import os
from dotenv import load_dotenv
from utils import *
import uuid
import json
load_dotenv()

# import os
# os.getenv["KMP_DUPLICATE_LIB_OK"]="TRUE"

img_model = SentenceTransformer('clip-ViT-B-32')
text_model = SentenceTransformer('clip-ViT-B-32-multilingual-v1')

# Define the directory where images will be saved
SAVE_DIR_IMG = 'uploaded_images'
SAVE_DIR_TXT = 'saved_texts'
# Make sure the directory exists
os.makedirs(SAVE_DIR_IMG, exist_ok=True)


# Make sure the directory exists
os.makedirs(SAVE_DIR_TXT, exist_ok=True)

product_img_dir = Path(r"C:\Users\bipsr\Desktop\Capstone\archive (1)\IMGS")
product_img_paths = [str(p) for p in product_img_dir.glob("*.jpg")]


######## Creating client to connect to weaviate instance on cloud ################
client = weaviate.Client(
    url=os.getenv("WEAVIATE_URL"),
    auth_client_secret=weaviate.auth.AuthApiKey(api_key=os.getenv("WEAVIATE_API_KEY")),
)
print(client.is_ready())

# Creating the class Schema

# class_obj = {
#     "class": "multimodality",
#     "vectorizer": "text2vec-openai",  # set your vectorizer module
#     "moduleConfig": {
#         "generative-openai": {
#             "model": "gpt-4"
#         }
#     }, 
#     "properties": [
#         {"name": "file_path",
#             "dataType": ["text"]
#             },
#         {"name": "img_source",
#             "dataType": ["text"]
#             },
#         {"name": "image",
#             "dataType": ["blob"]
#             },
#     ]
# }

# client.schema.create_class(class_obj)

################# Adding the objects to the class #########################

# class_name = "mmultimodality"
# client.batch.configure(batch_size=100)  # Configure batch
# with client.batch as batch:
#     for img_set in [
#         (product_img_paths, "TMDB"),
#     ]:
#         for img_path in img_set[0][:100]:
#             vector = img_model.encode([load_image(img_path)])[0].tolist()
#             img_b64 = to_base64(img_path)
#             image_hash = get_image_hash(img_path)
            
#             properties={
#                 "file_path":img_path,
#                 "image":img_b64,
#                 "img_source": img_set[1],
#                 "image_hash": image_hash
#             }

#             batch.add_data_object(
#             properties,
#             class_name,
#             vector=vector,
#             uuid=generate_uuid5(img_path)  # Optional: Specify an object vector  
#         )



def get_image_hash(image_path):
    """
    Generate a hash for the image to check for duplicates.
    """
    # Open the image and generate a hash based on the image content
    with open(image_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

# Function to process the image
def process_image(image):
    # Example: Just return the image size as a placeholder response
    img = Image.open(image)
    width, height = img.size
    return f"Image size is {width}x{height} pixels"

# Function to process the text input
def process_text(text):
    # Example: Return a simple uppercase version of the text
    return f"Processed Text: {text.upper()}"

# Title of the app
st.title("Streamlit App: Image or Text Input")


############## FOR REAL TIME INDEX UPDATES ###################
#image_path = r"C:\Users\bipsr\Desktop\Capstone\archive (1)\Actual dataset\55197.jpg"
image_path = r"C:\Users\bipsr\Downloads\download (1).jpeg"
classname="mmultimodality"

def get_image_hash(image_path):
    """
    Generate a hash for the image to check for duplicates.
    """
    # Open the image and generate a hash based on the image content
    with open(image_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def check_image_exists(image_hash):
    """
    Check if the image already exists in the Weaviate database using the image hash.
    """
    result = client.query.get("Mmultimodality", ["file_path"]).with_where({
        "path": ["file_path"],
        "operator": "Equal",
        "valueString": image_hash
    }).do()
    print(result)
    print(len(result["data"]["Get"]["Mmultimodality"]))
    if len(result["data"]["Get"]["Mmultimodality"]) > 0:
        return 1
    else:
        return 0

def ingest_image(image_path):
    """
    Function to ingest image embeddings into Weaviate only if the image doesn't already exist.
    """
    # Generate a unique hash for the image
    image_hash = get_image_hash(image_path)
    print(image_hash)
    
    # Check if the image already exists in the database
    if check_image_exists(image_hash) == 1:
        print(f"Image {image_path} already exists in the database. Skipping ingestion.")
        return
    
    # Get the image embedding
    embedding = img_model.encode([load_image(image_path)])[0].tolist()
    img_b64 = to_base64(image_path)
    
    # Create the data to store in Weaviate
    properties={
                "file_path":image_path,
                "image":img_b64,
                "img_source": image_path
            }
    
    # Ingest the image embedding into Weaviate
    client.batch.add_data_object(
            properties,
            classname,
            vector=embedding,
            uuid=generate_uuid5(image_path)  # Optional: Specify an object vector
        )
    print(f"Image {image_path} ingested successfully.")

  # Replace with your image file path
ingest_image(image_path)



# Radio buttons for choosing input type
input_type = st.radio("Choose Input Type", ["Image", "Text"])

# If the user selects "Image", provide an image uploader
if input_type == "Image":
    uploaded_image = st.file_uploader("Upload an image", type=["jpg", "png", "jpeg"])
    
    if uploaded_image is not None:
        # Save the uploaded image to the local directory
        saved_image_path = save_image_to_local(uploaded_image, SAVE_DIR_IMG)
        query = load_image(saved_image_path)
        img_vec = img_model.encode([query])[0].tolist()
        response = image_query(client, img_vec)

        # Check if there are any images to display
        if len(response) == 0:
            st.write("No images found in the directory.")
        else:
            # Loop through the image paths and display each image
            for image_path in response:
                # Open the image using PIL
                image = Image.open(image_path)
                
                # Display the image in the Streamlit app
                st.image(image, caption=f"Image: {os.path.basename(image_path)}", use_column_width=True)


# If the user selects "Text", provide a text input box
if input_type == "Text":
    user_input = st.text_area("Enter your text")
    
    if user_input:

        # Save the input text to a JSON file
        saved_json_path = save_text_to_json(user_input, SAVE_DIR_TXT)
        # Read and display the contents of the selected JSON file
        with open(saved_json_path, 'r') as json_file:
            data = json.load(json_file)

        query = data["input_text"]
        text_vec = text_model.encode([query])[0].tolist()

        response = text_query(client, text_vec)

        # Check if there are any images to display
        if len(response) == 0:
            st.write("No images found in the directory.")
        else:
            # Loop through the image paths and display each image
            for image_path in response:
                # Open the image using PIL
                image = Image.open(image_path)
                
                # Display the image in the Streamlit app
                st.image(image, caption=f"Image: {os.path.basename(image_path)}", use_column_width=True)