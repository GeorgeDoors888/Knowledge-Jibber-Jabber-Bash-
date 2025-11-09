// ChatGPT Extension Integration
const DRIVE_API_URL = 'http://localhost:5000';

// Function to inject into ChatGPT's interface
async function injectDriveSearch() {
    // Create the search button
    const button = document.createElement('button');
    button.innerHTML = '🔍 Search Drive';
    button.style.marginRight = '10px';
    
    // Create the search interface
    const searchDiv = document.createElement('div');
    searchDiv.style.display = 'none';
    searchDiv.innerHTML = `
        <div style="margin: 10px 0;">
            <input type="text" id="drive-search" placeholder="Search Google Drive...">
            <button id="execute-search">Search</button>
            <select id="sort-by">
                <option value="relevance">Relevance</option>
                <option value="modified">Last Modified</option>
                <option value="created">Created Date</option>
                <option value="name">Name</option>
            </select>
        </div>
    `;
    
    // Add to ChatGPT's interface
    const targetElement = document.querySelector('form').parentElement;
    targetElement.insertBefore(button, targetElement.firstChild);
    targetElement.insertBefore(searchDiv, targetElement.firstChild);
    
    // Handle click events
    button.onclick = () => searchDiv.style.display = searchDiv.style.display === 'none' ? 'block' : 'none';
    
    document.getElementById('execute-search').onclick = async () => {
        const query = document.getElementById('drive-search').value;
        const sortBy = document.getElementById('sort-by').value;
        
        try {
            const response = await fetch(`${DRIVE_API_URL}/search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query,
                    sort_by: sortBy,
                    max_results: 10,
                    include_content: true
                })
            });
            
            const data = await response.json();
            
            // Insert the GPT prompt into ChatGPT's textarea
            const textarea = document.querySelector('textarea');
            textarea.value = data.gpt_prompt;
            textarea.dispatchEvent(new Event('input', { bubbles: true }));
            
            // Hide the search interface
            searchDiv.style.display = 'none';
            
        } catch (error) {
            console.error('Error searching Drive:', error);
            alert('Error searching Google Drive. Please check the console for details.');
        }
    };
}

// Initialize when the page loads
if (document.readyState === 'complete') {
    injectDriveSearch();
} else {
    window.addEventListener('load', injectDriveSearch);
}