# legal_ner.py
from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch
import logging

logger = logging.getLogger(__name__)

def load_model():
    """Load the NER model and tokenizer"""
    try:
        model_name = "dslim/bert-base-NER"  # General NER model
        logger.info(f"Loading NER model: {model_name}")
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForTokenClassification.from_pretrained(model_name)
        
        logger.info("NER model loaded successfully")
        return model, tokenizer
    except Exception as e:
        logger.error(f"Failed to load NER model: {str(e)}")
        raise

def extract_ner_entities(text, model, tokenizer):
    """Extract named entities from text using the NER model"""
    try:
        # Tokenize input with proper handling of longer texts
        encoded_input = tokenizer(
            text, 
            return_tensors="pt", 
            truncation=True, 
            padding=True,
            max_length=512  # BERT models typically have a max length of 512
        )
        
        # Get predictions
        with torch.no_grad():
            outputs = model(**encoded_input)
            
        # Process predictions
        predictions = torch.argmax(outputs.logits, dim=2)
        tokens = tokenizer.convert_ids_to_tokens(encoded_input["input_ids"][0])
        labels = [model.config.id2label[pred.item()] for pred in predictions[0]]
        
        # Extract entities
        entities = []
        current_entity = ""
        current_label = "O"
        
        for token, label in zip(tokens, labels):
            # Skip special tokens
            if token in [tokenizer.cls_token, tokenizer.sep_token, tokenizer.pad_token]:
                continue
                
            if label.startswith("B-"):
                # Start of a new entity
                if current_entity:
                    entities.append((current_entity.strip(), current_label))
                current_entity = token.replace("##", "")
                current_label = label[2:]  # Remove "B-" prefix
            elif label.startswith("I-") and current_label == label[2:]:
                # Inside an entity
                if token.startswith("##"):
                    current_entity += token[2:]  # Append without space for subwords
                else:
                    current_entity += " " + token
            else:
                # Outside an entity
                if current_entity:
                    entities.append((current_entity.strip(), current_label))
                current_entity = ""
                current_label = "O"
        
        # Add the last entity if there is one
        if current_entity:
            entities.append((current_entity.strip(), current_label))
            
        logger.info(f"Extracted {len(entities)} entities from text")
        return entities
        
    except Exception as e:
        logger.error(f"Error extracting entities: {str(e)}")
        return []  # Return empty list on error