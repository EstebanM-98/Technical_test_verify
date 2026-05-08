import os
from dotenv import load_dotenv

def load_configuration():
    """
    Loads environment variables and returns the Veryfi API configuration.
    """
    # Assuming this is inside components/ocr/, we want to point to the project root for .env
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    env_path = os.path.join(root_dir, '.env')
    
    if os.path.exists(env_path):
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv() # Fallback to default loading
    
    config = {
        'client_id': os.getenv('VERYFI_CLIENT_ID'),
        'client_secret': os.getenv('VERYFI_CLIENT_SECRET'),
        'username': os.getenv('VERYFI_USERNAME'),
        'api_key': os.getenv('VERYFI_API_KEY')
    }
    
    missing_keys = [k for k, v in config.items() if not v]
    if missing_keys:
        raise ValueError(f"Missing Veryfi credentials in the .env file: {', '.join(missing_keys)}")
        
    return config
