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

    fetch('/api/form-teams', {
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

function displayResults(data) {
    const resultsDiv = document.getElementById('results');
    
    // Extract teams and summary from response
    const teams = data.teams || data.result || data;
    const summary = data.summary || {};
    
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
    
    // Calculate statistics
    const totalTeams = teams.length;
    const completeTeams = teams.filter(t => (t.completeness || 1) >= 1.0).length;
    const incompleteTeams = totalTeams - completeTeams;
    const avgTeamSize = teams.reduce((sum, t) => sum + (t.members || []).length, 0) / totalTeams;
    const avgCompleteness = teams.reduce((sum, t) => sum + (t.completeness || 1), 0) / totalTeams * 100;
    
    // Create formatted output like the original
    let html = `
        <div class="formatted-results">
            <h2>✅ Team Formation Results</h2>
            <p><strong>Successfully formed ${totalTeams} teams</strong></p>
            
            <h4>📊 Summary</h4>
            <p><strong>Keywords:</strong> ${summary.keywords_requested ? summary.keywords_requested.join(', ') : 'N/A'}</p>
            <p><strong>Algorithm:</strong> ${summary.algorithm_name || 'Team Formation Algorithm'}</p>
            <p><strong>Success Rate:</strong> ${completeTeams}/${totalTeams}</p>
            <p><strong>Average Team Size:</strong> ${avgTeamSize.toFixed(1)}</p>
            <p><strong>Average Completeness:</strong> ${avgCompleteness.toFixed(0)}%</p>
            <p><strong>Complete Teams:</strong> ${completeTeams}</p>
            <p><strong>Incomplete Teams:</strong> ${incompleteTeams}</p>
            <br>
    `;
    
    // Display each team in detailed format
    teams.forEach((team, index) => {
        const teamNumber = team.team_number || index + 1;
        const members = team.members || [];
        const completeness = team.completeness || 1;
        const skillsCovered = team.skills_covered || [];
        const requestedSkills = team.requested_skills || summary.keywords_requested || [];
        
        const isComplete = completeness >= 1.0;
        const emoji = isComplete ? '✅' : '⚠️';
        const status = isComplete ? 'Complete (100%)' : `Incomplete (${Math.round(completeness * 100)}%)`;
        const coverage = `${skillsCovered.length}/${requestedSkills.length}`;
        
        html += `
            <div class="team-section" style="margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <h4>${emoji} Team ${teamNumber}</h4>
                <p><strong>${status} Coverage: ${coverage}</strong></p>
                <br>
                <p><strong>Keywords Found:</strong> ${skillsCovered.join(', ')}</p>
        `;
        
        if (!isComplete) {
            const missingSkills = requestedSkills.filter(skill => !skillsCovered.includes(skill));
            html += `<p><strong>Missing Keywords:</strong> ${missingSkills.join(', ')}</p>`;
        }
        
        html += `
                <p><strong>Skills Covered:</strong> ${skillsCovered.join(', ')}</p>
                <h5>👥 Team Members (${members.length})</h5>
        `;
        
        members.forEach(member => {
            const name = member.author_name || member.name || 'Unknown';
            const id = member.author_id || member.id || '';
            const expertise = member.expertise || 'General';
            const addedFor = member.role || 'Member';
            
            html += `
                <div style="margin-left: 20px; margin-bottom: 15px;">
                    <p><strong>👤 ${name}</strong></p>
                    ${id ? `<p>ID: ${id}</p>` : ''}
                    <p><strong>Added For:</strong> ${addedFor}</p>
                    <p><strong>Expertise:</strong> ${expertise}</p>
                </div>
            `;
        });
        
        html += '</div>';
    });
    
    // Add Google Forms integration
    html += `
        <div style="margin-top: 30px; padding: 20px; background-color: #f8f9fa; border-radius: 8px;">
            <h4>📝 Help Us Improve - Evaluate This Team Formation</h4>
            <p>Your feedback is valuable for our scientific research. Please take 2-3 minutes to evaluate the team formation results.</p>
            <p><a href="https://forms.google.com/your-form-link" target="_blank" class="btn btn-primary">Provide Feedback</a></p>
        </div>
    `;
    
    html += '</div>';
    resultsDiv.innerHTML = html;
}

function displayError(message) {
    document.getElementById('results').innerHTML = 
        `<div class="alert alert-danger">Error: ${message}</div>`;
}