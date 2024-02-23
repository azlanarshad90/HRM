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
from langchain.memory import ConversationBufferWindowMemory
from langchain.memory import RedisChatMessageHistory
from langchain.agents import ZeroShotAgent, AgentExecutor
from langchain.agents import load_tools

app = Flask(__name__)

app.secret_key = 'hr_jd'
load_dotenv()

openai.api_key = os.environ["OPENAI_API_KEY"]

def generate_session_id():
    ip_address = request.remote_addr
    random_number = str(random.randint(1, 1000000))
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

memory = ""
llm = ChatOpenAI(
    temperature=1.0,  #For more creativeness
    openai_api_key=openai.api_key,
    model_name="gpt-4",
    verbose=True    
)

tools = load_tools(["llm-math"], llm=llm)
prefix = """You are an AI assistant who helps users in development of job description. The job description is finalized by confirming all the important information. Only finalize the job description when the user tells you to. Never access the tools."""
suffix = """Begin!"{chat_history}Question: {input}{agent_scratchpad}"""
conversation_memory = ConversationBufferWindowMemory(memory_key="chat_history", k=1, chat_memory=history)
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
final_jd = ''
final_questions = ''

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
                Answer the user's input given in triple backticks and Develop a more detailed job description as you can from your ability from the information given to you:
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
                Note: Always Develop a more detailed job description as you can and showcase your creativity. Also always check for any english grammar or spelling mistakes in user input and correct them with your ability but never tell it in your responses.
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
            response_text = jsonify({'response': response})
            return response_text
        elif approved_jd:
            print("Final Approved JD is:\n", final_jd)
            session["final_jd"] = final_jd
            response_text = jsonify({'response': final_jd, 'next_route': '/get-screening-questions'})
            return response_text
        else:
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
        
        main_prompt = f"""
            Answer the user's input given in triple backticks and develop at least 10 screening questions that should only be Yes or No questions from the given Job Description:
            1. Job Description: {previousResponse}
            Extract the job description from the chat history and user input.
            If user required any updates or changes, then make those changes and show the complete updated screening question to user.
            Only return the all screening question in numbers without any other extra words.
            Note: All questions should only be Yes or No questions.
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
    app.run(host="0.0.0.0", port=5000, debug = True)
