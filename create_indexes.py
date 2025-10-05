"""
Database Performance Optimization Script for Neo4j Team Formation

This script creates essential indexes to dramatically improve query performance.
Neo4j queries without proper indexes can take hours on large datasets.

CRITICAL INDEXES NEEDED:
1. Author.Author_ID (primary key lookup)
2. Author.skills (keyword matching)
3. Paper.Combined_Keywords (keyword search)
4. Relationship indexes for traversals

Run this once on the database to create all necessary indexes.
"""

CREATE_INDEXES_QUERIES = [
    # Core Author indexes
    "CREATE INDEX author_id_index IF NOT EXISTS FOR (a:Author) ON (a.Author_ID)",
    "CREATE INDEX author_skills_index IF NOT EXISTS FOR (a:Author) ON (a.skills)",
    "CREATE INDEX author_name_index IF NOT EXISTS FOR (a:Author) ON (a.Author_Name)",
    
    # Paper indexes for keyword searches
    "CREATE INDEX paper_keywords_index IF NOT EXISTS FOR (p:Paper) ON (p.Combined_Keywords)",
    "CREATE INDEX paper_citations_index IF NOT EXISTS FOR (p:Paper) ON (p.n_Citation)",
    "CREATE INDEX paper_years_index IF NOT EXISTS FOR (p:Paper) ON (p.Years_Passed)",
    
    # Text search indexes (full-text search for better performance)
    "CREATE FULLTEXT INDEX author_skills_fulltext IF NOT EXISTS FOR (a:Author) ON EACH [a.skills]",
    "CREATE FULLTEXT INDEX paper_keywords_fulltext IF NOT EXISTS FOR (p:Paper) ON EACH [p.Combined_Keywords]",
    
    # Composite indexes for common query patterns
    "CREATE INDEX author_skills_id_composite IF NOT EXISTS FOR (a:Author) ON (a.skills, a.Author_ID)",
    
    # Organization indexes if they exist
    "CREATE INDEX organization_index IF NOT EXISTS FOR (o:Organization) ON (o.name)",
]

# Query to check existing indexes
CHECK_INDEXES_QUERY = """
SHOW INDEXES YIELD name, type, entityType, labelsOrTypes, properties, state
RETURN name, type, entityType, labelsOrTypes, properties, state
ORDER BY name
"""

# Query to get database statistics
DATABASE_STATS_QUERY = """
MATCH (a:Author) 
WITH count(a) as author_count
MATCH (p:Paper) 
WITH author_count, count(p) as paper_count
MATCH ()-[r]->() 
RETURN author_count, paper_count, count(r) as relationship_count
"""