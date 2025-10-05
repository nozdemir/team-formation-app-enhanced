// Async team formation function to bypass Heroku 30s timeout
async function formTeamsAsync() {
    // Record start time for performance tracking
    window.teamFormationStartTime = Date.now();

    if (selectedKeywords.length === 0) {
        showStatus('Please select at least one keyword.', 'error');
        return;
    }

    const algorithm = document.getElementById('algorithm').value;
    const numTeams = parseInt(document.getElementById('numTeams').value);
    
    if (!algorithm) {
        showStatus('Please select an algorithm.', 'error');
        return;
    }
    
    // Show loading state
    const submitBtn = document.getElementById('submitBtn');
    const resultsDiv = document.getElementById('results');
    
    submitBtn.disabled = true;
    submitBtn.textContent = '🔄 Starting Team Formation...';
    
    // Show loading in results area with real-time counter
    resultsDiv.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <h3 style="color: #2a5298; margin-bottom: 15px;">🔄 Forming Teams...</h3>
            <p style="font-size: 16px; margin-bottom: 10px;">Algorithm: <strong>${algorithm.replace('_', ' ')}</strong></p>
            <p style="font-size: 14px; margin-bottom: 20px;">Keywords: <strong>${selectedKeywords.join(', ')}</strong></p>
            
            <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 15px; border-radius: 10px; margin: 20px 0;">
                <div style="font-size: 24px; font-weight: bold; margin-bottom: 5px;">
                    ⏱️ <span id="elapsedTimer">0</span> seconds
                </div>
                <div style="font-size: 12px; opacity: 0.9;">
                    Processing time (serverless mode may take up to 15 minutes)
                </div>
                <div style="width: 100%; background-color: rgba(255,255,255,0.3); border-radius: 10px; height: 8px; margin-top: 10px; overflow: hidden;">
                    <div id="progressBar" style="width: 0%; background-color: #90ee90; height: 100%; border-radius: 10px; transition: width 0.3s ease;"></div>
                </div>
            </div>
            
            <p style="font-size: 12px; color: #666; margin-top: 15px;">
                <i class="fas fa-info-circle"></i> Please wait... Now using async processing to handle long operations
            </p>
        </div>
    `;
    resultsDiv.style.display = 'block';
    
    // Start the elapsed time counter
    let elapsedSeconds = 0;
    const timerElement = document.getElementById('elapsedTimer');
    const progressBar = document.getElementById('progressBar');
    const maxExpectedTime = 900; // 15 minutes max expected time
    
    const timerInterval = setInterval(() => {
        elapsedSeconds++;
        if (timerElement) {
            timerElement.textContent = elapsedSeconds;
        }
        if (progressBar && elapsedSeconds <= maxExpectedTime) {
            // Progress bar fills up over 15 minutes
            const progressPercent = Math.min((elapsedSeconds / maxExpectedTime) * 100, 95);
            progressBar.style.width = progressPercent + '%';
            
            // Change color as time progresses
            if (elapsedSeconds < 60) {
                progressBar.style.backgroundColor = '#90ee90'; // Green for first minute
            } else if (elapsedSeconds < 300) {
                progressBar.style.backgroundColor = '#ffd700'; // Yellow for 1-5 minutes
            } else {
                progressBar.style.backgroundColor = '#ffb6c1'; // Light red for 5+ minutes
            }
        }
    }, 1000);
    
    // Store the interval ID to clear it later
    window.currentTimerInterval = timerInterval;

    try {
        console.log('Starting async team formation:', {
            algorithm: algorithm,
            keywords: selectedKeywords,
            num_teams: numTeams
        });

        // Start async team formation
        const startResponse = await fetch('/api/form-teams-async', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                algorithm: algorithm,
                keywords: selectedKeywords,
                num_teams: numTeams
            })
        });
        
        if (!startResponse.ok) {
            throw new Error(`Failed to start team formation: ${startResponse.status}`);
        }
        
        const startData = await startResponse.json();
        if (!startData.success) {
            throw new Error(startData.error || 'Failed to start team formation');
        }
        
        const taskId = startData.task_id;
        console.log('Team formation task started:', taskId);
        
        submitBtn.textContent = '🔄 Processing in Background...';
        
        // Poll for results
        let pollCount = 0;
        const maxPolls = 180; // 15 minutes max (5-second intervals)
        
        const pollForResults = async () => {
            try {
                const statusResponse = await fetch(`/api/task-status/${taskId}`);
                if (!statusResponse.ok) {
                    throw new Error(`Failed to get task status: ${statusResponse.status}`);
                }
                
                const statusData = await statusResponse.json();
                if (!statusData.success) {
                    throw new Error(statusData.error || 'Failed to get task status');
                }
                
                const status = statusData.task_status;
                console.log('Task status:', status);
                
                // Update progress indicators
                if (timerElement && status.elapsed_seconds !== undefined) {
                    elapsedSeconds = status.elapsed_seconds;
                    timerElement.textContent = elapsedSeconds;
                }
                if (progressBar && status.progress !== undefined) {
                    const progressPercent = Math.min(status.progress, 95);
                    progressBar.style.width = progressPercent + '%';
                }
                
                // Update status message
                const loadingDiv = document.querySelector('.loading h3');
                if (loadingDiv) {
                    loadingDiv.innerHTML = `🔄 ${status.message || 'Processing...'}`;
                }
                
                if (status.status === 'completed') {
                    // Clear the timer
                    if (window.currentTimerInterval) {
                        clearInterval(window.currentTimerInterval);
                        window.currentTimerInterval = null;
                    }
                    
                    // Process results
                    const result = status.result;
                    window.lastUsedKeywords = [...selectedKeywords];
                    displayResults(result);
                    showStatus('Teams formed successfully!', 'success');
                    
                    // Reset button
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Form Teams 🚀';
                    return; // Stop polling
                    
                } else if (status.status === 'failed') {
                    throw new Error(status.error || 'Team formation failed');
                    
                } else {
                    // Continue polling
                    pollCount++;
                    if (pollCount < maxPolls) {
                        setTimeout(pollForResults, 5000); // Poll every 5 seconds
                    } else {
                        throw new Error('Team formation timed out after 15 minutes');
                    }
                }
                
            } catch (pollError) {
                console.error('Polling error:', pollError);
                throw pollError;
            }
        };
        
        // Start polling after a short delay
        setTimeout(pollForResults, 2000);
        
    } catch (error) {
        console.error('Error details:', error);
        
        let errorMessage = 'An unexpected error occurred.';
        let suggestions = [];
        
        if (error.message.includes('Failed to start team formation')) {
            errorMessage = 'Failed to start team formation process.';
            suggestions = [
                'Check your internet connection',
                'Verify all form fields are filled correctly',
                'Try refreshing the page and try again'
            ];
        } else if (error.message.includes('timed out after')) {
            errorMessage = 'Team formation process timed out after 15 minutes.';
            suggestions = [
                'Try using fewer keywords (3-5 recommended)',
                'Try requesting fewer teams',
                'Use a simpler algorithm like CAT or ACET',
                'The database may need optimization - contact support'
            ];
        } else {
            errorMessage = error.message;
            suggestions = [
                'Try refreshing the page',
                'Try using fewer parameters',
                'Contact support if the problem persists'
            ];
        }
        
        showStatus(`❌ Team formation failed: ${errorMessage}`, 'error');
        
        // Show error in results area
        const suggestionsList = suggestions.map(s => `<li>${s}</li>`).join('');
        resultsDiv.innerHTML = `
            <div style="background-color: #f8d7da; color: #721c24; padding: 20px; border-radius: 5px; border: 1px solid #f5c6cb;">
                <h3>❌ Error Details</h3>
                <p><strong>Error:</strong> ${errorMessage}</p>
                <p><strong>Parameters Used:</strong></p>
                <ul>
                    <li>Algorithm: ${algorithm}</li>
                    <li>Keywords: ${selectedKeywords.join(', ')}</li>
                    <li>Number of Teams: ${numTeams}</li>
                    <li>Request Duration: ${elapsedSeconds}s</li>
                </ul>
                <p><strong>Recommended Solutions:</strong></p>
                <ul>${suggestionsList}</ul>
                <div style="margin-top: 15px; padding: 10px; background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; color: #856404;">
                    <strong>💡 Tip:</strong> We've implemented async processing to handle long operations. 
                    This should resolve timeout issues.
                </div>
            </div>
        `;
        
        // Clear timer if still running
        if (window.currentTimerInterval) {
            clearInterval(window.currentTimerInterval);
            window.currentTimerInterval = null;
        }
        
        // Reset button state
        submitBtn.disabled = false;
        submitBtn.textContent = 'Form Teams 🚀';
    }
}