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

let jobDetailsSubmitted = false;
function submitJobDetails() {
    jobDetails.title = document.getElementById("title").value;
    jobDetails.salary = document.getElementById("salary").value;
    jobDetails.experience = document.getElementById("experience").value;
    jobDetails.skills = document.getElementById("skills").value;
    jobDetails.location = document.getElementById("location").value;
    jobDetails.jobType = document.getElementById("jobType").value;
    if (!jobDetails.title || !jobDetails.salary || !jobDetails.experience || !jobDetails.skills || !jobDetails.location || !jobDetails.jobType) {
        alert('Please fill in all six input fields before submitting.');
        return;
    }

    updateChatBox('<div class="agent-message">Job details submitted. Now, you can ask for a job description.</div>');

    document.getElementById("inputjobdetails").disabled = true;
    document.getElementById("inputjobdetails").style.display = "none";

    document.getElementById("userQuery").disabled = false;
    document.getElementById("userInputSection").style.display = "block";
    
    document.getElementById("apiproceed").disabled = false;
    document.getElementById("apiproceed").style.display = "block";

    document.getElementById("submituserquerybutton").disabled = false;
    document.getElementById("submituserquerybutton").style.display = "block";

    jobDetailsSubmitted = true;
}


function submitUserQuery() {
    if (!jobDetailsSubmitted) {
        alert('Please submit job details first.');
        return;
    }
    document.getElementById("userQuery").disabled = true;
    var userQuery = document.getElementById("userQuery").value;
    document.getElementById("userQuery").value = "";

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
        document.getElementById("userQuery").disabled = false;
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById("userQuery").disabled = false;
    });
}
document.getElementById("userQuery").addEventListener("keyup", function(event) {
    if (event.key === "Enter") {
        submitUserQuery();
    }
});

let previousResponse = '';

function saveAndProceed() {
    document.getElementById("apiproceed").disabled = true;
    document.getElementById("apiproceed").style.display = "none";

    document.getElementById("userQuery").disabled = true;
    document.getElementById("userInputSection").style.display = "none";

    document.getElementById("submituserquerybutton").disabled = true;
    document.getElementById("submituserquerybutton").style.display = "none";

    document.getElementById("apiroutescreen").disabled = false;
    document.getElementById("apiroutescreen").style.display = "block";

    let apiUrl = mode === 'jd' ? '/get-jd' : '/get-screening-questions';
    userInput = ''

    fetch(apiUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            userInput: userInput,
            approved_jd: true,
        }),
    })
    .then(response => response.json())
    .then(data => {
        previousResponse = data.response;

        updateChatBox('<div class="agent-message">Final approved JD is: \n\n' + previousResponse + '</div>');

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

    updateChatBox('<div class="agent-message">You are all done' + '</div>');
    document.getElementById("inputjobdetails").disabled = true;
    document.getElementById("inputjobdetails").style.display = "none";

    document.getElementById("screenques").disabled = true;
    document.getElementById("screenques").style.display = "none";

    document.getElementById("userQuery").disabled = true;
    document.getElementById("userInputSection").style.display = "none";

    document.getElementById("submituserquerybutton").disabled = true;
    document.getElementById("submituserquerybutton").style.display = "none";

    alert('Kindly refresh the browser to start a new session.');
}


function apiScreeningQuestions() {
    userInput = "Create screening questions for the approved job description."
    updateChatBox('<div class="agent-message">Pleasse wait, the agent is creating some screening questions...' + '</div>');
    document.getElementById("apiroutescreen").disabled = true;
    document.getElementById("apiroutescreen").style.display = "none";
    fetch('/get-screening-questions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            userInput: userInput,
            approved_screen_ques: false,
        }),
    })
    .then(response => response.json())
    .then(data => {
        updateChatBox('<div class="agent-message">' + data.response + '</div>');

        document.getElementById("apiroutescreen").disabled = true;
        document.getElementById("apiroutescreen").style.display = "none";

        document.getElementById("userQuery").disabled = false;
        document.getElementById("userInputSection").style.display = "block";

        document.getElementById("submituserquerybutton").disabled = false;
        document.getElementById("submituserquerybutton").style.display = "block";

        document.getElementById("screenques").disabled = false;
        document.getElementById("screenques").style.display = "block";
    })
    .catch(error => {
        console.error('Error:', error);
    });
}