from transformers import AutoProcessor, LlamaForCausalLM
import torch
import logging
from typing import Optional

class VisionModel:
    def __init__(self, model_id: str = "meta-llama/Llama-3.2-11B-Vision-Instruct"):
        self.processor = AutoProcessor.from_pretrained(model_id)
        self.model = LlamaForCausalLM.from_pretrained(model_id)
        if torch.cuda.is_available():
            self.model = self.model.to("cuda")
            
    def analyze_image(self, image_path: str, prompt: Optional[str] = None) -> str:
        """Analyze an image using Llama Vision"""
        try:
            inputs = self.processor(
                images=image_path,
                text=prompt or "Describe this image in detail.",
                return_tensors="pt"
            )
            
            if torch.cuda.is_available():
                inputs = {k: v.to("cuda") for k, v in inputs.items()}
                
            outputs = self.model.generate(**inputs, max_length=200)
            return self.processor.decode(outputs[0], skip_special_tokens=True)
            
        except Exception as e:
            logging.error(f"Image analysis failed: {e}")
            return str(e)
