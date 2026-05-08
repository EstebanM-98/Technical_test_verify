from veryfi import Client

class VeryfiOCR:
    def __init__(self, config):
        """
        Initializes the Veryfi client using the provided configuration dictionary.
        """
        self.client = Client(
            config['client_id'],
            config['client_secret'],
            config['username'],
            config['api_key']
        )
        
    def process_document(self, file_path):
        """
        Sends a document to the Veryfi API and returns the full JSON response.
        """
        try:
            return self.client.process_document(file_path)
        except Exception as e:
            raise RuntimeError(f"Error communicating with Veryfi API: {e}")

    def extract_ocr_text(self, file_path):
        """
        Processes a document and extracts only the 'ocr_text' field.
        """
        response = self.process_document(file_path)
        return response.get('ocr_text', '')
