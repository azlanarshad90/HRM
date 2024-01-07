let mode = 'jd';
let jobDetails = {};

function updateChatBox(content) {
    var chatBubble = document.createElement("div");
    chatBubble.className = "chat-bubble";
    chatBubble.innerHTML = content;

    document.getElementById("chatBox").appendChild(chatBubble);

    var chatBox = document.getElementById("chatBox");
    chatBox.scrollTop = chatBox.scrollHeight;
}

function submitJobDetails() {
    jobDetails.title = document.getElementById("title").value;
    jobDetails.salary = document.getElementById("salary").value;
    jobDetails.experience = document.getElementById("experience").value;
    jobDetails.skills = document.getElementById("skills").value;
    jobDetails.location = document.getElementById("location").value;
    jobDetails.jobType = document.getElementById("jobType").value;

    updateChatBox('<div class="agent-message">Job details submitted. Now, you can ask for a job description.</div>');
}


function submitUserQuery() {
    var userQuery = document.getElementById("userQuery").value;

    updateChatBox('<div class="user-message">' + userQuery + '</div>');
    let apiUrl = mode === 'jd' ? '/get-jd' : '/get-screening-questions';

    fetch(apiUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            Title: jobDetails.title,
            Salary_Range: jobDetails.salary,
            Required_Experience: jobDetails.experience,
            Required_Skills: jobDetails.skills,
            Location: jobDetails.location,
            Job_Type: jobDetails.jobType,
            userInput: userQuery,
            approved_jd: false,
            previousResponse: previousResponse,
            approved_screen_ques: false,
        }),
    })
    .then(response => response.json())
    .then(data => {
        updateChatBox('<div class="agent-message">' + data.response + '</div>');
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

let previousResponse = '';

function saveAndProceed() {
    let apiUrl = mode === 'jd' ? '/get-jd' : '/get-screening-questions';

    fetch(apiUrl, {
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
        previousResponse = data.response;

        updateChatBox('<div class="agent-message">Final approved JD is: ' + previousResponse + '</div>');

        mode = 'screening-questions';
    
        if (data.next_route) {
            apiUrl = data.next_route;
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function approveScreeningQuestions() {
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
        updateChatBox('<div class="agent-message">' + data.response + '</div>');
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
