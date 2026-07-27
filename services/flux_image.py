"""
Vision AI v2.0 - Hugging Face Image Generator
==============================================
Multi-model image generation wrapper for Hugging Face Inference API.
Supports automatic fallback, queue waiting, and async execution.

Supported Models (Free):
- black-forest-labs/FLUX.1-dev          (Primary - Fast, detailed)
- stabilityai/stable-diffusion-3.5-large (Backup - High quality)
- black-forest-labs/FLUX.1-schnell       (Fallback - Very fast)
"""

import os
import base64
import asyncio
import requests
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
API_BASE = "https://api-inference.huggingface.co/models"

# 🔥 Updated list of free models to try
MODELS = [
    "black-forest-labs/FLUX.1-dev",           # Primary (Fast, high quality)
    "stabilityai/stable-diffusion-3.5-large", # Backup (Excellent quality, free)
    "black-forest-labs/FLUX.1-schnell",       # Fallback (Very fast)
]

async def generate_image_hf(prompt: str, model_index: int = 0) -> dict:
    """
    Generate an image using the Hugging Face Inference API.
    Automatically rotates through free models and handles queues.

    Args:
        prompt (str): The text prompt for the image generation.
        model_index (int): Which model to try first (0 = primary).

    Returns:
        dict: Success status, image_data (base64), or error message.
    """
    if not HF_TOKEN:
        return {"success": False, "error": "HF_TOKEN not configured in .env"}

    # Try each model in order
    for i in range(model_index, len(MODELS)):
        model_id = MODELS[i]
        url = f"{API_BASE}/{model_id}"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        payload = {"inputs": prompt}

        try:
            print(f"🖼️ Generating image with {model_id}...")
            response = requests.post(url, headers=headers, json=payload, timeout=90)

            # Handle Hugging Face waiting queues (Status 503 means "Model is loading, wait")
            if response.status_code == 503:
                print(f"⏳ {model_id} is loading. Waiting 5 seconds...")
                await asyncio.sleep(5)
                response = requests.post(url, headers=headers, json=payload, timeout=90)

            if response.status_code == 200:
                image_base64 = base64.b64encode(response.content).decode('utf-8')
                return {
                    "success": True,
                    "image_data": image_base64,
                    "provider": f"Hugging Face ({model_id})"
                }
            else:
                print(f"⚠️ {model_id} returned status {response.status_code}. Trying next model...")

        except requests.exceptions.Timeout:
            print(f"⏱️ {model_id} timed out. Trying next model...")
        except Exception as e:
            print(f"❌ Error with {model_id}: {e}. Trying next model...")

    # If all models fail
    return {
        "success": False,
        "error": "All Hugging Face models failed. Please try a simpler prompt or check your token."
    }

async def generate_flux_image(prompt: str) -> dict:
    """
    Legacy wrapper function to maintain backward compatibility.
    """
    return await generate_image_hf(prompt, model_index=0)