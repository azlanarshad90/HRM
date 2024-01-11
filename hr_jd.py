import os
import openai
import traceback
import hashlib
import random
from dotenv import load_dotenv
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from flask import Flask, jsonify, request, session, render_template, send_from_directory
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory, ConversationBufferWindowMemory
# from langchain_community.chat_message_histories.redis import RedisChatMessageHistory
from langchain.memory import RedisChatMessageHistory
from langchain.agents import ZeroShotAgent, AgentExecutor
from langchain.agents import AgentType, initialize_agent, load_tools

app = Flask(__name__)

app.secret_key = 'hr_jd'
openai.api_key = ""
load_dotenv()

# openai.api_key = os.environ["OPENAI_API_KEY"]
# openai_api_key = "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"
openai.api_key = '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'
def generate_session_id():
    ip_address = request.remote_addr
    random_number = str(random.randint(1, 1000000))  # Adjust the range as needed
    unique_string = f"{ip_address}-{random_number}"
    session_id = hashlib.sha256(unique_string.encode()).hexdigest()
    return session_id
session_id = str(generate_session_id)
REDIS_USERNAME = os.environ["REDIS_USERNAME"]
REDIS_PASSWORD = os.environ["REDIS_PASSWORD"]
REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = os.environ["REDIS_PORT"]
REDIS_DB = os.environ["REDIS_DB"]
REDIS_URL = f"redis://{REDIS_USERNAME}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
history = RedisChatMessageHistory(url=REDIS_URL, session_id=session_id, key_prefix='HR_Tool_TEST')
print("session_id: ----------------------\n", session_id)

memory = ""
llm = ChatOpenAI(
    temperature=1.0,
    openai_api_key=openai.api_key,
    model_name="gpt-4",
    verbose=True    
)

tools = load_tools(["llm-math"], llm=llm)
prefix = """You are an AI assistant who helps users in development of job description. The job description is finalized by confirming all the important information. Only finalize the job description when the user tells you to. Never access the tools."""
suffix = """Begin!"{chat_history}Question: {input}{agent_scratchpad}"""
# memory = ConversationBufferMemory(memory_key="chat_history")
conversation_memory = ConversationBufferWindowMemory(memory_key="chat_history", k=1, chat_memory=history)
# redis_memory = RedisChatMessageHistory(session_id="user_session")
# memory = [conversation_memory, redis_memory]
# memory.save_context({"input": "hi"}, {"output": "Hi, how can I help you with your new job opening?"})
# memory.save_context({"input": "Write me a job description for an Engineer"}, {"output": "Sure, I would love to. Can you please provide me with more details of this new job opening as an Engineer."})
# memory.save_context({"input": "We need an Electrical Engineer with 3 years of experience"}, {"output": "Great, I see you need an Electrical Engineer with 3 years of experience. But for a job description, I need more details from you. Can you please provide me the details like, Main Responsibilities, Salary Range, Required Qualifications or any other things you would like to add?"})
# memory.save_context({"input": "The minimum qualification must be Bachelors Degree and salary will range from $3000 to $4000"}, {"output": "I got your requirements. What about the main responsibilities or anything that you want me to add in the job description?"})
# memory.save_context({"input": "Tell me a joke"}, {"output": "I'm sorry. As an HR assistant I can only create Job Description for you. Do you want me to create one for you?"})
# memory.load_memory_variables({})
prompt = ZeroShotAgent.create_prompt(
    tools=tools,
    prefix=prefix,
    suffix=suffix,
    input_variables=["input", "chat_history", "agent_scratchpad"],
  )
llm_chain = LLMChain(llm=llm, prompt=prompt)
agent = ZeroShotAgent(llm_chain=llm_chain, tools=tools, verbose=True, handle_parsing_errors="Take action and give output!")
agent_chain = AgentExecutor.from_agent_and_tools(
    agent=agent, tools=tools, verbose=True, memory=conversation_memory, max_execution_time=2, early_stopping_method="generate", handle_parsing_errors=True
    )
