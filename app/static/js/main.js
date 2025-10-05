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
    
    // Store globally for Google Forms integration
    window.currentTeamResults = teams;
    
    // Fix: Ensure teams is always an array
    if (!teams) {
        resultsDiv.innerHTML = '<div class="alert alert-warning">No teams could be formed with the given criteria.</div>';
        return;
    }
    
    // Convert single team object to array if needed
    if (!Array.isArray(teams)) {
        teams = [teams];  // Wrap single team in array
        window.currentTeamResults = teams;
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
    
        // Display each team in enhanced detailed format
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
                <div class="card team-card shadow-sm" style="margin-bottom: 30px;">
                    <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
                        <h5 class="mb-0">${emoji} Team ${teamNumber}</h5>
                        <span class="badge bg-light text-dark">${status}</span>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-lg-8">
                                <h6><i class="fas fa-user-friends"></i> Team Members (${members.length})</h6>
                                <div class="row">
            `;
            
            // Member display with database-calculated values
            members.forEach(member => {
                const name = member.author_name || member.name || 'Unknown';
                const id = member.author_id || member.id || '';
                const addedFor = member.role || member.added_for || 'Team Member';
                const allSkills = member.all_skills || member.skills || 'No skills data available';
                const paperCount = member.paper_count || 0;
                const organizations = member.organizations || [];
                const totalCitations = member.total_citations || 0;
                
                html += `
                    <div class="col-md-6 mb-3">
                        <div class="card h-100 border-left-primary">
                            <div class="card-body p-3">
                                <h6 class="text-primary mb-2">
                                    <i class="fas fa-user"></i> ${name}
                                </h6>
                                
                                <div class="mb-2">
                                    <strong>Added For:</strong>
                                    <span class="badge bg-info">${addedFor}</span>
                                </div>
                                
                                <div class="mb-2">
                                    <strong>Skills:</strong>
                                    <div class="mt-1">
                `;
                
                // Display skills as badges
                if (allSkills && allSkills !== 'No skills data available') {
                    const skillsArray = allSkills.split(',').map(s => s.trim()).filter(s => s);
                    skillsArray.slice(0, 5).forEach(skill => { // Show max 5 skills
                        html += `<span class="badge bg-light text-dark me-1 mb-1">${skill}</span>`;
                    });
                    if (skillsArray.length > 5) {
                        html += `<span class="badge bg-secondary">+${skillsArray.length - 5} more</span>`;
                    }
                } else {
                    html += `<span class="text-muted">No skills data</span>`;
                }
                
                html += `
                                    </div>
                                </div>
                                
                                <div class="mb-2">
                                    <strong>Number of Papers:</strong>
                                    <span class="badge bg-secondary">${paperCount}</span>
                                </div>
                `;
                
                // Display organizations
                if (organizations && organizations.length > 0) {
                    html += `
                        <div class="mb-2">
                            <strong>Organizations:</strong>
                            <div class="mt-1">
                    `;
                    organizations.slice(0, 3).forEach(org => { // Show max 3 organizations
                        if (org && org.trim()) {
                            html += `<span class="badge bg-success me-1 mb-1">${org.trim()}</span>`;
                        }
                    });
                    if (organizations.length > 3) {
                        html += `<span class="badge bg-secondary">+${organizations.length - 3} more</span>`;
                    }
                    html += `</div></div>`;
                } else {
                    html += `
                        <div class="mb-2">
                            <strong>Organizations:</strong>
                            <span class="text-muted">No organization data</span>
                        </div>
                    `;
                }
                
                html += `
                                <div class="mb-1">
                                    <strong>Total Citations:</strong>
                                    <span class="badge bg-warning">${totalCitations}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            html += `
                                </div>
                            </div>
                            
                            <div class="col-lg-4">
                                <h6><i class="fas fa-chart-pie"></i> Team Statistics</h6>
                                
                                <div class="card mb-3">
                                    <div class="card-body p-3">
                                        <h6 class="card-title">Skills Coverage</h6>
            `;
            
            if (skillsCovered.length > 0) {
                skillsCovered.forEach(skill => {
                    html += `<span class="badge bg-success me-1 mb-1">${skill}</span>`;
                });
            } else {
                html += `<small class="text-muted">No skills covered information</small>`;
            }
            
            html += `
                                    </div>
                                </div>
                                
                                <div class="card mb-3">
                                    <div class="card-body p-3">
                                        <h6 class="card-title">Requested Skills</h6>
            `;
            
            if (requestedSkills.length > 0) {
                requestedSkills.forEach(skill => {
                    html += `<span class="badge bg-primary me-1 mb-1">${skill}</span>`;
                });
            }
            
            // Calculate team metrics
            const totalPapers = members.reduce((sum, m) => sum + (m.paper_count || 0), 0);
            const totalTeamCitations = members.reduce((sum, m) => sum + (m.total_citations || 0), 0);
            
            html += `
                                    </div>
                                </div>
                                
                                <div class="card">
                                    <div class="card-body p-3">
                                        <h6 class="card-title">Team Metrics</h6>
                                        <div class="row text-center">
                                            <div class="col-6">
                                                <h5 class="text-info">${members.length}</h5>
                                                <small>Members</small>
                                            </div>
                                            <div class="col-6">
                                                <h5 class="text-success">${totalPapers}</h5>
                                                <small>Total Papers</small>
                                            </div>
                                        </div>
                                        <div class="row text-center mt-2">
                                            <div class="col-12">
                                                <h5 class="text-warning">${totalTeamCitations}</h5>
                                                <small>Total Citations</small>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });    // Add Google Forms integration with your actual survey
    html += `
        <div style="margin-top: 30px; padding: 20px; background: linear-gradient(135deg, #f0fff4 0%, #f8fff9 100%); border: 2px solid #28a745; border-radius: 10px;">
            <div class="text-center">
                <h4 style="color: #28a745; margin-bottom: 15px;">
                    <i class="fas fa-chart-line"></i> Help Us Improve - Evaluate This Team Formation
                </h4>
                <p style="margin-bottom: 20px; color: #155724;">
                    <strong>Your feedback is valuable for our scientific research.</strong><br>
                    Please take 2-3 minutes to evaluate the team formation results.
                </p>
                
                <div class="row justify-content-center">
                    <div class="col-md-8">
                        <button onclick="openFeedbackForm()" class="btn btn-success btn-lg me-3" style="min-width: 180px;">
                            <i class="fas fa-clipboard-list"></i> Provide Feedback
                        </button>
                        <button onclick="copyTeamResults()" class="btn btn-outline-primary">
                            <i class="fas fa-copy"></i> Copy Results
                        </button>
                    </div>
                </div>
                
                <!-- Embedded form option -->
                <div class="mt-3">
                    <small class="text-muted">
                        Prefer embedded form? 
                        <a href="#" onclick="showEmbeddedForm(); return false;" style="color: #28a745;">
                            Click here to open form below
                        </a>
                    </small>
                </div>
                
                <!-- Embedded form container (initially hidden) -->
                <div id="embeddedFormContainer" style="display: none; margin-top: 20px;">
                    <hr>
                    <iframe src="https://docs.google.com/forms/d/e/1FAIpQLSfjqhqiC3mDT3UU2R5oupe08Kr5ESuNTseKPQbEbwjPMumnRw/viewform?embedded=true" 
                            width="100%" height="600" frameborder="0" marginheight="0" marginwidth="0">
                        Loading feedback form...
                    </iframe>
                </div>
            </div>
        </div>
    `;
    
    html += '</div>';
    resultsDiv.innerHTML = html;
}

function displayError(message) {
    document.getElementById('results').innerHTML = 
        `<div class="alert alert-danger">Error: ${message}</div>`;
}

// Google Forms Integration Functions
function openFeedbackForm() {
    const teamsData = getCurrentTeamResults();
    
    if (!teamsData || teamsData.length === 0) {
        alert('No team formation results available. Please form teams first.');
        return;
    }
    
    // Get feedback form URL from configuration
    const feedbackFormUrl = CONFIG?.FEEDBACK_FORM_URL || 'https://forms.gle/your-survey-link';
    
    // Optional: Add team formation context as URL parameters if your form supports it
    const urlParams = new URLSearchParams();
    urlParams.append('teams_count', teamsData.length);
    urlParams.append('algorithm', teamsData[0]?.algorithm || 'unknown');
    urlParams.append('timestamp', new Date().toISOString());
    
    const finalUrl = `${feedbackFormUrl}?${urlParams.toString()}`;
    
    // Open the feedback form in a new tab
    window.open(finalUrl, '_blank');
    
    // Show a thank you message
    setTimeout(() => {
        showNotification('Thank you for providing feedback! Your input helps us improve our team formation algorithms.', 'success');
    }, 1000);
}

function openEmbeddedFeedback() {
    const teamsData = getCurrentTeamResults();
    
    if (!teamsData || teamsData.length === 0) {
        alert('No team formation results available. Please form teams first.');
        return false;
    }
    
    // Optionally add team data to iframe URL parameters
    const iframe = document.getElementById('feedbackIframe');
    const baseUrl = CONFIG?.FEEDBACK_FORM_URL || 'https://docs.google.com/forms/d/e/1FAIpQLSfjqhqiC3mDT3UU2R5oupe08Kr5ESuNTseKPQbEbwjPMumnRw/viewform';
    
    // Add context parameters if supported by your form
    const urlParams = new URLSearchParams();
    urlParams.append('teams_count', teamsData.length);
    urlParams.append('algorithm', teamsData[0]?.algorithm || 'unknown');
    urlParams.append('embedded', 'true');
    
    const embeddedUrl = `${baseUrl}?embedded=true&${urlParams.toString()}`;
    iframe.src = embeddedUrl;
    
    return true;
}

function exportToGoogleForms() {
    // This is the old function, now redirecting to the main feedback form
    openFeedbackForm();
}

function generateTeamEvaluationForm() {
    const teamsData = getCurrentTeamResults();
    
    if (!teamsData || teamsData.length === 0) {
        alert('No team formation results available. Please form teams first.');
        return;
    }
    
    // Use your actual Google Forms survey URL
    // You can add team data as URL parameters if your form supports pre-filling
    const evaluationUrl = 'https://forms.gle/your-actual-form-id'; // Replace with your actual form URL
    
    window.open(evaluationUrl, '_blank');
    
    // Optional: Show success message
    setTimeout(() => {
        alert('Thank you for providing feedback! Your input helps improve our team formation algorithms.');
    }, 1000);
}

function generateGoogleFormLink() {
    const title = document.getElementById('googleFormTitle')?.value || 'Team Formation Results';
    const description = document.getElementById('googleFormDescription')?.value || 'Team formation results for evaluation.';
    const teamsData = getCurrentTeamResults();
    
    if (!teamsData) {
        alert('No team formation results available.');
        return;
    }
    
    const formUrl = generateGoogleFormUrl(title, description, teamsData);
    displayGeneratedLink(formUrl);
}

function generateGoogleFormUrl(title, description, teamsData) {
    const baseUrl = 'https://docs.google.com/forms/d/e/create';
    const params = new URLSearchParams();
    
    // Add form title and description
    params.append('title', title);
    params.append('description', description);
    
    // Add team data as pre-filled content
    teamsData.forEach((team, index) => {
        params.append(`team_${index + 1}_name`, team.team_name || `Team ${index + 1}`);
        params.append(`team_${index + 1}_members`, team.members.map(m => m.author_name).join(', '));
        params.append(`team_${index + 1}_skills`, (team.skills_covered || []).join(', '));
        params.append(`team_${index + 1}_status`, team.status || 'unknown');
    });
    
    return `${baseUrl}?${params.toString()}`;
}

function copyTeamResults() {
    const teamsData = getCurrentTeamResults();
    
    if (!teamsData || teamsData.length === 0) {
        alert('No team formation results available to copy.');
        return;
    }
    
    // Format team results as text
    let resultText = `Team Formation Results\n`;
    resultText += `Generated on: ${new Date().toLocaleString()}\n\n`;
    
    teamsData.forEach((team, index) => {
        resultText += `=== ${team.team_name || 'Team ' + (index + 1)} ===\n`;
        resultText += `Status: ${team.status || 'Unknown'}\n`;
        resultText += `Algorithm: ${team.algorithm || 'N/A'}\n`;
        resultText += `Skills Covered: ${(team.skills_covered || []).join(', ')}\n`;
        resultText += `Members (${team.members ? team.members.length : 0}):\n`;
        
        if (team.members) {
            team.members.forEach((member, memberIndex) => {
                resultText += `  ${memberIndex + 1}. ${member.author_name}\n`;
                resultText += `     Added For: ${member.added_for || member.role || 'N/A'}\n`;
                resultText += `     Skills: ${member.all_skills || 'N/A'}\n`;
                resultText += `     Papers: ${member.paper_count || 0}\n`;
                resultText += `     Organizations: ${(member.organizations || []).join(', ') || 'N/A'}\n`;
                resultText += `     Citations: ${member.total_citations || 0}\n\n`;
            });
        }
        resultText += `\n`;
    });
    
    // Copy to clipboard
    navigator.clipboard.writeText(resultText).then(() => {
        alert('Team results copied to clipboard!');
    }).catch(err => {
        console.error('Failed to copy text: ', err);
        alert('Failed to copy to clipboard. Please try again.');
    });
}

function copyGeneratedLink() {
    const linkInput = document.getElementById('generatedLink');
    linkInput.select();
    linkInput.setSelectionRange(0, 99999); // For mobile devices
    
    navigator.clipboard.writeText(linkInput.value).then(() => {
        alert('Google Form link copied to clipboard!');
    }).catch(err => {
        console.error('Failed to copy link: ', err);
        alert('Failed to copy link. Please manually copy from the text field.');
    });
}

function displayGeneratedLink(url) {
    const container = document.getElementById('generatedLinkContainer');
    const linkInput = document.getElementById('generatedLink');
    
    if (container && linkInput) {
        linkInput.value = url;
        container.style.display = 'block';
    }
}

function getCurrentTeamResults() {
    // This function should return the current team formation results
    // For now, we'll try to extract from the results div or from a global variable
    
    // Try to get from global variable if set
    if (window.currentTeamResults) {
        return window.currentTeamResults;
    }
    
    // Try to extract from the displayed results (simplified)
    const resultsDiv = document.getElementById('results');
    if (!resultsDiv || !resultsDiv.innerHTML.trim()) {
        return null;
    }
    
    // Return mock data structure for demonstration
    return [
        {
            team_name: 'Sample Team 1',
            team_number: 1,
            status: 'complete',
            algorithm: 'ACET',
            skills_covered: ['machine learning', 'data mining'],
            requested_skills: ['machine learning', 'data mining', 'optimization'],
            members: [
                {
                    author_name: 'Sample Author 1',
                    added_for: 'machine learning',
                    all_skills: 'machine learning, neural networks, deep learning',
                    paper_count: 15,
                    organizations: ['University A', 'Research Lab B'],
                    total_citations: 250
                }
            ]
        }
    ];
}

// Additional utility functions
function exportTeamSummary() {
    const teamsData = getCurrentTeamResults();
    
    if (!teamsData || teamsData.length === 0) {
        alert('No team formation results available to export.');
        return;
    }
    
    // Generate CSV format summary
    let csvContent = "Team,Algorithm,Status,Members Count,Skills Covered,Total Papers,Total Citations\n";
    
    teamsData.forEach((team, index) => {
        const memberCount = team.members ? team.members.length : 0;
        const skillsCovered = (team.skills_covered || []).join('; ');
        const totalPapers = team.members ? team.members.reduce((sum, m) => sum + (m.paper_count || 0), 0) : 0;
        const totalCitations = team.members ? team.members.reduce((sum, m) => sum + (m.total_citations || 0), 0) : 0;
        
        csvContent += `"${team.team_name || 'Team ' + (index + 1)}","${team.algorithm}","${team.status}",${memberCount},"${skillsCovered}",${totalPapers},${totalCitations}\n`;
    });
    
    // Download CSV
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `team_formation_summary_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showNotification('Team summary exported successfully!', 'success');
}

