import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from logger import Logger

LOG = Logger("Model Handler Logger", True, "Logs/model_handler_logs.log", 'DEV')

class ModelHandler:
    def __init__(self, model_id: str, quantize: bool = False):
        """
        Initialization of class arguments.

        1. model_id -> str -> Hugging face repo id.
        2. quantize -> bool -> Whether to not quantize the model.
        """
        self.model_id = model_id
        self.quantize = quantize
    
    def load_model(self):
        """
        Loads the tokenizer and model according to the initialization parameters.

        Returns:
            model: The loaded AutoModelForCausalLM on the specified device.
            tokenizer: The corresponding AutoTokenizer.
        """
        try:
            tokenizer = AutoTokenizer.from_pretrained(self.model_id, local_files_only=True)
            LOG.debug("Model's tokenizer loaded successfully.")
            if self.quantize:
                model = AutoModelForCausalLM.from_pretrained(self.model_id, local_files_only=True, device_map=None, torch_dtype=torch.float16)
                LOG.debug("Model loaded and quantized successfully.")
            else:
                model = AutoModelForCausalLM.from_pretrained(self.model_id, local_files_only=True, device_map=None)
                LOG.debug("Model loaded successfully.")
        
        except (OSError, ValueError) as e:
            LOG.debug("Model not found locally, starting download")
            tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            LOG.debug("Model's tokenizer loaded successfully.")
            if self.quantize:
                model = AutoModelForCausalLM.from_pretrained(self.model_id, device_map=None, torch_dtype=torch.float16)
                LOG.debug("Model loaded and quantized successfully.")
            else:
                model = AutoModelForCausalLM.from_pretrained(self.model_id, device_map=None)
                LOG.debug("Model loaded successfully.")

        return model, tokenizer