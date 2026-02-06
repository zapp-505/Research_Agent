"""
UI configuration loader
"""

import configparser
import os


class UIConfig:
    """
    Load and manage UI configuration
    """
    
    def __init__(self, config_file="uiconfigfile.ini"):
        self.config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), config_file)
        self.config.read(config_path)
    
    def get(self, section, key, fallback=None):
        """
        Get configuration value
        """
        return self.config.get(section, key, fallback=fallback)
    
    def get_ui_config(self):
        """
        Get UI section configuration as dict
        """
        return dict(self.config['UI'])
    
    def get_streamlit_config(self):
        """
        Get Streamlit section configuration as dict
        """
        return dict(self.config['Streamlit'])
    
    def get_chat_config(self):
        """
        Get Chat section configuration as dict
        """
        return dict(self.config['Chat'])