function shareResults() {
    const teamsData = getCurrentTeamResults();
    
    if (!teamsData || teamsData.length === 0) {
        alert('No team formation results available to share.');
        return;
    }
    
    // Generate shareable text
    const shareText = `Team Formation Results:\n${teamsData.length} teams formed using ${teamsData[0]?.algorithm || 'advanced'} algorithm.\n\nView details at: ${window.location.href}`;
    
    if (navigator.share) {
        // Use Web Share API if available
        navigator.share({
            title: 'Team Formation Results',
            text: shareText,
            url: window.location.href
        });
    } else {
        // Fallback: copy to clipboard
        navigator.clipboard.writeText(shareText).then(() => {
            showNotification('Results link copied to clipboard!', 'info');
        }).catch(() => {
            alert('Share link: ' + window.location.href);
        });
    }
}

function downloadPDF() {
    const teamsData = getCurrentTeamResults();
    
    if (!teamsData || teamsData.length === 0) {
        alert('No team formation results available to download.');
        return;
    }
    
    // For now, just show a placeholder message
    // You would implement actual PDF generation here using libraries like jsPDF
    showNotification('PDF download feature will be implemented soon. Use "Copy Results" for now.', 'info');
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.minWidth = '300px';
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

function showEmbeddedForm() {
    const container = document.getElementById('embeddedFormContainer');
    if (container) {
        container.style.display = container.style.display === 'none' ? 'block' : 'none';
        
        // Scroll to the form if showing it
        if (container.style.display === 'block') {
            setTimeout(() => {
                container.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 300);
        }
    }
}