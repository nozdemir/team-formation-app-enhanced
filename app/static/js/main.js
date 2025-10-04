// This file contains the JavaScript code for the application, handling client-side interactions and dynamic content.

function formTeams() {
    const algorithm = document.getElementById('algorithm').value;
    const keywords = document.getElementById('keywords').value;
    const teamSize = document.getElementById('team_size').value || 5;
    const numTeams = document.getElementById('num_teams').value || 3;

    if (!keywords.trim()) {
        alert('Please enter keywords');
        return;
    }

    fetch('/form_team', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            algorithm: algorithm,
            keywords: keywords,
            team_size: parseInt(teamSize),
            num_teams: parseInt(numTeams)
        })
    })
    .then(response => {
        console.log('Response status:', response.status);
        console.log('Response headers:', response.headers);
        
        // Check if response is actually JSON
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            // If it's not JSON, get the text to see what error page was returned
            return response.text().then(text => {
                console.error('Non-JSON response received:', text);
                throw new Error('Server returned HTML instead of JSON. Check server logs for Python errors.');
            });
        }
        
        return response.json();
    })
    .then(data => {
        console.log('Response data:', data);
        if (data.success) {
            displayResults(data.result);
        } else {
            displayError(data.error || 'Unknown error occurred');
        }
    })
    .catch(error => {
        console.error('Network error:', error);
        displayError('Network error: ' + error.message);
    });
}

function displayResults(teams) {
    const resultsDiv = document.getElementById('results');
    
    // Fix: Ensure teams is always an array
    if (!teams) {
        resultsDiv.innerHTML = '<div class="alert alert-warning">No teams could be formed with the given criteria.</div>';
        return;
    }
    
    // Convert single team object to array if needed
    if (!Array.isArray(teams)) {
        teams = [teams];  // Wrap single team in array
    }
    
    if (teams.length === 0) {
        resultsDiv.innerHTML = '<div class="alert alert-warning">No teams could be formed with the given criteria.</div>';
        return;
    }
    
    let html = `<h3>🎉 Successfully formed ${teams.length} team${teams.length > 1 ? 's' : ''}!</h3>`;
    
    teams.forEach((team, index) => {
        // Ensure team has the expected structure
        const teamNumber = team.team_number || index + 1;
        const members = team.members || [];
        const completeness = team.completeness || 1;
        const skillsCovered = team.skills_covered || [];
        
        html += `
            <div class="card mt-3">
                <div class="card-header">
                    <h5>Team ${teamNumber}
                        <span class="badge badge-success">${Math.round(completeness * 100)}% Complete</span>
                    </h5>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-8">
                            <h6>Team Members (${members.length}):</h6>
                            <ul class="list-group">
        `;
        
        members.forEach(member => {
            html += `
                <li class="list-group-item d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${member.name || member.author_name || 'Unknown'}</strong>
                        <br><small class="text-muted">${member.role || 'Team Member'}</small>
                    </div>
                    <span class="badge badge-primary badge-pill">${member.expertise || 'General'}</span>
                </li>
            `;
        });
        
        html += `
                            </ul>
                        </div>
                        <div class="col-md-4">
                            <h6>Skills Covered:</h6>
                            <div>
        `;
        
        skillsCovered.forEach(skill => {
            html += `<span class="badge badge-success mr-1 mb-1">${skill}</span>`;
        });
        
        html += `
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    resultsDiv.innerHTML = html;
}

function displayError(message) {
    document.getElementById('results').innerHTML = 
        `<div class="alert alert-danger">Error: ${message}</div>`;
}