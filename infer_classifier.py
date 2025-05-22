import openvino as ov
from torchvision.models import MobileNet_V2_Weights
from PIL import Image
from sys import argv
import numpy as np
from scipy.special import expit as sigmoid

# compile the model for CPU device
ovcore = ov.Core()
ov_model = ovcore.read_model('sunset_model_openvino.xml')
compiled_model = ovcore.compile_model(ov_model, 'CPU')


def infer(image_path):
    image = Image.open(image_path)
    image = image.convert('RGB')
    weights = MobileNet_V2_Weights.DEFAULT
    transform = weights.transforms()
    image = transform(image)
    image = image.unsqueeze(0)  # Make this a batch of 1
    result = compiled_model([image])
    # print(result)
    prob = sigmoid(result[0])
    return prob[0][0]


if __name__ == "__main__":
    image_path = argv[1]
    if image_path:
        print(infer(image_path))
    else:
        print("No image path provided")
