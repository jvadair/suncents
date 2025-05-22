# Proudly vibe-coded by ChatGPT
import re
import matplotlib.pyplot as plt

# Path to your log file
log_path = "train_output.log"  # Replace with actual log location

# Read the log file
with open(log_path, 'r') as f:
    log_contents = f.read()

# Find all epoch numbers and corresponding val accuracies
pattern = r"Epoch (\d+)/\d+\s.*?Val Accuracy:\s+([0-9.]+)"
matches = re.findall(pattern, log_contents, re.DOTALL)

# Convert to list of [epoch, accuracy] as floats
data = [(int(epoch), float(acc)) for epoch, acc in matches]

# Split into two lists for plotting
epochs, accuracies = zip(*data)

# Plotting
plt.figure(figsize=(10, 6))
plt.plot(epochs, accuracies, marker='o', linestyle='-')
plt.title("Validation Accuracy per Epoch")
plt.xlabel("Epoch")
plt.ylabel("Validation Accuracy")
plt.grid(True)
plt.tight_layout()
plt.show()
