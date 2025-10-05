@echo off
echo Setting Heroku configuration variables...
heroku config:set NEO4J_URI=neo4j+s://cc773764.databases.neo4j.io -a team-formation-app-new-05
heroku config:set NEO4J_USER=neo4j -a team-formation-app-new-05
heroku config:set NEO4J_PASSWORD=z2rSb4ew9gxVlqlrFk8l_VZQcVhIzBwgnlder4nKv1A -a team-formation-app-new-05
echo Configuration complete!
heroku config -a team-formation-app-new-05