# title = "AI developer"
# salary = "$4k to $5k"
# experience = "Minimum 5 years"
# skills = "NLP, Python, Django"
# location = "Lahore"
# job_type = "Remote"
final_jd = ''
final_questions = ''
# Similarly, after approving the Job Description, show the user ten screening questions accroding to that Job Description, and when the user approves the screening question, you must thanks at the end.
@app.route('/get-jd', methods=['POST'])
def get_job_description():
    global final_jd, memory
    try:
        data = request.get_json()
        userInput = data.get('userInput', '')
        approved_jd = data.get('approved_jd', False)
        title = data.get('Title', '')
        salary = data.get('Salary_Range', '')
        experience = data.get('Required_Experience', '')
        skills = data.get('Required_Skills', '')
        location = data.get('Location', '')
        job_type = data.get('Job_Type', '')
        response = ''
        if userInput != "":
            main_prompt = f"""
                Answer the user's input given in triple backticks and Develop a detailed job description from your creativity for the information given to you:
                1. Job Title: {title}
                2. Salary Range: {salary}
                3. Required Experience: {experience}
                4. Required Skills: {skills}
                5. Location: {location}
                6. Onsite or Remote: {job_type}
                If the user starts the conversation, then you must greet the user and ask them if they need anything. Access these input parameters when the user needs to develop a job description.
                Extract these parameters from the chat history and user input.
                If you do not find these six parameters or any of the parameters are missing, then query the user for the missing parameters.
                Once you have all six parameters, proceed to develop the job description with maximum detail according to your ability.
                If the user requires any updates or changes, then make those changes and show the complete updated job description to the user.
                Only return the job description without any other extra words.
                Note: Develop as a more detailed job description as you can and showcase your creativity.
                ```{userInput}```
            """
            try:
                response = agent_chain.run(input=main_prompt)
            except ValueError as e:
                response = str(e)
                if not response.startswith("Could not parse LLM output: `"):
                    raise e
                response = response.replace("Could not parse LLM output: `AI:", '')
                response = response.replace("`", '')
            final_jd = response
            print("Memory without approval: /n-------------------------", memory)
            response_text = jsonify({'response': response})
            return response_text
        elif approved_jd:
            print("Final Approved JD is:\n", final_jd)
            session["final_jd"] = final_jd
            # memory = ""
            response_text = jsonify({'response': final_jd, 'next_route': '/get-screening-questions'})
            print("After JD Approval: /n---------------------------------", memory)
            return response_text
        else:
            # Handle case where userInput and approved_jd are both empty or False
            return jsonify({'response': "Invalid request. Please provide userInput or set approved_jd to True."})
    except Exception as e:
        print("Error getting chat response:", e)
        traceback.print_exc()
        return jsonify({'response': "I'm having trouble with that question. Please rephrase it to help me understand?"})


@app.route('/get-screening-questions', methods=['POST'])
def get_screening_questions():
    global final_questions, memory
    try:
        final_jd = session.get("final_jd", None)
        session.clear()
        data = request.get_json()
        userInput = data.get('userInput', '')
        previousResponse = data.get('previousResponse', '')  # Get previous response
        approved_screen_ques = data.get('approved_screen_ques', False)
        response = ''
        
        # Use previous response in the conversation
        main_prompt = f"""
            Answer the user's input given in triple backticks and develop at least 10 screening questions from the given Job Description:
            1. Job Description: {previousResponse}
            Extract the job description from the chat history and user input.
            If user required any updates or changes, then make those changes and show the complete updated screening question to user.
            Only return the all screening question in numbers without any other extra words.
            ```{userInput}```
        """

        try:
            response = agent_chain.run(input=main_prompt)
        except ValueError as e:
            response = str(e)
            if not response.startswith("Could not parse LLM output: `"):
                raise e
            response = response.replace("Could not parse LLM output: `AI:", '')
            response = response.replace("`", '')
        final_questions = response
        print("Memory in screen route: /n---------------------", memory)
        response_text = jsonify({'response': response})
        return response_text
    except Exception as e:
        print("Error getting chat response:", e)
        traceback.print_exc()
        return jsonify({'response': "I'm having trouble with that question. Please rephrase it to help me understand?"})


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('C:\\Users\\Azlan\\OneDrive\\Desktop\\HR-JD', filename)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug = True)
