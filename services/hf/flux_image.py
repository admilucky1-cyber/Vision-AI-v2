import os
import base64
import requests
from dotenv import load_dotenv

load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
HF_API_FLUX = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev"

async def generate_flux_image(prompt: str):
    if not HF_TOKEN:
        return {"success": False, "error": "HF_TOKEN missing"}
    
    try:
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        payload = {"inputs": prompt}
        response = requests.post(HF_API_FLUX, headers=headers, json=payload, timeout=60)
        
        if response.status_code != 200:
            return {"success": False, "error": f"HF Error {response.status_code}"}
        
        image_base64 = base64.b64encode(response.content).decode('utf-8')
        return {"success": True, "image_data": image_base64}
    except Exception as e:
        return {"success": False, "error": str(e)}