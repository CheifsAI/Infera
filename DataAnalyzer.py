from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from OprFuncs import data_infer, extract_code, extract_questions
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import re

class DataAnalyzer:
    def __init__(self,dataframe,llm):
        self.dataframe = dataframe
        self.llm = llm
        self.data_info = data_infer(dataframe)
        self.memory = []

    def analysis_data(self):
        data_info = self.data_info

        # Prompt and Chain for Analysis Data
        analysis_prompt = '''
        You are a data analyst. You are provided with a dataset about {data_info}
        Here is the dataset structure:
        {data_info}

        Please analyze the data and provide insights about:
        1. Key trends and patterns in the {data_info}.
        2. Any anomalies or outliers in the data.
        3. Recommendations or actionable insights based on the analyzed data.
        '''
        # Define the prompt template
        analysis_template = PromptTemplate(
            input_variables=["data_info"],
            template=analysis_prompt
        )
        # Create a chain for analysis data
        analysis_chain = LLMChain(llm=self.llm, prompt=analysis_template)

        # Run the analysis chain on the provided data
        analysis = analysis_chain.run(data_info=data_info)

        # Log the interaction in memory
        self.memory.append(HumanMessage(content=analysis_prompt))
        self.memory.append(AIMessage(content=analysis))

        # Return the analysis
        return analysis        

    # Drop Nulls
    def drop_nulls(self):
        data_info = self.data_info
        
        # Prompt and Chain for dropping nulls
        drop_nulls_prompt = '''
        create a code to drop the nulls from the DataFrame named 'df',
        only include the dropping part and importing pandas,
        insure that inplace = True, no extra context or reading the file.
        '''
        # Define the prompt template
        drop_nulls_template = PromptTemplate(
            input_variables=["data_info"],
            template=drop_nulls_prompt
        )
        # Create a chain for dropping nulls
        drop_nulls_chain = LLMChain(llm=self.llm, prompt=drop_nulls_template)
        
        # Extracting code for dropping nulls
        drop_nulls_code = extract_code(drop_nulls_chain.run(data_info=data_info))
        
        # Print the code for dropping nulls
        print("Code for dropping nulls:\n", drop_nulls_code)

        self.memory.append(HumanMessage(content=drop_nulls_prompt))
        self.memory.append(AIMessage(content=drop_nulls_code))
        
        # Drop null values from the data
        exec_env = {"df": self.dataframe}
        exec(drop_nulls_code, exec_env)
        updated_df = exec_env["df"]
        return updated_df


    # Question Generator
    def questions_gen(self, num):
        data_info = self.data_info

        # Prompt Template for Question Generation
        question_prompt = '''
        Create {num} analysis questions about the following data: 
        {data_info}
        Please format each question on a new line without numbering.
        '''
        
        # Define the prompt template
        question_template = PromptTemplate(
            input_variables=["num", "data_info"],
            template=question_prompt
        )
        
        # Create a chain for question generation
        # Create a chain for question generation
        from langchain.schema.runnable import RunnableLambda

        # Create a RunnableSequence instead of LLMChain
        question_chain = question_template | self.llm

        # Use .invoke() instead of .run()
        generated_questions = question_chain.invoke({"num": num, "data_info": data_info})


        
        # Parse the generated text into a list of questions
        print("Generated Questions:", generated_questions)  # Debugging Output

        questions_list = self._extract_questions(generated_questions)
        
        # Update conversation memory with actual inputs/outputs
        formatted_prompt = question_template.format(num=num, data_info=data_info)
        self.memory.append(HumanMessage(content=formatted_prompt))
        self.memory.append(AIMessage(content="\n".join(questions_list)))
        
        return questions_list

    def _extract_questions(self, generated_questions):
        # Extract text from the dictionary
        if isinstance(generated_questions, dict):
            text = generated_questions.get("text", "")  # Adjust key based on actual output
        else:
            text = str(generated_questions)  # Convert to string if unexpected type

        if not text:
            return []

        return [line.strip() for line in text.split('\n') if line.strip()]



    def visual(self, questions):
        data_info = self.data_info
        
        # Prompt for creating visualization code
        visual_prompt = '''
        I already have a DataFrame named 'df'. Generate **correctly formatted** matplotlib code to answer each question in {questions}.
        Ensure the code is **indented properly** and follows Python syntax standards.
        Use the following columns information: {data_info}. Create only the visualization code.
        '''
        
        # Define the prompt template
        visual_template = PromptTemplate(
            input_variables=["data_info", "questions"],
            template=visual_prompt
        )
        
        # Create a chain for generating visualizations
        visual_chain = LLMChain(llm=self.llm, prompt=visual_template)
        
        # Extracting the visualization code
        viscode = extract_code(visual_chain.run(data_info=data_info, questions=questions))
        
        # Print the generated visualization code
        print("Generated Visualization Code:\n", viscode)

        self.memory.append(HumanMessage(content="Generated visualization"))

        self.memory.append(AIMessage(content=viscode))

        # Execute the visualization code
        exec_env = {"df": self.dataframe}
        exec(viscode, exec_env)

    def chat(self):
        prompt_template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a data analyst.",
                    ),
                    MessagesPlaceholder(variable_name="memory"),
                    ("human", "{input}"),
                    ]
                    )
        chain = prompt_template | self.llm

        while True:
            question = input("You: ")
            if question == "done":
                return
            # response = llm.invoke(question)
            response = chain.invoke({"input": question, "memory":self.memory})
            self.memory.append(HumanMessage(content=question))
            self.memory.append(AIMessage(content=response))
            return response