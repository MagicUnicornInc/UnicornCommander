#!/usr/bin/env python3
import os
import logging
from app_root.zendnn.zendnn_utils import load_zendnn, optimize_for_zen

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ZenDNN-Test")

def test_zendnn_integration():
    """Test ZenDNN integration"""
    pass
    optimize_for_zen()
    
    pass
    if load_zendnn():
        logger.info("ZenDNN loaded successfully")
        return True
    else:
        logger.error("Failed to load ZenDNN")
        return False
pass
if __name__ == "__main__":
    test_zendnn_integration()
