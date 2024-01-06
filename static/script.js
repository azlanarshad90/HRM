function submitJobDetails() {
    // Get values from input fields
    var title = document.getElementById("title").value;
    var salary = document.getElementById("salary").value;
    var experience = document.getElementById("experience").value;
    var skills = document.getElementById("skills").value;
    var location = document.getElementById("location").value;
    var jobType = document.getElementById("jobType").value;

    // Send data to the backend API
    fetch('/get-jd', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            Title: title,
            Salary_Range: salary,
            Required_Experience: experience,
            Required_Skills: skills,
            Location: location,
            Job_Type: jobType,
            userInput: '',
            approved_jd: false,
        }),
    })
    .then(response => response.json())
    .then(data => {
        // Display AI agent response in the textarea
        document.getElementById("agentResponse").value = data.response;
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function submitUserQuery() {
    // Get user query from input field
    var userQuery = document.getElementById("userQuery").value;

    // Send user query to the backend API
    fetch('/get-jd', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            userInput: userQuery,
            approved_jd: false,
        }),
    })
    .then(response => response.json())
    .then(data => {
        // Display AI agent response in the textarea
        document.getElementById("agentResponse").value = data.response;
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function saveAndProceed() {
    // Save current response in session and proceed to the next API
    fetch('/get-jd', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            userInput: '',
            approved_jd: true,
        }),
    })
    .then(response => response.json())
    .then(data => {
        // Display AI agent response in the textarea
        document.getElementById("agentResponse").value = data.response;
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function approveScreeningQuestions() {
    // Approve screening questions and proceed to the next API
    fetch('/get-screening-questions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            userInput: '',
            approved_screen_ques: true,
        }),
    })
    .then(response => response.json())
    .then(data => {
        // Display AI agent response in the textarea
        document.getElementById("agentResponse").value = data.response;
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
