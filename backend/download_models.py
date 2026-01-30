"""
Pre-download sentence transformers model for offline use.
Run this script to download the model locally before building the Docker image.
"""
from sentence_transformers import SentenceTransformer
import os

# Create models directory if it doesn't exist
MODEL_DIR = "./sentence_transformers_cache"
os.makedirs(MODEL_DIR, exist_ok=True)

# Download the model
print(f"Downloading model to {MODEL_DIR}...")
model = SentenceTransformer("all-MiniLM-L6-v2", cache_folder=MODEL_DIR)
print("Model downloaded successfully!")
print(f"Model location: {MODEL_DIR}")

# Show the cache structure
print("\nCache contents:")
for root, dirs, files in os.walk(MODEL_DIR):
    level = root.replace(MODEL_DIR, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = ' ' * 2 * (level + 1)
    for file in files[:5]:  # Show first 5 files
        print(f"{subindent}{file}")
    if len(files) > 5:
        print(f"{subindent}... and {len(files) - 5} more files")

print("\n✓ The model is cached and ready to be bundled in the Docker image")
print("✓ When SENTENCE_TRANSFORMERS_HOME is set, the library will use this cache")
print("✓ No internet connection will be needed at runtime")
