from huggingface_hub import HfApi, create_repo
import os

token = "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"
repo_id = "sandeepcm/news-bias-distilbert"
model_folder = "model/saved_model"

api = HfApi()

# Create repo first
print("Creating repository on HuggingFace Hub...")
create_repo(
    repo_id=repo_id,
    token=token,
    exist_ok=True,
    repo_type="model"
)
print(f"✅ Repository created: https://huggingface.co/{repo_id}")

# Upload all files
for filename in os.listdir(model_folder):
    filepath = os.path.join(model_folder, filename)
    if os.path.isfile(filepath):
        print(f"Uploading {filename}...")
        api.upload_file(
            path_or_fileobj=filepath,
            path_in_repo=filename,
            repo_id=repo_id,
            repo_type="model",
            token=token
        )
        print(f"✅ {filename} uploaded")

print("\nALL FILES UPLOADED TO HUGGINGFACE HUB")
print(f"View at: https://huggingface.co/{repo_id}")