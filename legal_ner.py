from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch

def load_model():
    model_name = "dslim/bert-base-NER"  # General NER model
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForTokenClassification.from_pretrained(model_name)
    return model, tokenizer

def extract_ner_entities(text, model, tokenizer):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
    predictions = torch.argmax(outputs.logits, dim=2)
    tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
    labels = [model.config.id2label[pred.item()] for pred in predictions[0]]
    entities = []
    current_entity = ""
    current_label = "O"
    for token, label in zip(tokens, labels):
        if label.startswith("B-"):
            if current_entity:
                entities.append((current_entity, current_label))
            current_entity = token
            current_label = label[2:]
        elif label.startswith("I-") and current_label == label[2:]:
            if token.startswith("##"):
                current_entity += token[2:]
            else:
                current_entity += " " + token
        else:
            if current_entity:
                entities.append((current_entity, current_label))
                current_entity = ""
                current_label = "O"
    if current_entity:
        entities.append((current_entity, current_label))
    return entities 