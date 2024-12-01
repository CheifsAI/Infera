import pandas as pd
import io
import re
def data_infer(dataframe):   
    buffer = io.StringIO()
    dataframe.info(buf=buffer)
    data_info = buffer.getvalue()
    with open("df_info.txt", "w",
            encoding="utf-8") as f:  
        f.write(data_info)
    return data_info
def extract_code(input_text):
    result = re.search(r'```.*?\n(.*?)\n```', input_text, re.DOTALL)
    code = result.group(1) if result else input_text
    code_lines = code.splitlines()
    cleaned_code = "\n".join(line.strip() for line in code_lines)
    return cleaned_code.strip()
import pandas as pd
import os

def read_file(path):
    # Get the file extension
    _, extension = os.path.splitext(path)
    
    # Determine the file type and read accordingly
    if extension == ".csv":
        df = pd.read_csv(path)
    elif extension in [".xls", ".xlsx"]:
        df = pd.read_excel(path)
    else:
        raise ValueError(f"Unsupported file format: {extension}")
    
    return df
