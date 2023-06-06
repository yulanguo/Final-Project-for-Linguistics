import os
from docx import Document
from fuzzywuzzy import fuzz
import spacy
from spacy.matcher import PhraseMatcher

nlp = spacy.load('en_core_web_lg')

def deidentify_names_in_directory(directory_path, name_dict):
    output_directory = os.path.join(directory_path, 'deidentified_docs')
    os.makedirs(output_directory, exist_ok=True)
    for filename in os.listdir(directory_path):
        if filename.endswith('.docx') and not filename.startswith('~$'):
            file_path = os.path.join(directory_path, filename)
            deidentify_names(file_path, name_dict, output_directory)

def deidentify_names(doc_path, name_dict, output_directory):
    document = Document(doc_path)
    matcher = PhraseMatcher(nlp.vocab)
    # patterns = [nlp(name) for name in name_dict.keys()]
    # matcher.add('Names', None, *patterns)
    replaced_entities = {}

    for paragraph in document.paragraphs:
        doc = nlp(paragraph.text)
        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'ORG', 'LOC']:
                ent_text = ent.text
                if ent_text not in name_dict and ent_text not in replaced_entities:
                    if name_dict.get(ent_text) is None:
                        paragraph.text = paragraph.text.replace(ent_text, f'[{ent_text}]')
                        print('Potential name:', ent_text)

        for name, pseudonym in name_dict.items():
            name_tokens = nlp(name)
            for token in doc:
                if fuzz.partial_ratio(token.text.lower(), name_tokens[0].text.lower()) >= 70:
                    # Check for multi-word phrases
                    entity_tokens = [token]
                    for i in range(1, len(name_tokens)):
                        if token.i + i < len(doc) and fuzz.partial_ratio(
                                doc[token.i + i].text.lower(), name_tokens[i].text.lower()) >= 70:
                            print(fuzz.partial_ratio(doc[token.i + i].text.lower(), name_tokens[i].text.lower()))
                            print(doc[token.i + i].text.lower())
                            print(name_tokens[i].text.lower())
                            entity_tokens.append(doc[token.i + i])
                        else:
                            break
                    if len(entity_tokens) == len(name_tokens):
                        paragraph.text = paragraph.text.replace(' '.join([t.text for t in entity_tokens]), pseudonym)

    modified_filename = os.path.basename(doc_path).replace('.docx', '_deidentified.docx')
    modified_doc_path = os.path.join(output_directory, modified_filename)
    document.save(modified_doc_path)
    print('Deidentification complete. Modified document saved as:', modified_doc_path)

# Example Usage (Change the directory path and enter pseudonyms as needed)
# Please enter the entire names as keys and pseudonyms as values
directory_path = 'all_docs'
names_to_pseudonyms = {
    'Ryan': 'Rocky',
    'Alex': 'A',
    'John': 'J',
    'West Garfield Park': 'Skokie River',
    'West Garfield': 'Skokie River'
    ## is there a way to make this better? 
}
deidentify_names_in_directory(directory_path, names_to_pseudonyms)
