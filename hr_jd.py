import os
import openai
import traceback
from dotenv import load_dotenv
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from flask import Flask, jsonify, request, session
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory, ConversationBufferWindowMemory
from langchain.agents import ZeroShotAgent, AgentExecutor
from langchain.agents import AgentType, initialize_agent, load_tools

app = Flask(__name__)

app.secret_key = 'hr_jd'
openai.api_key = ""
load_dotenv()

openai.api_key = os.environ["OPENAI_API_KEY"]

print(openai.api_key)
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
prompt = ZeroShotAgent.create_prompt(
    tools=tools,
    prefix=prefix,
    suffix=suffix,
    input_variables=["input", "chat_history", "agent_scratchpad"],
  )
memory = ConversationBufferMemory(memory_key="chat_history")
# memory.save_context({"input": "hi"}, {"output": "Hi, how can I help you with your new job opening?"})
# memory.save_context({"input": "Write me a job description for an Engineer"}, {"output": "Sure, I would love to. Can you please provide me with more details of this new job opening as an Engineer."})
# memory.save_context({"input": "We need an Electrical Engineer with 3 years of experience"}, {"output": "Great, I see you need an Electrical Engineer with 3 years of experience. But for a job description, I need more details from you. Can you please provide me the details like, Main Responsibilities, Salary Range, Required Qualifications or any other things you would like to add?"})
# memory.save_context({"input": "The minimum qualification must be Bachelors Degree and salary will range from $3000 to $4000"}, {"output": "I got your requirements. What about the main responsibilities or anything that you want me to add in the job description?"})
# memory.save_context({"input": "Tell me a joke"}, {"output": "I'm sorry. As an HR assistant I can only create Job Description for you. Do you want me to create one for you?"})
# memory.load_memory_variables({})
llm_chain = LLMChain(llm=llm, prompt=prompt)
agent = ZeroShotAgent(llm_chain=llm_chain, tools=tools, verbose=True, handle_parsing_errors="Take action and give output!")
agent_chain = AgentExecutor.from_agent_and_tools(
    agent=agent, tools=tools, verbose=True, memory=memory, max_execution_time=2, early_stopping_method="generate", handle_parsing_errors=True
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
        main_prompt = f"""Answer the user's input given in triple backticks and Develop a detailed job description from your creativity for the information given to you:
                        1. Job Title: {title}
                        2. Salary Range: {salary}
                        3. Required Experience: {experience}
                        4. Required Skills: {skills}
                        5. Location: {location}
                        6. Onsite or Remote: {job_type}
                        If user starts the conversation, then you must greet the user and ask them if they need anything. Access these input parameters when the user need to develop a job description.
                        Extract these parameters from the chat history and user input.
                        If you do not find these six parameters or any of the parameter is missing, then query the user for the missing parameters.
                        Once you have all six parameters, proceed to develop the job description with maximum detail according to your ability.
                        If user required any updates or changes, then make those changes and show the complete updated job description to user.
                        Only return the job description without any other extra words.
                        Note: Develop as more detailed job description as you can and showcase your creativity.
                        ```{userInput}```
                        """
        try:
            response = agent_chain.run(main_prompt)
        except ValueError as e:
            response = str(e)
            if not response.startswith("Could not parse LLM output: `"):
                raise e
            response = response.replace("Could not parse LLM output: `AI:", '')
            response = response.replace("`", '')
        final_jd = response
        response_text = jsonify({'response': response})
        return response_text
      elif approved_jd == "True":
        print("Final Approved JD is:\n", final_jd)
        session["final_jd"]=final_jd
        memory = ""
        response_text = jsonify({'response': final_jd})
        print("In JD route: ", memory)
        return response_text
  except Exception as e:
      print("Error getting chat response:", e)
      traceback.print_exc()
      return jsonify({'response': "I'm having trouble with that question. Please rephrase it to help me understand?"})


@app.route('/get-screening-questions', methods=['POST'])
def get_screening_questions():
  global final_questions, memory
  try:
      final_jd = session.get("final_jd",None)
      session.clear()
      data = request.get_json()
      userInput = data.get('userInput', '')
      approved_screen_ques = data.get('approved_screen_ques', False)
      response = ''
      if userInput != "":
        main_prompt = f"""Answer the user's input given in triple backticks and develop at least 10 screening questions from the given Job Description:
                        1. Job Description: {final_jd}
                        Extract the job description from the chat history and user input.
                        If user required any updates or changes, then make those changes and show the complete updated screening question to user.
                        Only return the all screening question in numbers without any other extra words.
                        ```{userInput}```
                        """
        try:
            response = agent_chain.run(main_prompt)
        except ValueError as e:
            response = str(e)
            if not response.startswith("Could not parse LLM output: `"):
                raise e
            response = response.replace("Could not parse LLM output: `AI:", '')
            response = response.replace("`", '')
        final_questions = response
        response_text = jsonify({'response': response})
        return response_text
      elif approved_screen_ques == "True":
        print("Final Approved screening questions are:\n", final_questions)
        memory = ""
        response_text = jsonify({'response': final_questions})
        print("In screen route: ", memory)
        return response_text
  except Exception as e:
      print("Error getting chat response:", e)
      traceback.print_exc()
      return jsonify({'response': "I'm having trouble with that question. Please rephrase it to help me understand?"})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug = True)
