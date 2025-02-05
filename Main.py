from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from OprFuncs import data_infer, extract_code, extract_questions
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

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
    def quetions_gen (self, num):
        data_info = self.data_info
        
        # Prompt and Chain for Question Generation
        question_prompt = '''
        create {num} anlysis questions about the following data {data_info}
        '''
        # Define the prompt template
        question_template = PromptTemplate(
            input_variables=["num", "data_info"],
            template=question_prompt
        )
        
        # Create a chain for question generation
        question_chain = LLMChain(
            llm=self.llm,
            prompt=question_template
        )
        
        # Generate the questions
        questions = question_chain.run(num=num, data_info=data_info)
        
        questions_list = extract_questions(questions)

        self.memory.append(HumanMessage(content=question_prompt))
        self.memory.append(AIMessage(content="\n".join(questions_list)))      
        # Print the generated questions
        return questions_list


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

        self.memory.append(HumanMessage(content=visual_prompt))
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