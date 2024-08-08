import os
from dotenv import load_dotenv
import yaml, psycopg2
from langchain.prompts.few_shot import FewShotPromptTemplate
from langchain.prompts.prompt import PromptTemplate
from langchain.sql_database import SQLDatabase
from langchain.chains.sql_database.prompt import PROMPT_SUFFIX, _postgres_prompt
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.llms import Bedrock
from langchain.prompts.example_selector.semantic_similarity import (
    SemanticSimilarityExampleSelector,
)
from langchain_community.vectorstores import Chroma
from langchain_experimental.sql import SQLDatabaseChain

# Loading environment variables
load_dotenv()

region = os.getenv("region")

# configuring your instance of Amazon bedrock, selecting the CLI profile, modelID, endpoint url and region.
llm = Bedrock(
    credentials_profile_name=os.getenv("profile_name"),
    model_id="amazon.titan-text-express-v1",
    endpoint_url=f"https://bedrock-runtime.{region}.amazonaws.com",
    region_name=region, 
    verbose=True
)


# Executing the SQL database chain with the users question
def rds_answer(question):
    """
    This function collects all necessary information to execute the sql_db_chain and get an answer generated, taking
    a natural language question in and returning an answer and generated SQL query.
    :param question: The question the user passes in from the frontend
    :return: The final answer in natural langauge along with the generated SQL query.
    """
    # retrieving the final RDS URI to initiate a connection with the database
    rds_uri = get_rds_uri()
    # formatting the RDS URI and preparing it to be used with Langchain sql_db_chain
    db = SQLDatabase.from_uri(rds_uri)
    # loading the sample prompts from SampleData/moma_examples.yaml
    examples = load_samples()
    # initiating the sql_db_chain with the specific LLM we are using, the db connection string and the selected examples
    sql_db_chain = load_few_shot_chain(llm, db, examples)
    # the answer created by Amazon Bedrock and ultimately passed back to the end user
    answer = sql_db_chain(question)

    if 'graph' in question:
        plot_data = run_aggregate_query(answer["intermediate_steps"][1])
    else:
        plot_data = None

    # Passing back both the generated SQL query and the final result in a natural language format
    return answer["intermediate_steps"][1], answer["result"], plot_data


def get_rds_uri():
    # SQLAlchemy 2.0 reference: https://docs.sqlalchemy.org/en/20/dialects/postgresql.html
    # URI format: postgresql+psycopg2://user:pwd@hostname:port/dbname
    """
    This function is used to build the RDS URL and eventually used to connect to the database.
    :return: The full RDS URL that is used to query against.
    """
    # setting the key parameters to build the rds connection string, these are stored in the .env file
    rds_username = os.getenv('rds_username')
    rds_password = os.getenv('rds_password')
    rds_endpoint = os.getenv('rds_endpoint')
    rds_port = os.getenv('rds_port')
    rds_db_name = os.getenv('rds_db_name')
    # taking all the inputted parameters and formatting them in a finalized string
    rds_uri = f"postgresql+psycopg2://{rds_username}:{rds_password}@{rds_endpoint}:{rds_port}/{rds_db_name}"
    # returning the final RDS URL that was built in the line of code above
    return rds_uri


def load_samples():
    """
    Load the sql examples for few-shot prompting examples
    :return: The sql samples in from the moma_examples.yaml file
    """
    # instantiating the sql samples variable
    sql_samples = None
    # opening our prompt sample file
    # SampleData/moma_examples.yaml

    with open("prompts.yaml", "r") as stream:
        # reading our prompt samples into the sql_samples variable
        sql_samples = yaml.safe_load(stream)

    # yaml_file_path = os.path.join(os.path.dirname(__file__), 'moma_examples.yaml')
    # with open(yaml_file_path, "r") as stream:
    #     sql_samples = yaml.safe_load(stream)

    # returning the sql samples as a string
    return sql_samples


def load_few_shot_chain(llm, db, examples):
    """
    This function is used to load in the most similar prompts, format them along with the users question and then is
    passed in to Amazon Bedrock to generate an answer.
    :param llm: Large Language model you are using
    :param db: The rds database URL
    :param examples: The samples loaded from your examples file.
    :return: The results from the SQLDatabaseChain
    """
    # This is formatting the prompts that are retrieved from the SampleData/moma_examples.yaml
    example_prompt = PromptTemplate(
        input_variables=["table_info", "input", "sql_cmd", "sql_result", "answer"],
        template=(
            "{table_info}\n\nQuestion: {input}\nSQLQuery: {sql_cmd}\nSQLResult:"
            " {sql_result}\nAnswer: {answer}"
        ),
    )
    # instantiating the hugging face embeddings model to be used to produce embeddings of user queries and prompts
    local_embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    # The example selector loads the examples, creates the embeddings, stores them in Chroma (vector store) and a
    # semantic search is performed to see the similarity between the question and prompts, it returns the 3 most similar
    # prompts as defined by k
    example_selector = SemanticSimilarityExampleSelector.from_examples(
        examples,
        local_embeddings,
        Chroma,
        k=min(3, len(examples)),
    )
    # This is orchestrating the example selector (finding similar prompts to the question), example_prompt (formatting
    # the retrieved prompts, and formatting the chat history and the user input
    few_shot_prompt = FewShotPromptTemplate(
        example_selector=example_selector,
        example_prompt=example_prompt,
        prefix=_postgres_prompt + "Provide no preamble",
        suffix=PROMPT_SUFFIX,
        input_variables=["table_info", "input", "top_k"],
    )
    # Where the LLM, DB and prompts are all orchestrated to answer a user query.
    return SQLDatabaseChain.from_llm(
        llm,
        db,
        prompt=few_shot_prompt,
        use_query_checker=True,
        verbose=True,
        return_intermediate_steps=True,
    )


# Function to run aggregate query using psycopg2
def run_aggregate_query(query):
    try:
        rds_username = os.getenv('rds_username')
        rds_password = os.getenv('rds_password')
        rds_endpoint = os.getenv('rds_endpoint')
        rds_port = os.getenv('rds_port')
        rds_db_name = os.getenv('rds_db_name')

        # Connect to your postgres DB
        conn = psycopg2.connect(
            dbname=rds_db_name,
            user=rds_username,
            password=rds_password,
            host=rds_endpoint,
            port=rds_port
        )

        # Create a cursor object
        cur = conn.cursor()

        # Execute the query
        cur.execute(query)

        # Fetch all the results
        results = cur.fetchall()

        # Close the cursor and connection
        cur.close()
        conn.close()

        return results

    except Exception as e:
        print(f"Error: {e}")
        return None
