from fuzzywuzzy import fuzz
import itertools

def find_duplicate_entities(entities, threshold=85):
    """Find likely duplicate entities based on name similarity"""
    duplicates = []
    
    for e1, e2 in itertools.combinations(entities, 2):
        name1, name2 = e1['name'], e2['name']
        similarity = fuzz.token_sort_ratio(name1, name2)
        
        if similarity > threshold:
            duplicates.append({
                'source': name1,
                'target': name2,
                'score': similarity
            })
    
    return duplicates

# Example
entities = [
    {'name': 'Apple Inc.', 'type': 'Organization'},
    {'name': 'Apple', 'type': 'Organization'},
    {'name': 'Apple Computer', 'type': 'Organization'},
    {'name': 'Microsoft', 'type': 'Organization'}
]

dupes = find_duplicate_entities(entities)
for d in dupes:
    print(f"'{d['source']}' might be same as '{d['target']}' ({d['score']}%)")