import base64
from weaviate.util import generate_uuid5
from IPython.display import Image as IPImage, display
from PIL import Image
import os
import uuid
import json


################ Function to display the retrieved images from the response to query , res-------> response after querying ###################
def show_images(res, src_img=None):
    for i in range(0,len(res["data"]["Get"]["Modality"])):
        f = res["data"]["Get"]["Modality"][i]['file_path']
        # Path to the image file
        image_path = str(f) # Replace with the correct path
        print(image_path)
        # Display the image
        display(IPImage(filename=image_path))


######## Helper Function to load the image #########
def load_image(path):
    return Image.open(path)

def data_ingestion(client, product_img_paths, img_model):
    class_name = "multimodality"
    client.batch.configure(batch_size=100)  # Configure batch
    with client.batch as batch:
        for img_set in [
            (product_img_paths, "TMDB"),
        ]:
            for img_path in img_set[0][:100]:
                vector = img_model.encode([load_image(img_path)])[0].tolist()
                img_b64 = to_base64(img_path)
                
                properties={
                    "file_path":img_path,
                    "image":img_b64,
                    "img_source": img_set[1]
                }

                batch.add_data_object(
                properties,
                class_name,
                vector=vector,
                uuid=generate_uuid5(img_path)  # Optional: Specify an object vector
            )


def to_base64(path):
    with open(path, 'rb') as file:
        return base64.b64encode(file.read()).decode('utf-8')
    

def save_image_to_local(uploaded_image, SAVE_DIR):
    # Generate a unique filename using uuid to avoid overwriting
    image_filename = f"{uuid.uuid4().hex}.png"  # You can modify the extension based on the uploaded image type
    
    # Create the full file path
    file_path = os.path.join(SAVE_DIR, image_filename)

    # Open the uploaded image using PIL
    image = Image.open(uploaded_image)
    
    # Save the image locally
    image.save(file_path)

    return file_path



def save_text_to_json(user_input, SAVE_DIR):
    # Generate a unique filename using uuid to avoid overwriting
    json_filename = f"{uuid.uuid4().hex}.json"
    
    # Create the full file path
    file_path = os.path.join(SAVE_DIR, json_filename)
    
    # Prepare the data to be saved as JSON
    data = {"input_text": user_input}
    
    # Write the data to the JSON file
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file)
    
    return file_path




def text_query(client, text_vec):
    response = []
    try:
        # Construct the query
        result = client.query.get("Mmultimodality", ["image", "file_path"]) \
            .with_near_vector({"vector": text_vec}) \
            .with_where({
                "path": ["img_source"], 
                "operator": "Equal", 
                "valueString": "TMDB"
            }) \
            .with_limit(5) \
            .do()

        # Check if there are results
        if "data" in result and "Get" in result["data"] and "Mmultimodality" in result["data"]["Get"]:
            for obj in result["data"]["Get"]["Mmultimodality"]:
                image = obj.get("image", "No image")
                file_path = obj.get("file_path", "No file path")
                print(result)
                print(f"Image: {image}, File Path: {file_path}")

            for i in range(0,len(result["data"]["Get"]["Mmultimodality"])):
                    f = result["data"]["Get"]["Mmultimodality"][i]['file_path']
                    # Path to the image file
                    image_path = str(f) # Replace with the correct path
                    response.append(image_path)
                    # Display the image
                    display(IPImage(filename=image_path))
                
        else:
            print("No results found.")
        return response

    except Exception as e:
        print(f"An error occurred: {e}")
        return []



def image_query(client,img_vec):
    response = []
    try:
        # Construct the query
        result = client.query.get("Mmultimodality", ["image", "file_path"]) \
            .with_near_vector({"vector": img_vec}) \
            .with_where({
                "path": ["img_source"], 
                "operator": "Equal", 
                "valueString": "TMDB"
            }) \
            .with_limit(5) \
            .do()
        # Check if there are results
        if "data" in result and "Get" in result["data"] and "Mmultimodality" in result["data"]["Get"]:
            for obj in result["data"]["Get"]["Mmultimodality"]:
                image = obj.get("image", "No image")
                file_path = obj.get("file_path", "No file path")
                print(f"Image: {image}, File Path: {file_path}")
            
            for i in range(0,len(result["data"]["Get"]["Mmultimodality"])):
                    f = result["data"]["Get"]["Mmultimodality"][i]['file_path']
                    # Path to the image file
                    image_path = str(f) # Replace with the correct path
                    response.append(image_path)
                    # Display the image
                    display(IPImage(filename=image_path))
        else:
            print("No results found.")
        return response

    except Exception as e:
        print(f"An error occurred: {e}")
        return []