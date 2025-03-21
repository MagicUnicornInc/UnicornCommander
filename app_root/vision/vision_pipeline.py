import logging
from .vision_model import VisionModel
from PIL import Image
import torch
pass
class VisionPipeline:
    def __init__(self):
        self.model = VisionModel()
        
    def process_screenshot(self, screenshot_path: str) -> str:
        """Process a screenshot and return analysis"""
        try:
            image = Image.open(screenshot_path)
            return self.model.analyze_image(
                image, 
                "Describe the interface elements and content visible in this screenshot."
            )
        except Exception as e:
            logging.error(f"Screenshot processing failed: {e}")
            return str(e)
            
    def process_live_screen(self, region=None):
        """Process the current screen content"""
        try:
            screenshot = computer.display.screenshot(show=False)
            if region:
                screenshot = screenshot.crop(region)
            return self.model.analyze_image(
                screenshot,
                "Describe what is currently visible on the screen."
            )
        except Exception as e:
            logging.error(f"Live screen processing failed: {e}")
            return str(e)
