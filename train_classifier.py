import os
import sys
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split
from torchvision import models, datasets, transforms
from torchvision.datasets import ImageFolder
from torchvision.models import mobilenet_v2, MobileNet_V2_Weights
import openvino as ov
from pyntree import Node
from tqdm import tqdm

config = Node("train.yml").config

ovcore = ov.Core()
# print(ovcore.available_devices)

print("Configuring neural net...")
model = mobilenet_v2(pretrained=True)

# Freeze the base (optional, recommended for small datasets)
for param in model.features.parameters():
    param.requires_grad = False

# Create a binary output layer
model.classifier = nn.Sequential(
    nn.Dropout(0.2),
    nn.Linear(model.last_channel, 1),  # Condense to a single output
    # nn.Sigmoid(),  # Only needed if using BCELoss, BCEWithLogitsLoss handles this
)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)

loss_function = nn.BCEWithLogitsLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate())  # Use a small learning rate to prevent craziness

# Load training data
# Load default weights
weights = MobileNet_V2_Weights.DEFAULT

# Automatically get the matching transform
transform = weights.transforms()

# Load properly-sorted images
print("Loading dataset...")
dataset = ImageFolder("classifier_labeleddata", transform=transform)

# Split into training and validation sets
train_size = int(0.8 * len(dataset))  # 80% is train data
val_size = len(dataset) - train_size  # 20% is validation data
train_dataset, val_dataset = random_split(dataset, [train_size, val_size])

# Create data loaders
train_loader = DataLoader(train_dataset, batch_size=config.batch_size(), shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=config.batch_size(), shuffle=True)

# Training loop
for epoch in range(config.num_epochs()):
    print(f"\nEpoch {epoch+1}/{config.num_epochs()}")
    model.train()  # Set model to training mode
    for images, labels in tqdm(train_loader, desc="Train"):
        images, labels = images.to(device), labels.to(device).float().unsqueeze(1)
    outputs = model(images)
    loss = loss_function(outputs, labels)

    optimizer.zero_grad()
    # Back propagate
    loss.backward()
    optimizer.step()

    # Validation phase
    model.eval()
    total_val_loss = 0
    correct = 0
    total = 0
    with torch.no_grad():
        for images, labels in tqdm(val_loader, desc="Validate"):
            images = images.to(device)
            labels = labels.to(device).float().unsqueeze(1)

            outputs = model(images)
            loss = loss_function(outputs, labels)
            total_val_loss += loss.item()

            predictions = (outputs > 0.5).float()
            correct += (predictions == labels).sum().item()
            total += labels.size(0)

    avg_val_loss = total_val_loss / len(val_loader)
    val_accuracy = correct / total

    print(
        f"Train Loss: {loss:.4f} | "
        f"Average val Loss: {avg_val_loss:.4f} | "
        f"Val Accuracy: {val_accuracy:.4f}"
    )


# Save model
print("Saving model...")
torch.save(model.state_dict(), 'sunset_model.pth')

# OpenVINO optimization
print("Optimizing model for OpenVino...")
image, label = dataset[0]
ov_model = ov.convert_model(model, example_input=(image.unsqueeze(0),))  # Convert model with an example as a batch of 1
ov.save_model(ov_model, "sunset_model_openvino.xml")
