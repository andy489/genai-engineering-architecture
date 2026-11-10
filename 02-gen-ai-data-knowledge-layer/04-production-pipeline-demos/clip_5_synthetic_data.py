import openai
from typing import List, Dict

def generate_synthetic_qa(document_text: str, num_pairs: int = 5) -> List[Dict]:
    prompt = f"""
    Based on the following document, generate {num_pairs} question-answer pairs.
    Make the questions diverse: some should be factual, some should require inference,
    and some should use synonyms not found in the text.
    
    Document:
    {document_text[:2000]}  # Truncate to avoid token limits
    
    Return the pairs as a JSON list with 'question' and 'answer' keys.
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-5.4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    
    # Parse the response (simplified - you'd need proper JSON parsing)
    import json
    qa_pairs = json.loads(response.choices[0].message.content)
    return qa_pairs

# Example usage
document = "The Eiffel Tower was completed in 1889. It is located in Paris, France. It was designed by Gustave Eiffel."
qa_pairs = generate_synthetic_qa(document, num_pairs=3)

for qa in qa_pairs:
    print(f"Q: {qa['question']}")
    print(f"A: {qa['answer']}\n")