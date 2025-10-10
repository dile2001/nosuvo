import spacy

# Load English model
nlp = spacy.load("en_core_web_sm")

def chunk_sentence(sentence: str):
    doc = nlp(sentence)
    chunks = []

    # Collect noun chunks (noun phrases)
    for chunk in doc.noun_chunks:
        chunks.append(chunk.text)

    # Collect verb phrases (verbs + auxiliaries)
    for token in doc:
        if token.pos_ == "VERB":
            verb_phrase = " ".join([t.text for t in token.lefts if t.dep_ in ("aux", "auxpass")])
            verb_phrase += " " + token.text
            chunks.append(verb_phrase.strip())

    # Collect prepositional phrases (prep + its object)
    for token in doc:
        if token.pos_ == "ADP":  # prepositions
            prep_phrase = token.text + " " + " ".join([child.text for child in token.children])
            chunks.append(prep_phrase)

    return chunks

text = "Students assemble in the quad with their teacher at the time of evacuation. The teacher will do a head count and check the roll."
print(chunk_sentence(text))