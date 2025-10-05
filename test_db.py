#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables
load_dotenv()

def test_database():
    uri = os.getenv('NEO4J_URI')
    user = os.getenv('NEO4J_USER') 
    password = os.getenv('NEO4J_PASSWORD')
    
    print(f"Testing connection to: {uri}")
    print(f"User: {user}")
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        # Test basic connection
        with driver.session() as session:
            # Check if database is accessible
            result = session.run("RETURN 'Connected!' as message")
            record = result.single()
            print(f"✅ Connection successful: {record['message']}")
            
            # Check total nodes
            result = session.run("MATCH (n) RETURN count(n) as total_nodes")
            record = result.single()
            total_nodes = record['total_nodes']
            print(f"📊 Total nodes in database: {total_nodes}")
            
            if total_nodes == 0:
                print("⚠️  Database is empty! This is likely why team formation is failing.")
                return False
            
            # Check for author nodes specifically
            result = session.run("MATCH (n:Author) RETURN count(n) as author_count LIMIT 1")
            record = result.single()
            author_count = record['author_count'] if record else 0
            print(f"👤 Author nodes: {author_count}")
            
            if author_count == 0:
                print("⚠️  No Author nodes found! Team formation requires Author nodes.")
                return False
            
            # Sample some authors
            result = session.run("MATCH (n:Author) RETURN n.author_name as name LIMIT 5")
            authors = [record['name'] for record in result]
            print(f"📝 Sample authors: {authors}")
            
            return True
            
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False
    finally:
        if 'driver' in locals():
            driver.close()

if __name__ == "__main__":
    test_database()