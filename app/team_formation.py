import logging
from collections import defaultdict, Counter
from datetime import datetime
import random
import numpy as np
import time
import os
import pandas as pd
from typing import List, Dict, Tuple, Optional, Any
from neo4j import GraphDatabase
import csv

logger = logging.getLogger(__name__)

class AlgorithmConfig:
    """Configuration class for managing algorithm settings and metadata - from AuraDB_0_4.ipynb"""
    
    def __init__(self):
        self.algorithms = {
            "ACET": {
                "name": "All-Connections-Equal Team Formation",
                "description": "Considers all types of connections equally",
                "seed_filter": "filter_authors_with_sufficient_connections",
                "member_finder": "find_member_near_team_and_highest_degree"
            },
            "CAT": {
                "name": "Co-Authorship Team Formation", 
                "description": "Builds teams only using co-authorship relations",
                "seed_filter": "filter_authors_with_written_connections",
                "member_finder": "find_member_near_team_with_written_connection"
            },
            "OAT": {
                "name": "Organizational Affiliation Team Formation",
                "description": "Builds teams only using co-working relations",
                "seed_filter": "filter_authors_with_sufficient_connections",
                "member_finder": "find_member_near_team_with_organizational_connection"
            },
            "PRT": {
                "name": "Prioritized Relationship Team Formation",
                "description": "Prioritizes co-authorship relations over organizational relations",
                "seed_filter": "filter_authors_with_written_connections",
                "member_finder": "find_member_near_team_with_prioritized_connection"
            },
            "COT": {
                "name": "Cohesion-Optimized Team Formation",
                "description": "Maximizes team cohesion by selecting members with most connections to existing team",
                "seed_filter": "filter_authors_with_sufficient_connections",
                "member_finder": "find_member_near_team_cohesion_optimized"
            },
            "TAT": {
                "name": "Time-Aware Team Formation",
                "description": "Considers recency of collaborations in team formation",
                "seed_filter": "filter_authors_with_sufficient_connections",
                "member_finder": "find_member_near_team_time_aware"
            },
            "CIT": {
                "name": "Citation-Optimized Team Formation",
                "description": "Optimizes team formation based on citation impact and collaboration strength",
                "seed_filter": "filter_authors_with_high_citation_connections",
                "member_finder": "find_member_near_team_citation_optimized"
            }
        }
    
    def get_algorithm_info(self, algorithm: str) -> Dict[str, str]:
        """Get algorithm information by code."""
        return self.algorithms.get(algorithm, {})
    
    def list_algorithms(self) -> List[Tuple[str, str, str]]:
        """Return list of (code, name, description) for all algorithms."""
        return [(code, info["name"], info["description"]) 
                for code, info in self.algorithms.items()]

