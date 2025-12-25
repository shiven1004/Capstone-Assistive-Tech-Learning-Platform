from transformers import AutoTokenizer, AutoModelForSequenceClassification

class SequenceModelHandler:
    def __init__(self, model_name: str):
        """
        Initialization of class arguments.

        1. model_name -> str -> Hugging face repo id.\n
        """
        self.model_name = model_name
    
    def load_sequence_model(self):
        """
        Loads the tokenizer and model according to the initialization parameters.

        Returns:
            model: The loaded AutoModelForCausalLM on the specified device.
            tokenizer: The corresponding AutoTokenizer.
        """
        tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        model = AutoModelForSequenceClassification.from_pretrained(
            self.model_name,
            device_map="cpu",
        )
        
        return model, tokenizer
