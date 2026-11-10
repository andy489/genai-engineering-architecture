from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List

# Initialize your LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# Define the structure we want using Pydantic
class Entity(BaseModel):
    name: str = Field(description="The entity name")
    type: str = Field(description="Entity type: Person, Organization, Product, Technology")
    
class Relationship(BaseModel):
    source: str = Field(description="Source entity name")
    target: str = Field(description="Target entity name")
    type: str = Field(description="Relationship type")

class KnowledgeGraph(BaseModel):
    entities: List[Entity] = Field(description="List of unique entities")
    relationships: List[Relationship] = Field(description="List of relationships")

# Create a parser
parser = JsonOutputParser(pydantic_object=KnowledgeGraph)

# Build the prompt
prompt = ChatPromptTemplate.from_template(
    """
    Extract a knowledge graph from the text below.
    
    Rules:
    - Identify all relevant entities
    - Extract relationships between them
    - Use consistent entity names
    - Only include explicit information from the text
    
    {format_instructions}
    
    Text: {text}
    """
)

# Chain everything
chain = prompt | llm | parser

# Example text
text = """
Apple acquired DarwinAI in 2024 to boost its AI capabilities. 
DarwinAI was founded by Alexander Wong in Waterloo, Canada. 
The company specialized in efficient computer vision models.
"""

# Run extraction
result = chain.invoke({
    "text": text,
    "format_instructions": parser.get_format_instructions()
})

# Display results
print("Entities found:")
for entity in result["entities"]:
    print(f"  - {entity['name']} ({entity['type']})")

print("\nRelationships found:")
for rel in result["relationships"]:
    print(f"  - {rel['source']} --[{rel['type']}]--> {rel['target']}")