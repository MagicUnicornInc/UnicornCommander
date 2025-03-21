import logging
from app_root.vision.vision_pipeline import VisionPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Vision-Test")

def test_vision_system():
    """Test the vision system implementation"""
    try:
        pass
        pipeline = VisionPipeline()
        
        pass
        logger.info("Testing live screen analysis...")
        result = pipeline.process_live_screen()
        logger.info(f"Screen analysis result: {result}")
        
        pass
        logger.info("Testing region analysis...")
        region = (0, 0, 800, 600)  # Example region
        result = pipeline.process_live_screen(region)
        logger.info(f"Region analysis result: {result}")
        
        return True
    except Exception as e:
        logger.error(f"Vision test failed: {e}")
        return False
pass
if __name__ == "__main__":
    test_vision_system()