class ScientificTeamFormation:
    """
    Scientific Team Formation System implementing all 7 algorithms from AuraDB_0_4.ipynb
    Based on AMİNER dataset with Neo4j cloud database
    
    Database Schema (from your Jupyter notebook):
    - (Author)-[WRITTEN]->(Paper)
    - (Author)-[WORKS_IN]->(Department/Organization) 
    - (Organization)-[INCLUDES]->(Department)
    
    Author properties: Author_ID, Author_Name, skills
    Paper properties: Paper_ID, Paper_Title, Combined_Keywords, n_Citation, Years_Passed
    Department properties: Dept_ID, Dept_Name
    Organization properties: Org_ID, Org_Name
    """
    
    def __init__(self):
        """Initialize with Neo4j database connection from environment"""
        self.driver = None
        self.config = AlgorithmConfig()
        self.performance_metrics = {}
        self.connect_to_neo4j()
        
        logger.info(f"ScientificTeamFormation initialized with Neo4j database")
    
    def connect_to_neo4j(self):
        """Connect to Neo4j cloud database using environment variables"""
        try:
            # Get Neo4j connection details from environment variables
            neo4j_uri = os.getenv('NEO4J_URI')
            neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
            neo4j_password = os.getenv('NEO4J_PASSWORD')
            
            if not neo4j_uri or not neo4j_password:
                logger.error("Neo4j connection details not found in environment variables")
                raise Exception("Neo4j connection details missing")
            
            logger.info(f"Connecting to Neo4j at: {neo4j_uri}")
            
            # Configure extended timeouts for serverless mode (AuraDB with Graph Analytics Serverless)
            self.driver = GraphDatabase.driver(
                neo4j_uri, 
                auth=(neo4j_user, neo4j_password),
                # Much longer timeouts for complex team formation algorithms
                connection_timeout=180.0,  # 3 minutes for initial connection
                max_connection_lifetime=600.0,  # 10 minutes max connection lifetime
                max_connection_pool_size=15,
                connection_acquisition_timeout=300.0  # 5 minutes to acquire connection
            )
            
            # Test connection with increased timeout
            with self.driver.session(default_access_mode="READ") as session:
                # Use query with timeout for serverless mode
                result = session.run("RETURN 1 as test", timeout=60)
                test_record = result.single()
                if test_record and test_record["test"] == 1:
                    logger.info("Successfully connected to Neo4j cloud database with extended timeouts")
                else:
                    raise Exception("Connection test failed")
                    
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise Exception(f"Neo4j connection failed: {str(e)}")
    
    def get_available_algorithms(self):
        """Return the 7 team formation algorithms"""
        return self.config.algorithms
    
    def validate_algorithm(self, algorithm: str) -> bool:
        """Validate algorithm from Jupyter notebook"""
        if algorithm not in self.config.algorithms:
            logger.warning(f"Unknown algorithm: {algorithm}")
            return False
            
        algo_info = self.config.algorithms[algorithm]
        required_methods = [algo_info["seed_filter"], algo_info["member_finder"]]
        
        for method_name in required_methods:
            if not hasattr(self, method_name):
                logger.error(f"Algorithm {algorithm} missing method: {method_name}")
                return False
                
        logger.info(f"Algorithm {algorithm} validation successful")
        return True

    # ==================== SEED FILTERING METHODS (From Jupyter Notebook) ====================
    
    def filter_authors_with_sufficient_connections(self, tx, keywords: List[str], max_distance: int = 4, limit: int = 10) -> List[Tuple]:
        """Find authors who have the first keyword and sufficient connections to potentially form a team."""
        method_start = time.time()
        first_keyword = keywords[0]
        min_connections = len(keywords) - 1
        
        query = f"""
        MATCH (a:Author)-[:WRITTEN]->(p:Paper)
        WHERE any(kw IN split(p.Combined_Keywords, ', ') WHERE toLower(kw) CONTAINS toLower($first_keyword))
        OR (a.skills IS NOT NULL AND any(skill IN split(a.skills, ', ') WHERE toLower(skill) CONTAINS toLower($first_keyword)))
        
        WITH a, SIZE([()--(a) | 1]) AS degree
        
        MATCH (a)-[*1..{max_distance}]-(conn:Author)
        WHERE conn <> a
        
        WITH a, degree, COUNT(DISTINCT conn) AS connection_count
        WHERE connection_count >= $min_connections
        
        RETURN a.Author_ID AS author_id, 
               a.Author_Name AS author_name, 
               degree,
               a.skills AS skills,
               connection_count
        ORDER BY degree DESC
        LIMIT $limit
        """
        
        try:
            result = tx.run(
                query, 
                first_keyword=first_keyword, 
                min_connections=min_connections, 
                limit=limit
            )
            data = result.values()
            logger.info(f"filter_authors_with_sufficient_connections found {len(data)} authors in {time.time() - method_start:.2f}s")
            return data
        except Exception as e:
            logger.error(f"Error in filter_authors_with_sufficient_connections: {e}")
            return []

    def filter_authors_with_written_connections(self, tx, keywords: List[str], max_distance: int = 4, limit: int = 10) -> List[Tuple]:
        """Find authors who have the first keyword and sufficient WRITTEN connections."""
        method_start = time.time()
        first_keyword = keywords[0]
        min_connections = len(keywords) - 1
        
        query = f"""
        MATCH (a:Author)-[:WRITTEN]->(p:Paper)
        WHERE any(kw IN split(p.Combined_Keywords, ', ') WHERE toLower(kw) CONTAINS toLower($first_keyword))
        OR (a.skills IS NOT NULL AND any(skill IN split(a.skills, ', ') WHERE toLower(skill) CONTAINS toLower($first_keyword)))
        
        WITH a, SIZE([(a)-[:WRITTEN]-() | 1]) AS degree
        
        MATCH (a)-[:WRITTEN*1..{max_distance}]-(conn:Author)
        WHERE conn <> a
        
        WITH a, degree, COUNT(DISTINCT conn) AS connection_count
        WHERE connection_count >= $min_connections
        
        RETURN a.Author_ID AS author_id, 
               a.Author_Name AS author_name, 
               degree,
               a.skills AS skills,
               connection_count
        ORDER BY degree DESC
        LIMIT $limit
        """
        
        try:
            result = tx.run(
                query, 
                first_keyword=first_keyword, 
                min_connections=min_connections, 
                limit=limit
            )
            data = result.values()
            logger.info(f"filter_authors_with_written_connections found {len(data)} authors in {time.time() - method_start:.2f}s")
            return data
        except Exception as e:
            logger.error(f"Error in filter_authors_with_written_connections: {e}")
            return []

    def filter_authors_with_high_citation_connections(self, tx, keywords: List[str], max_distance: int = 3, limit: int = 10) -> List[Tuple]:
        """Find initial candidate authors for CIT based on keyword-specific citations."""
        method_start = time.time()
        first_keyword = keywords[0]
        
        query = """
        MATCH (author:Author)
        WHERE author.skills IS NOT NULL 
              AND any(skill IN split(author.skills, ', ') WHERE toLower(skill) CONTAINS toLower($skill))
        
        OPTIONAL MATCH (author)-[:WRITTEN]->(paper:Paper)
        WHERE any(kw IN split(paper.Combined_Keywords, ', ') WHERE toLower(kw) CONTAINS toLower($skill))
        
        WITH author, 
             SUM(coalesce(paper.n_Citation, 0)) AS skill_citations
        
        RETURN author.Author_ID AS author_id,
               author.Author_Name AS author_name,
               author.skills AS skills,
               skill_citations AS citation_count
        ORDER BY skill_citations DESC
        LIMIT $limit
        """
        
        try:
            result = tx.run(
                query, 
                skill=first_keyword,
                limit=limit,
                timeout=180  # 3 minute timeout for serverless mode
            )
            data = result.values()
            logger.info(f"filter_authors_with_high_citation_connections found {len(data)} authors in {time.time() - method_start:.2f}s")
            return data
        except Exception as e:
            logger.error(f"Error in filter_authors_with_high_citation_connections: {e}")
            return []

    # ==================== MEMBER FINDING METHODS (From Jupyter Notebook) ====================

    def find_member_near_team_and_highest_degree(self, tx, team_ids: List[str], keyword: str, max_distance: int, excluded_ids: List[str] = None, **kwargs) -> Optional[Dict]:
        """Find an author who has the required keyword, is close to team members, and has highest degree."""
        excluded_ids = excluded_ids or []
        
        query = f"""
        MATCH (team_member:Author)
        WHERE team_member.Author_ID IN $team_ids
                
        WITH COLLECT(team_member) AS team
        
        UNWIND team AS node
        MATCH path = (node)-[*1..{max_distance}]-(a:Author)
        
        WHERE (a.skills IS NOT NULL AND any(skill IN split(a.skills, ', ') WHERE toLower(skill) CONTAINS toLower($keyword)))
          AND NOT a.Author_ID IN $team_ids 
          AND NOT a.Author_ID IN $excluded_ids
        
        WITH a, 
             MIN(length(path)) AS distance, 
             SIZE([()--(a) | 1]) AS degree
        
        ORDER BY distance ASC, degree DESC
        LIMIT 1
        
        RETURN a.Author_ID AS author_id, 
               a.Author_Name AS author_name, 
               degree, 
               distance,
               a.skills AS skills
        """
        
        try:
            result = tx.run(
                query, 
                team_ids=team_ids, 
                keyword=keyword, 
                excluded_ids=excluded_ids
            )
            record = result.single()
            return dict(record) if record else None
        except Exception as e:
            logger.error(f"Error in find_member_near_team_and_highest_degree: {e}")
            return None

    def find_member_near_team_with_written_connection(self, tx, team_ids: List[str], keyword: str, max_distance: int, excluded_ids: List[str] = None, **kwargs) -> Optional[Dict]:
        """Find an author connected to team members through WRITTEN relationships."""
        excluded_ids = excluded_ids or []
        
        query = f"""
        MATCH (team_member:Author)
        WHERE team_member.Author_ID IN $team_ids
        
        WITH COLLECT(team_member) AS team
        
        UNWIND team AS node
        MATCH path = (node)-[:WRITTEN*1..{max_distance}]-(a:Author)
        
        WHERE (a.skills IS NOT NULL AND any(skill IN split(a.skills, ', ') WHERE toLower(skill) CONTAINS toLower($keyword)))
          AND NOT a.Author_ID IN $team_ids 
          AND NOT a.Author_ID IN $excluded_ids
        
        WITH a, 
             MIN(length(path)) AS distance, 
             SIZE([()--(a) | 1]) AS degree
        
        ORDER BY distance ASC, degree DESC
        LIMIT 1
        
        RETURN a.Author_ID AS author_id, 
               a.Author_Name AS author_name, 
               degree, 
               distance,
               a.skills AS skills
        """
        
        try:
            result = tx.run(
                query, 
                team_ids=team_ids, 
                keyword=keyword, 
                excluded_ids=excluded_ids
            )
            record = result.single()
            return dict(record) if record else None
        except Exception as e:
            logger.error(f"Error in find_member_near_team_with_written_connection: {e}")
            return None

    def find_member_near_team_with_organizational_connection(self, tx, team_ids: List[str], keyword: str, max_distance: int, excluded_ids: List[str] = None, **kwargs) -> Optional[Dict]:
        """Find an author connected to team members through organizational relationships."""
        excluded_ids = excluded_ids or []
        
        query = f"""
        MATCH (team_member:Author)
        WHERE team_member.Author_ID IN $team_ids
        
        WITH COLLECT(team_member) AS team
        
        UNWIND team AS node
        
        MATCH path = (node)-[:WORKS_IN|INCLUDES*1..{max_distance}]-(candidate:Author)
        WHERE any(rel IN relationships(path) WHERE type(rel) IN ['WORKS_IN', 'INCLUDES'])
          AND (candidate.skills IS NOT NULL AND any(skill IN split(candidate.skills, ', ') WHERE toLower(skill) CONTAINS toLower($keyword)))
          AND NOT candidate.Author_ID IN $team_ids 
          AND NOT candidate.Author_ID IN $excluded_ids
        
        WITH candidate, node, MIN(length(path)) AS path_length,
             SIZE([(candidate)-[:WORKS_IN]->() | 1]) as org_degree
        
        WITH candidate, MIN(path_length) AS min_distance, 
             COUNT(node) AS connected_to_members,
             org_degree
        
        ORDER BY min_distance ASC, org_degree DESC, connected_to_members DESC
        LIMIT 1
        
        RETURN candidate.Author_ID AS author_id, 
               candidate.Author_Name AS author_name, 
               org_degree AS degree, 
               min_distance AS distance,
               connected_to_members,
               candidate.skills AS skills
        """
        
        try:
            result = tx.run(
                query, 
                team_ids=team_ids, 
                keyword=keyword, 
                excluded_ids=excluded_ids
            )
            record = result.single()
            return dict(record) if record else None
        except Exception as e:
            logger.error(f"Error in find_member_near_team_with_organizational_connection: {e}")
            return None

    def find_member_near_team_with_prioritized_connection(self, tx, team_ids: List[str], keyword: str, max_distance: int, excluded_ids: List[str] = None, **kwargs) -> Optional[Dict]:
        """Find an author with prioritized connections (WRITTEN first, then organizational)."""
        excluded_ids = excluded_ids or []
        
        query = f"""
        MATCH (team_member:Author)
        WHERE team_member.Author_ID IN $team_ids
        
        WITH COLLECT(team_member) AS team
        
        UNWIND team AS node
        
        OPTIONAL MATCH (node)-[:WRITTEN]-(:Paper)-[:WRITTEN]-(a:Author)
        WHERE (a.skills IS NOT NULL AND any(skill IN split(a.skills, ', ') WHERE toLower(skill) CONTAINS toLower($keyword)))
          AND NOT a.Author_ID IN $team_ids 
          AND NOT a.Author_ID IN $excluded_ids

        OPTIONAL MATCH (node)-[:WORKS_IN|INCLUDES*1..4]-(a2:Author)
        WHERE (a2.skills IS NOT NULL AND any(skill IN split(a2.skills, ', ') WHERE toLower(skill) CONTAINS toLower($keyword)))
          AND NOT a2.Author_ID IN $team_ids 
          AND NOT a2.Author_ID IN $excluded_ids
          AND a IS NULL

        OPTIONAL MATCH (node)-[*1..{max_distance}]-(a3:Author)
        WHERE (a3.skills IS NOT NULL AND any(skill IN split(a3.skills, ', ') WHERE toLower(skill) CONTAINS toLower($keyword)))
          AND NOT a3.Author_ID IN $team_ids 
          AND NOT a3.Author_ID IN $excluded_ids
          AND a IS NULL AND a2 IS NULL

        WITH COALESCE(a, a2, a3) AS author,
             CASE WHEN a IS NOT NULL THEN 'WRITTEN'
                  WHEN a2 IS NOT NULL THEN 'WORKS_IN' 
                  ELSE 'ANY_PATH' END AS connection_type,
             CASE WHEN a IS NOT NULL THEN 2
                  WHEN a2 IS NOT NULL THEN 3
                  ELSE {max_distance} END AS distance
        
        WHERE author IS NOT NULL
        
        WITH author, 
             MIN(distance) AS distance, 
             SIZE([()--(author) | 1]) AS degree,
             connection_type
        
        ORDER BY connection_type ASC, distance ASC, degree DESC
        LIMIT 1
        
        RETURN author.Author_ID AS author_id, 
               author.Author_Name AS author_name, 
               degree, 
               distance,
               author.skills AS skills
        """
        
        try:
            result = tx.run(
                query, 
                team_ids=team_ids, 
                keyword=keyword, 
                excluded_ids=excluded_ids
            )
            record = result.single()
            return dict(record) if record else None
        except Exception as e:
            logger.error(f"Error in find_member_near_team_with_prioritized_connection: {e}")
            return None

    def find_member_near_team_cohesion_optimized(self, tx, team_ids: List[str], keyword: str, max_distance: int, 
                                               cohesion_weight: float = 0.7, distance_weight: float = 0.3, 
                                               excluded_ids: List[str] = None, **kwargs) -> Optional[Dict]:
        """Find an author who maximizes team cohesion."""
        excluded_ids = excluded_ids or []
        
        # First find candidates
        candidates = self.find_candidates_with_cohesion(tx, team_ids, keyword, max_distance, excluded_ids)
        
        if not candidates:
            return None
        
        # Evaluate cohesion for each candidate
        best_candidate = None
        best_score = -1
        
        for candidate_id, candidate_name, candidate_distance in candidates:
            try:
                potential_cohesion = self.calculate_potential_cohesion(tx, team_ids, candidate_id)
                
                # Combined score using weights
                distance_score = 1.0 / (candidate_distance + 0.1)
                combined_score = (cohesion_weight * potential_cohesion) + (distance_weight * distance_score)
                
                if combined_score > best_score:
                    best_score = combined_score
                    best_candidate = {
                        'author_id': candidate_id,
                        'author_name': candidate_name,
                        'distance': candidate_distance,
                        'degree': potential_cohesion,
                        'skills': ''  # Will be filled by calling function
                    }
            except Exception as e:
                logger.error(f"Error evaluating candidate {candidate_name}: {e}")
        
        return best_candidate

    def find_candidates_with_cohesion(self, tx, team_ids: List[str], keyword: str, max_distance: int, excluded_ids: List[str] = None) -> List[Tuple]:
        """Helper method to find candidates for cohesion optimization."""
        excluded_ids = excluded_ids or []
        
        query = f"""
        MATCH (team_member:Author)
        WHERE team_member.Author_ID IN $team_ids
        WITH COLLECT(team_member) AS team
        UNWIND team AS node
        MATCH path = (node)-[*1..{max_distance}]-(a:Author)
        WHERE (a.skills IS NOT NULL AND any(skill IN split(a.skills, ', ') WHERE toLower(skill) CONTAINS toLower($keyword)))
        AND NOT a.Author_ID IN $team_ids 
        AND NOT a.Author_ID IN $excluded_ids
        WITH a, MIN(length(path)) AS distance
        RETURN a.Author_ID AS author_id, a.Author_Name AS author_name, distance
        ORDER BY distance ASC
        LIMIT 10
        """
        
        try:
            result = tx.run(query, team_ids=team_ids, keyword=keyword, excluded_ids=excluded_ids)
            return result.values()
        except Exception as e:
            logger.error(f"Error in find_candidates_with_cohesion: {e}")
            return []

    def calculate_potential_cohesion(self, tx, team_ids: List[str], candidate_id: str) -> float:
        """Calculate potential cohesion contribution of a candidate."""
        query = """
        MATCH (candidate:Author {Author_ID: $candidate_id})
        
        UNWIND $team_ids AS team_member_id
        MATCH (team_member:Author {Author_ID: team_member_id})
        
        OPTIONAL MATCH (candidate)-[:WRITTEN]->(p:Paper)<-[:WRITTEN]-(team_member)
        WITH candidate, team_member, COLLECT(DISTINCT p) AS shared_papers
        
        OPTIONAL MATCH (candidate)-[:WORKS_IN]->(o:Organization|Department)<-[:WORKS_IN]-(team_member)
        WITH team_member, SIZE(shared_papers) AS paper_count, COLLECT(DISTINCT o) AS shared_orgs
        
        WITH team_member.Author_ID AS member_id, 
             paper_count, 
             SIZE(shared_orgs) AS org_count,
             paper_count * 2 + SIZE(shared_orgs) AS pair_score
        
        RETURN SUM(pair_score) AS total_cohesion
        """
        
        try:
            result = tx.run(query, team_ids=team_ids, candidate_id=candidate_id)
            record = result.single()
            return record["total_cohesion"] if record else 0
        except Exception as e:
            logger.error(f"Error in calculate_potential_cohesion: {e}")
            return 0

    def find_member_near_team_time_aware(self, tx, team_ids: List[str], keyword: str, max_distance: int = 4, 
                                       time_threshold: int = 5, excluded_ids: List[str] = None, 
                                       null_years_option: int = 1, **kwargs) -> Optional[Dict]:
        """Find team members prioritizing recent collaborations."""
        excluded_ids = excluded_ids or []
        
        # Determine null replacement value
        if null_years_option == 1:
            null_replacement = time_threshold + 1
        elif null_years_option == 2:
            null_replacement = max(0, time_threshold - 1)
        elif null_years_option == 3:
            null_replacement = random.randint(0, 30)
        else:
            null_replacement = time_threshold + 1
        
        query = f"""
        MATCH (author:Author)
        WHERE author.skills IS NOT NULL 
              AND any(skill IN split(author.skills, ', ') WHERE toLower(skill) CONTAINS toLower($keyword))
              AND NOT author.Author_ID IN $excluded_ids
        
        WITH author
        MATCH (team:Author)
        WHERE team.Author_ID IN $team_ids AND author <> team
        
        MATCH (author)-[:WRITTEN]->(paper:Paper)<-[:WRITTEN]-(team)
        
        WHERE coalesce(paper.Years_Passed, {null_replacement}) <= $time_threshold
        
        WITH DISTINCT author, 
             2 AS direct_distance,
             min(coalesce(paper.Years_Passed, {null_replacement})) AS min_years_passed
        
        OPTIONAL MATCH (author)-[:WRITTEN]->(p:Paper)
        WHERE any(kw IN split(p.Combined_Keywords, ', ') WHERE toLower(kw) CONTAINS toLower($keyword))
        WITH author, direct_distance, min_years_passed,
             SUM(coalesce(p.n_Citation, 0)) AS citation_count
        
        ORDER BY min_years_passed ASC, direct_distance ASC, citation_count DESC
        LIMIT 1
        
        RETURN author.Author_ID AS author_id,
               author.Author_Name AS author_name,
               author.skills AS skills,
               citation_count,
               direct_distance AS distance,
               min_years_passed AS recency
        """
        
        try:
            result = tx.run(
                query,
                keyword=keyword,
                excluded_ids=excluded_ids,
                team_ids=team_ids,
                time_threshold=time_threshold
            )
            record = result.single()
            return dict(record) if record else None
        except Exception as e:
            logger.error(f"Error in find_member_near_team_time_aware: {e}")
            return None

    def find_member_near_team_citation_optimized(self, tx, team_ids: List[str], keyword: str, max_distance: int, 
                                               excluded_ids: List[str] = None, time_threshold: int = 5, 
                                               null_years_option: int = 1, sort_order: str = "citation_first", **kwargs) -> Optional[Dict]:
        """Find team members prioritizing citation impact and recent collaborations."""
        excluded_ids = excluded_ids or []
        
        # Determine null replacement value
        if null_years_option == 1:
            null_replacement = time_threshold + 1
        elif null_years_option == 2:
            null_replacement = max(1, time_threshold - 1)
        elif null_years_option == 3:
            null_replacement = random.randint(0, 30)
        else:
            null_replacement = time_threshold + 1
    
        # Determine ORDER BY clause based on sort_order parameter
        if sort_order == "recency_first":
            order_clause = "ORDER BY min_years_passed, citation_count DESC"
        elif sort_order == "citation_first":
            order_clause = "ORDER BY citation_count DESC, min_years_passed"
        elif sort_order == "distance_citation":
            order_clause = "ORDER BY min_distance, citation_count DESC, min_years_passed"
        else:
            order_clause = "ORDER BY min_distance, min_years_passed, citation_count DESC"
        
        query = f"""
        MATCH (author:Author)
        WHERE author.skills IS NOT NULL 
              AND any(skill IN split(author.skills, ', ') WHERE toLower(skill) CONTAINS toLower($keyword))
              AND NOT author.Author_ID IN $excluded_ids
        
        WITH author
        
        MATCH (team:Author)
        WHERE team.Author_ID IN $team_ids

        MATCH (author)-[w1:WRITTEN]->(paper:Paper)<-[w2:WRITTEN]-(team)
        WHERE coalesce(paper.Years_Passed, $null_replacement) <= $time_threshold
        
        WITH author, team, paper, 
             2 AS path_length,
             coalesce(paper.Years_Passed, $null_replacement) AS years_passed

        WITH author, min(path_length) AS min_distance, min(years_passed) AS min_years_passed

        OPTIONAL MATCH (author)-[:WRITTEN]->(p:Paper)
        WHERE any(kw IN split(p.Combined_Keywords, ', ') WHERE toLower(kw) CONTAINS toLower($keyword))
        WITH author, min_distance, min_years_passed,
             SUM(coalesce(p.n_Citation, 0)) AS citation_count
        
        {order_clause}
        LIMIT 1
        
        RETURN author.Author_ID AS author_id,
               author.Author_Name AS author_name,
               author.skills AS skills,
               citation_count,
               min_distance AS distance,
               min_years_passed AS recency
        """
        
        try:
            result = tx.run(
                query,
                keyword=keyword,
                excluded_ids=excluded_ids,
                team_ids=team_ids,
                time_threshold=time_threshold,
                null_replacement=null_replacement
            )
            record = result.single()
            
            if record:
                logger.debug(f"CIT found author {record['author_name']} with citation count: {record.get('citation_count', 0)}")
            
            return dict(record) if record else None
        except Exception as e:
            logger.error(f"Error in find_member_near_team_citation_optimized: {e}")
            return None

    # ==================== MAIN TEAM BUILDING METHOD (From Jupyter Notebook) ====================
    
    def build_teams(self, keywords: List[str], max_distance: int = 3, initial_distance: int = 2,
                   max_increase: int = 5, cohesion_weight: float = 0.7, distance_weight: float = 0.3, 
                   limit: int = 10, excluded_ids: List[str] = None, algorithm: str = "ACET", 
                   time_threshold: int = 5, null_years_option: int = 1, use_org_connections: bool = True,
                   sort_order: str = "citation_first", single_skill_per_author: bool = True) -> Tuple[int, pd.DataFrame]:
        """
        Build teams based on connections and expertise using specified algorithm.
        This is the exact logic from AuraDB_0_4.ipynb
        """
        build_start_time = time.time()
        excluded_ids = excluded_ids or []
        
        # Validate algorithm
        if not self.validate_algorithm(algorithm):
            logger.error(f"Invalid algorithm: {algorithm}. Using ACET as fallback.")
            algorithm = "ACET"
        
        algo_info = self.config.get_algorithm_info(algorithm)
        logger.info(f"Starting team building with {algo_info.get('name', algorithm)}")
        
        # Initialize DataFrame
        teams_df = pd.DataFrame(columns=[
            "Team", "Author ID", "Author Name", "Matching Skills", 
            "Added For Skill", "Status", "Intra-Team Distance", "Completion_Time", "Algorithm"
        ])
        
        # Get the appropriate methods
        seed_filter_method = getattr(self, algo_info["seed_filter"])
        member_finder_method = getattr(self, algo_info["member_finder"])
        
        with self.driver.session() as session:
            # Find seed authors
            logger.info(f"Searching for seed authors using {algorithm} algorithm...")
            initial_candidates = session.execute_read(
                seed_filter_method,
                keywords,
                max_distance=max_distance,
                limit=limit
            )
            
            if not initial_candidates:
                logger.warning("No suitable seed authors found for the first keyword.")
                return 0, teams_df
                
            logger.info(f"Found {len(initial_candidates)} potential seed authors")
            
            # Build teams
            successful_teams = 0
            total_attempts = len(initial_candidates)
            
            for i, member in enumerate(initial_candidates):
                if member[0] in excluded_ids:
                    logger.info(f"Skipping seed author {member[1]} (already in another team)")
                    continue
                    
                team_start_time = time.time()
                logger.info(f"Starting Team {i+1} with seed author: {member[1]}")
                
                # Initialize team
                author_id = member[0]
                team = [author_id]
                team_distance = 0
                all_keywords_matched = True
                skills_added_for = {author_id: keywords[0]}
                
                # Find team members for remaining keywords
                for k_index, keyword in enumerate(keywords[1:], 1):
                    logger.info(f"Looking for member #{len(team)+1} with expertise in: {keyword}")
                    distance = initial_distance
                    member_found = False
                    
                    # Try increasing distances
                    while distance <= max_increase:
                        logger.debug(f"Search distance = {distance}")
                        
                        # Find member using the selected algorithm
                        if algorithm == "CIT":
                            new_member = session.execute_read(
                                member_finder_method,
                                team, keyword, distance, excluded_ids,
                                time_threshold=time_threshold,
                                null_years_option=null_years_option,
                                sort_order=sort_order
                            )
                        elif algorithm == "TAT":
                            new_member = session.execute_read(
                                member_finder_method,
                                team, keyword, 
                                max_distance=distance,
                                time_threshold=time_threshold,
                                excluded_ids=excluded_ids,
                                null_years_option=null_years_option
                            )
                        elif algorithm == "COT":
                            new_member = session.execute_read(
                                member_finder_method,
                                team, keyword, distance,
                                cohesion_weight=cohesion_weight,
                                distance_weight=distance_weight,
                                excluded_ids=excluded_ids
                            )
                        else:
                            new_member = session.execute_read(
                                member_finder_method,
                                team, keyword, distance, excluded_ids
                            )
                        
                        if new_member:
                            team.append(new_member['author_id'])
                            skills_added_for[new_member['author_id']] = keyword
                            team_distance += new_member.get('distance', distance)
                            member_found = True
                            logger.info(f"SUCCESS! Found: {new_member['author_name']}")
                            break                            
                        elif algorithm in ["TAT", "CIT"] and use_org_connections:
                            # Try organizational connections as fallback
                            new_member = session.execute_read(
                                self.find_member_near_team_with_organizational_connection,
                                team, keyword, distance, excluded_ids
                            )
                            if new_member:
                                team.append(new_member['author_id'])
                                skills_added_for[new_member['author_id']] = keyword
                                team_distance += new_member.get('distance', distance)
                                member_found = True
                                logger.info(f"SUCCESS! Found: {new_member['author_name']} using organizational connections")
                                break
                            else:
                                distance += 1
                        else:
                            distance += 1
                
                    if not member_found:
                        all_keywords_matched = False
                        logger.warning(f"FAILED: Could not find author with expertise in '{keyword}'")
                        break
                    
                    logger.info(f"Team progress: {len(team)}/{len(keywords)} members added")
                
                # Calculate results
                team_time = time.time() - team_start_time
                
                if all_keywords_matched:
                    status = "complete"
                    successful_teams += 1
                    logger.info(f"TEAM {i+1} COMPLETE! ({len(team)} members, time: {team_time:.2f}s)")
                else:
                    status = "incomplete"
                    logger.warning(f"TEAM {i+1} INCOMPLETE ({len(team)} members, time: {team_time:.2f}s)")
                
                # Add to DataFrame
                team_label = f"Team {i + 1}"
                teams_df = self.add_team_to_df(
                    teams_df, team_label, team, keywords, 
                    status, team_distance, team_time/60, skills_added_for, algorithm
                )
                
                excluded_ids.extend(team)
        
        # Log performance
        total_time = time.time() - build_start_time
        self.log_performance_metrics(algorithm, total_time, successful_teams, total_attempts)
        
        logger.info(f"Team building completed: {successful_teams}/{total_attempts} successful teams in {total_time:.2f}s")
        return successful_teams, teams_df

    # ==================== UTILITY METHODS (From Jupyter Notebook) ====================
            
    def get_member_details(self, tx, author_ids: List[str]) -> List[Tuple]:
        """Get detailed information about specific authors."""
        query = """
        MATCH (a:Author)
        WHERE a.Author_ID IN $author_ids
        RETURN a.Author_ID AS author_id, 
               a.Author_Name AS author_name, 
               a.skills AS skills
        """
        
        try:
            result = tx.run(query, author_ids=author_ids)
            return result.values()
        except Exception as e:
            logger.error(f"Error in get_member_details: {e}")
            return []

    def get_enhanced_member_details(self, tx, author_ids: List[str]) -> List[Dict]:
        """Get enhanced detailed information about specific authors including papers, organizations, and all skills."""
        query = """
        MATCH (a:Author)
        WHERE a.Author_ID IN $author_ids
        
        // Get paper count and total citation count for all papers
        OPTIONAL MATCH (a)-[:WRITTEN]->(p:Paper)
        WITH a, COUNT(DISTINCT p) as paper_count, SUM(COALESCE(p.n_Citation, 0)) AS total_citations
        
        // Get all organizational affiliations (both direct and through departments)
        OPTIONAL MATCH (a)-[:WORKS_IN]->(org:Organization)
        OPTIONAL MATCH (a)-[:WORKS_IN]->(dept:Department)
        OPTIONAL MATCH (a)-[:WORKS_IN]->(dept2:Department)<-[:INCLUDES]-(parent_org:Organization)
        
        WITH a, paper_count, total_citations,
             COLLECT(DISTINCT org.Org_Name) + 
             COLLECT(DISTINCT dept.Dept_Name) + 
             COLLECT(DISTINCT parent_org.Org_Name) AS all_orgs
        
        RETURN a.Author_ID AS author_id, 
               a.Author_Name AS author_name, 
               COALESCE(a.skills, '') AS skills,
               COALESCE(paper_count, 0) as paper_count,
               [org_name IN all_orgs WHERE org_name IS NOT NULL AND org_name <> ''] AS organizations,
               COALESCE(total_citations, 0) AS total_citations
        ORDER BY a.Author_Name
        """
        
        try:
            result = tx.run(query, author_ids=author_ids)
            enhanced_details = []
            
            for record in result:
                # Process skills - clean up and format properly
                skills_str = record['skills'] or ''
                if skills_str:
                    # Remove quotes and clean up
                    skills_str = skills_str.replace('"', '').replace("'", "").strip()
                    # Handle various separators
                    if ',' in skills_str:
                        skills_list = [s.strip() for s in skills_str.split(',') if s.strip()]
                    elif ';' in skills_str:
                        skills_list = [s.strip() for s in skills_str.split(';') if s.strip()]
                    else:
                        skills_list = [skills_str] if skills_str else []
                    
                    # Clean and join skills
                    cleaned_skills = [s for s in skills_list if len(s) > 1]
                    skills_str = ', '.join(cleaned_skills) if cleaned_skills else 'No specific skills listed'
                else:
                    skills_str = 'No skills data available'
                
                # Process organizations - clean up the list
                organizations = record['organizations'] or []
                cleaned_orgs = []
                for org in organizations:
                    if org and org.strip() and len(org.strip()) > 1:
                        cleaned_orgs.append(org.strip())
                
                author_detail = {
                    'author_id': record['author_id'],
                    'author_name': record['author_name'],
                    'skills': skills_str,  # Keep it as 'skills' for consistency
                    'paper_count': record['paper_count'],
                    'organizations': cleaned_orgs,
                    'total_citations': record['total_citations']
                }
                enhanced_details.append(author_detail)
                
            logger.info(f"Retrieved enhanced details for {len(enhanced_details)} authors")
            return enhanced_details
            
        except Exception as e:
            logger.error(f"Error in get_enhanced_member_details: {e}")
            # Return basic structure even on error
            fallback_details = []
            for aid in author_ids:
                fallback_details.append({
                    'author_id': aid,
                    'author_name': f'Author {aid}',
                    'skills': 'Data unavailable',
                    'paper_count': 0,
                    'organizations': [],
                    'total_citations': 0
                })
            return fallback_details

    def find_matching_skills(self, skills_str: str, keywords: List[str]) -> List[str]:
        """Find skills from an author that match any of the required keywords."""
        if not skills_str:
            return []
            
        skills_list = [skill.strip() for skill in skills_str.split(",") if skill.strip()]
        matching_skills = set()

        for skill in skills_list:
            for keyword in keywords:
                if keyword.lower() in skill.lower():
                    matching_skills.add(skill)
                    break

        return list(matching_skills)

    def add_team_to_df(self, df: pd.DataFrame, team_label: str, team: List[str], 
        keywords: List[str], status: str, team_distance: int, 
        time_takes: float, skills_added_for: Dict[str, str] = None, 
        algorithm: str = None) -> pd.DataFrame:
        """Add a team's information to the DataFrame."""
        skills_added_for = skills_added_for or {}
        team_data = []
        
        if team:
            with self.driver.session() as session:
                try:
                    members_details = session.execute_read(self.get_enhanced_member_details, team)

                    for member_detail in members_details:
                        member_id = member_detail['author_id']
                        name = member_detail['author_name']
                        skills = member_detail['skills']
                        
                        matching_skills = self.find_matching_skills(skills, keywords)
                        matching_skill_str = ", ".join(matching_skills) if matching_skills else "No matching skills"
                        
                        added_for = skills_added_for.get(member_id, "Seed Author")
                        
                        team_data.append([
                            team_label, member_id, name, matching_skill_str, added_for,
                            status, team_distance, time_takes, algorithm or "Unknown"
                        ])
                except Exception as e:
                    logger.error(f"Error getting team member details: {e}")
        
        if team_data:
            columns = [
                "Team", "Author ID", "Author Name", "Matching Skills", 
                "Added For Skill", "Status", "Intra-Team Distance", "Completion_Time", "Algorithm"
            ]
            team_df = pd.DataFrame(team_data, columns=columns)
            return pd.concat([df, team_df], ignore_index=True)
            
        return df

    def log_performance_metrics(self, algorithm: str, total_time: float, successful_teams: int, total_attempts: int):
        """Log performance metrics for analysis."""
        if algorithm not in self.performance_metrics:
            self.performance_metrics[algorithm] = []
        
        metrics = {
            'timestamp': datetime.now(),
            'total_time': total_time,
            'successful_teams': successful_teams,
            'total_attempts': total_attempts,
            'success_rate': successful_teams / total_attempts if total_attempts > 0 else 0
        }
        
        self.performance_metrics[algorithm].append(metrics)
        logger.info(f"Performance metrics logged for {algorithm}: {metrics}")
    
    def get_keywords(self, limit=100):
        """Get available keywords from database"""
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                query = """
                MATCH (a:Author)
                WHERE a.skills IS NOT NULL
                WITH split(a.skills, ', ') AS skill_list
                UNWIND skill_list AS skill
                WITH trim(skill) AS clean_skill
                WHERE clean_skill <> ''
                RETURN DISTINCT clean_skill AS keyword
                ORDER BY keyword
                LIMIT $limit
                """
                result = session.run(query, limit=limit)
                return [record["keyword"] for record in result]
        except Exception as e:
            logger.error(f"Error getting keywords: {e}")
            return []
    
    def search_authors(self, query_text, limit=10):
        """Search authors by name or skills"""
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                query = """
                MATCH (a:Author)
                WHERE toLower(a.Author_Name) CONTAINS toLower($query)
                   OR (a.skills IS NOT NULL AND toLower(a.skills) CONTAINS toLower($query))
                RETURN a.Author_ID AS id, a.Author_Name AS name, a.skills AS skills
                LIMIT $limit
                """
                result = session.run(query, query=query_text, limit=limit)
                return [{"id": record["id"], "name": record["name"], "skills": record["skills"]} 
                       for record in result]
        except Exception as e:
            logger.error(f"Error searching authors: {e}")
            return []
    
    def test_database_connection(self):
        """Test database connectivity and log basic stats"""
        try:
            with self.driver.session() as session:
                # Test basic connectivity
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]
                
                # Get basic counts
                author_count = session.run("MATCH (a:Author) RETURN count(a) as count").single()["count"]
                paper_count = session.run("MATCH (p:Paper) RETURN count(p) as count").single()["count"]
                
                logger.info(f"Database connection test successful")
                logger.info(f"Authors: {author_count}, Papers: {paper_count}")
                return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def debug_database_structure(self):
        """Debug method to test database structure"""
        try:
            with self.driver.session() as session:
                # Test basic queries with your schema
                result1 = session.run("MATCH (a:Author) RETURN count(a) as total_authors LIMIT 1")
                total_authors = result1.single()["total_authors"]
                
                result2 = session.run("""
                    MATCH (a:Author) 
                    WHERE a.skills IS NOT NULL 
                    RETURN a.Author_ID, a.Author_Name, a.skills 
                    LIMIT 5
                """)
                sample_authors = [dict(record) for record in result2]
                
                result3 = session.run("""
                    MATCH (p:Paper) 
                    RETURN count(p) as total_papers, 
                           collect(p.Combined_Keywords)[0..3] as sample_keywords 
                    LIMIT 1
                """)
                paper_info = dict(result3.single())
                
                return {
                    "status": "success",
                    "total_authors": total_authors,
                    "sample_authors": sample_authors,
                    "paper_info": paper_info,
                    "connection": "OK"
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def __del__(self):
        """Cleanup on object destruction"""
        self.close()

    # ==================== WEB INTERFACE COMPATIBILITY METHODS ====================
    
    def form_teams(self, algorithm, keywords, team_size=5, num_teams=3, **kwargs):
        """Multiple teams formation method for web interface compatibility"""
        try:
            # Convert to list if needed
            if isinstance(keywords, str):
                keywords = [kw.strip() for kw in keywords.split(',') if kw.strip()]
            
            logger.info(f"=== TEAM FORMATION DEBUG START ===")
            logger.info(f"Algorithm: {algorithm}")
            logger.info(f"Keywords: {keywords}")
            logger.info(f"Requested teams: {num_teams}")
            
            # Debug: Test basic database connectivity with extended timeout
            try:
                # Use session with extended timeout for serverless mode
                with self.driver.session(
                    default_access_mode="READ",
                    fetch_size=1000,
                    connection_acquisition_timeout=120
                ) as session:
                    # Use much longer timeout for queries in serverless mode
                    test_result = session.run("MATCH (a:Author) RETURN count(a) as total_authors LIMIT 1", timeout=180)
                    author_record = test_result.single()
                    author_count = author_record["total_authors"] if author_record else 0
                    logger.info(f"Database connectivity test: Found {author_count} total authors")
                    
                    # Test keyword search
                    test_keyword_query = """
                    MATCH (a:Author)
                    WHERE (a.skills IS NOT NULL AND toLower(a.skills) CONTAINS toLower($keyword))
                    OR EXISTS {
                        MATCH (a)-[:WRITTEN]->(p:Paper)
                        WHERE toLower(p.Combined_Keywords) CONTAINS toLower($keyword)
                    }
                    RETURN a.Author_ID, a.Author_Name, a.skills
                    LIMIT 5
                    """
                    
                    test_result = session.run(test_keyword_query, keyword=keywords[0], timeout=180)
                    test_authors = list(test_result)
                    logger.info(f"Test search for '{keywords[0]}' found {len(test_authors)} authors")
                    for author in test_authors[:3]:
                        logger.info(f"  - {author['a.Author_Name']}: {author['a.skills']}")
                        
            except Exception as db_error:
                logger.error(f"Database connectivity issue: {db_error}")
                return {
                    "teams": [],
                    "algorithm": algorithm,
                    "message": f"Database connectivity error: {str(db_error)}",
                    "statistics": {"total_teams": 0, "total_members": 0, "keyword_coverage": 0}
                }
            
            # Use build_teams method
            # Extract parameters to avoid duplicate keyword arguments
            max_distance = kwargs.pop('max_distance', 3)
            initial_distance = kwargs.pop('initial_distance', 2) 
            max_increase = kwargs.pop('max_increase', 5)
            
            logger.info(f"Calling build_teams with max_distance={max_distance}, initial_distance={initial_distance}")
            
            successful_teams, teams_df = self.build_teams(
                keywords=keywords,
                algorithm=algorithm,
                limit=num_teams,
                max_distance=max_distance,
                initial_distance=initial_distance,
                max_increase=max_increase,
                **kwargs
            )
            
            logger.info(f"build_teams returned: successful_teams={successful_teams}, teams_df shape={teams_df.shape if not teams_df.empty else 'EMPTY'}")
            
            teams = []
            if successful_teams > 0 and not teams_df.empty:
                # Group by team
                if 'Team' in teams_df.columns:
                    grouped = teams_df.groupby('Team')
                    
                    for team_name, team_data in grouped:
                        members = []
                        team_skills = set()
                        team_status = "complete"
                        

                        
                        # Get enhanced details for all team members at once
                        team_member_ids = [str(row.get('Author ID', '')) for _, row in team_data.iterrows()]
                        
                        with self.driver.session() as session:
                            enhanced_details = session.execute_read(self.get_enhanced_member_details, team_member_ids)
                        
                        # Create a mapping of author_id to enhanced details
                        details_map = {detail['author_id']: detail for detail in enhanced_details}
                        
                        for _, row in team_data.iterrows():
                            author_id = str(row.get('Author ID', ''))
                            author_name = str(row.get('Author Name', 'Unknown Author'))
                            matching_skills = str(row.get('Matching Skills', ''))
                            added_for_skill = str(row.get('Added For Skill', 'Team Member'))
                            
                            # Get enhanced details from database
                            enhanced_detail = details_map.get(author_id, {})
                            
                            members.append({
                                "author_id": author_id,
                                "author_name": author_name,
                                "expertise": matching_skills,
                                "role": added_for_skill,
                                "added_for": added_for_skill,
                                "all_skills": enhanced_detail.get('skills', 'No skills data'),
                                "skills": enhanced_detail.get('skills', 'No skills data'),
                                "paper_count": enhanced_detail.get('paper_count', 0),
                                "organizations": enhanced_detail.get('organizations', []),
                                "total_citations": enhanced_detail.get('total_citations', 0)
                            })
                            
                            if matching_skills and matching_skills != 'nan':
                                skills = [s.strip() for s in matching_skills.split(',') if s.strip()]
                                team_skills.update(skills)
                            
                            if row.get('Status') == 'incomplete':
                                team_status = "incomplete"
                        
                        teams.append({
                            "team_number": len(teams) + 1,
                            "team_name": str(team_name),
                            "members": members,
                            "skills_covered": list(team_skills),
                            "requested_skills": keywords,
                            "completeness": 1.0 if team_status == "complete" else 0.7,
                            "algorithm": algorithm,
                            "status": team_status
                        })
            
            statistics = self._calculate_team_statistics(teams, keywords)
            
            return {
                "teams": teams,
                "algorithm": algorithm,
                "message": f"Successfully formed {len(teams)} teams using {self.config.algorithms[algorithm]['name']}",
                "statistics": statistics
            }
            
        except Exception as e:
            logger.error(f"Error in form_teams: {e}")
            return {
                "teams": [],
                "algorithm": algorithm,
                "message": f"Error forming teams: {str(e)}",
                "statistics": {"total_teams": 0, "total_members": 0, "keyword_coverage": 0}
            }

    def _calculate_team_statistics(self, teams, keywords):
        """Calculate overall statistics for all formed teams"""
        if not teams:
            return {
                "total_teams": 0,
                "total_members": 0,
                "keyword_coverage": 0,
                "avg_team_size": 0,
                "avg_completeness": 0
            }
        
        total_members = sum(len(team["members"]) for team in teams)
        total_completeness = sum(team["completeness"] for team in teams)
        
        return {
            "total_teams": len(teams),
            "total_members": total_members,
            "keyword_coverage": round((total_completeness / len(teams)) * 100, 1) if teams else 0,
            "avg_team_size": round(total_members / len(teams), 2) if teams else 0,
            "avg_completeness": round(total_completeness / len(teams), 2) if teams else 0
        }