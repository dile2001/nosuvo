from flask import Flask, request, jsonify
# Flask is a lightweight web framework in Python for building APIs and web apps.
import spacy
# spacy is a Natural Language Processing (NLP) library for tokenizing and analyzing text.

#initializes the Flask application.
app = Flask(__name__)  

#loads a pre-trained English model for NLP (small version).
nlp = spacy.load("en_core_web_sm") 

def chunk_paragraph(paragraph: str):
    doc = nlp(paragraph)
    chunks = []
    
    # Process each sentence separately to maintain sentence boundaries
    for sent in doc.sents:
        sentence_chunks = []
        
        # Extract noun phrases for better chunking
        noun_phrases = [chunk.text for chunk in sent.noun_chunks]
        
        # Create chunks based on noun phrases and meaningful units
        i = 0
        while i < len(sent):
            token = sent[i]
            
            # Check if this token starts a noun phrase
            noun_phrase_found = False
            for np in noun_phrases:
                np_tokens = np.split()
                if i + len(np_tokens) <= len(sent) and sent[i:i+len(np_tokens)].text == np:
                    sentence_chunks.append(np)
                    i += len(np_tokens)
                    noun_phrase_found = True
                    break
            
            if not noun_phrase_found:
                # For other tokens, group them with adjacent tokens based on dependency
                current_chunk = [token.text]
                
                # Add dependent tokens (adjectives, adverbs, etc.)
                for child in token.children:
                    if child.dep_ in ("amod", "advmod", "det", "compound", "aux", "auxpass"):
                        current_chunk.append(child.text)
                
                # Add the chunk
                if current_chunk:
                    sentence_chunks.append(" ".join(current_chunk))
                i += 1
        
        # Clean up and add sentence chunks
        for chunk in sentence_chunks:
            chunk = chunk.strip()
            if chunk and not all(c in ".,!?;:" for c in chunk):
                chunks.append(chunk)
    
    return chunks


@app.route("/chunk", methods=["POST"])
def chunk():
    if request.content_type == 'application/json':
        data = request.json
        text = data.get("text", "")
    elif 'file' in request.files:
        text = request.files['file'].read().decode("utf-8")
    else:
        return jsonify({"error": "Send 'text' as JSON or 'file' as txt upload"}), 400

    chunks = chunk_paragraph(text)
    return jsonify({"chunks": chunks})


@app.route("/", methods=["GET"])
def home():
    return """
    <h2>Reading Chunker API</h2>
    <p>POST /chunk with either JSON {"text": "..."} or upload .txt file as 'file'</p>
    """


if __name__ == "__main__":
    app.run(debug=True)
