
# Setup Amazon Bedrock agent, knowledge base, and action group with Streamlit

## Introduction
This guide details the setup process for an Amazon Bedrock agent on AWS, which will include setting up S3 buckets, a knowledge base, an action group, and a Lambda function. We will use the Streamlit framework for the user interface. The agent is designed to dynamically create an investment company portfolio based on specific parameters, and has Q&A capability to FOMC(Federal Open Market Committee) reports. This exercise will also include a sending email method, but will not be fully configured.

## Prerequisites
- An active AWS Account.
- Familiarity with AWS services like Amazon Bedrock, S3, Lambda, and Cloud9.

## Diagram

![Diagram](Streamlit_App/images/diagram.png)

## Configuration and Setup

### Step 1: Creating S3 Buckets
- Please make sure that you are in the **us-west-2** region. If another region is required, you will need to update the region in the `InvokeAgent.py` file on line 22 of the code. 
- **Domain Data Bucket**: Create an S3 bucket to store the domain data. For example, call the S3 bucket `knowledgebase-bedrock-agent-alias`. We will use the default settings. 

![Bucket create 1](Streamlit_App/images/bucket_pic_1.png)

![Bucket create 2](Streamlit_App/images/bucket_pic_2.png)

- Next, we will download the domain data from [here](https://github.com/build-on-aws/bedrock-agents-streamlit/tree/main/s3Docs). On your local computer, open up a cmd (command prompt) , and run the following curl commands to download the files:

```bash
  curl https://raw.githubusercontent.com/build-on-aws/bedrock-agents-streamlit/main/s3Docs/fomcminutes20230201.pdf --output ~/Downloads/fomcminutes20230201.pdf

  curl https://raw.githubusercontent.com/build-on-aws/bedrock-agents-streamlit/main/s3Docs/fomcminutes20230322.pdf --output ~/Downloads/fomcminutes20230322.pdf
  
  curl https://raw.githubusercontent.com/build-on-aws/bedrock-agents-streamlit/main/s3Docs/fomcminutes20230614.pdf --output ~/Downloads/fomcminutes20230614.pdf
  
  curl https://raw.githubusercontent.com/build-on-aws/bedrock-agents-streamlit/main/s3Docs/fomcminutes20230726.pdf --output ~/Downloads/fomcminutes20230726.pdf
  
  curl https://raw.githubusercontent.com/build-on-aws/bedrock-agents-streamlit/main/s3Docs/fomcminutes20230920.pdf --output ~/Downloads/fomcminutes20230920.pdf
  
  curl https://raw.githubusercontent.com/build-on-aws/bedrock-agents-streamlit/main/s3Docs/fomcminutes20231101.pdf --output ~/Downloads/fomcminutes20231101.pdf
```
  
- These files will download to your **Downloads** folder. Upload these files to S3 bucket `knowledgebase-bedrock-agent-{alias}`.These files are the Federal Open Market Committee documents describing monetary policy decisions made at the Federal Reserved board meetings. The documents include discussion of economic conditions, policy directives to the Federal Reserve Bank of New York for open market operations, and votes on target ranges for the federal funds rate. More information can be found [here](https://www.federalreserve.gov/newsevents/pressreleases/monetary20231011a.htm). Once uploaded, please select one of the documents to open and review the content.

![bucket domain data](Streamlit_App/images/bucket_domain_data.png)


- **Artifacts Bucket**: Create another S3 bucket to store artifacts. For example, call it `artifacts-bedrock-agent-creator-{alias}`. Then, download the API schema file from [here](https://github.com/build-on-aws/bedrock-agents-streamlit/blob/main/ActionSchema.json) by running the following `curl` command in the command prompt:

```bash
  curl https://raw.githubusercontent.com/build-on-aws/bedrock-agents-streamlit/main/ActionSchema.json --output ~/Downloads/ActionSchema.json
```

- Upload this file from the **Downloads** folder to S3 bucket `artifacts-bedrock-agent-creator-{alias}`. The provided schema is an OpenAPI specification for the "PortfolioCreator API," which outlines the structure and capabilities of a service designed for company portfolio creation, company financial research, and sending an email. This API Schema is a rich description of each action, so agents know when to use it, and exactly how to call it and use results. This schmea defines three primary endpoints, `/companyResearch`, `/createPortfolio`, and `/sendEmail` detailing how to interact with the API, the required parameters, and the expected responses. Once uploaded, please select and open the .json document to review the content.

![Loaded Artifact](Streamlit_App/images/loaded_artifact.png)
 

### Step 2: Knowledge Base Setup in Bedrock Agent

- Before we setup the knowledge base, we will need to grant access to the models that will be needed for our Bedrock agent. Navigate to the Amazon Bedrock console, then on the left of the screen, scroll down and select **Model access**. On the right, select the orange **Manage model access** button.

![Model access](Streamlit_App/images/model_access.png)

- Select the checkbox next to the base models for the **Anthropic** column. Also, verify that **Titan Embeddings G1 - Text** column is checked, if not by default. This will provide you access to the required models. After, scroll down to the bottom right and select **Request model access**.


- After, verify that the Access status of the Models are green with **Access granted**.

![Access granted](Streamlit_App/images/access_granted.png)


- Now, we will create a knowledge base by selecting **Knowledge base** on the left, then selecting the orange button **Create knowledge base**.  

![create_kb_btn](Streamlit_App/images/create_kb_btn.png)

- You can use the default name, or enter in your own. Then, select **Next** at the bottom right of the screen.

![KB details](Streamlit_App/images/kb_details.gif)


- Sync S3 bucket `knowledgebase-bedrock-agent-alias` to this knowledge base.

![KB setup](Streamlit_App/images/KB_setup.png)

- For the embedding model, choose **Titan Embeddings G1 - Text v1.2**. Leave the other options as default, and scroll down to select **Next**.
 
![Vector Store Config](/static/vector_store_config.gif)

- On the next screen, review your work, then select **Create knowledge base**
(Creating the knowledge base may take a few minutes. You can continue to the next step in the meantime.)

![Review and Create KB](Streamlit_App/images/review_create_kb.png)



### Step 3: Lambda Function Configuration
- Create a Lambda function (Python 3.12) for the Bedrock agent's action group. We will call this Lambda function `PortfolioCreator-actions`. 

![Create Function](Streamlit_App/images/create_function.png)

![Create Function2](Streamlit_App/images/create_function2.png)

- Copy the python code provided below, or from the file [here](https://github.com/build-on-aws/bedrock-agents-streamlit/blob/main/ActionLambda.py) into your Lambda function. 

```python
import json

def lambda_handler(event, context):
    print(event)
  
    # Mock data for demonstration purposes
    company_data = [
        #Technology Industry
        {"companyId": 1, "companyName": "TechStashNova Inc.", "industrySector": "Technology", "revenue": 10000, "expenses": 3000, "profit": 7000, "employees": 10},
        {"companyId": 2, "companyName": "QuantumPirateLeap Technologies", "industrySector": "Technology", "revenue": 20000, "expenses": 4000, "profit": 16000, "employees": 10},
        {"companyId": 3, "companyName": "CyberCipherSecure IT", "industrySector": "Technology", "revenue": 30000, "expenses": 5000, "profit": 25000, "employees": 10},
        {"companyId": 4, "companyName": "DigitalMyricalDreams Gaming", "industrySector": "Technology", "revenue": 40000, "expenses": 6000, "profit": 34000, "employees": 10},
        {"companyId": 5, "companyName": "NanoMedNoLand Pharmaceuticals", "industrySector": "Technology", "revenue": 50000, "expenses": 7000, "profit": 43000, "employees": 10},
        {"companyId": 6, "companyName": "RoboSuperBombTech Industries", "industrySector": "Technology", "revenue": 60000, "expenses": 8000, "profit": 52000, "employees": 12},
        {"companyId": 7, "companyName": "FuturePastNet Solutions", "industrySector": "Technology",  "revenue": 60000, "expenses": 9000, "profit": 51000, "employees": 10},
        {"companyId": 8, "companyName": "InnovativeCreativeAI Corp", "industrySector": "Technology", "revenue": 65000, "expenses": 10000, "profit": 55000, "employees": 15},
        {"companyId": 9, "companyName": "EcoLeekoTech Energy", "industrySector": "Technology", "revenue": 70000, "expenses": 11000, "profit": 59000, "employees": 10},
        {"companyId": 10, "companyName": "TechyWealthHealth Systems", "industrySector": "Technology", "revenue": 80000, "expenses": 12000, "profit": 68000, "employees": 10},
    
        #Real Estate Industry
        {"companyId": 11, "companyName": "LuxuryToNiceLiving Real Estate", "industrySector": "Real Estate", "revenue": 90000, "expenses": 13000, "profit": 77000, "employees": 10},
        {"companyId": 12, "companyName": "UrbanTurbanDevelopers Inc.", "industrySector": "Real Estate", "revenue": 100000, "expenses": 14000, "profit": 86000, "employees": 10},
        {"companyId": 13, "companyName": "SkyLowHigh Towers", "industrySector": "Real Estate", "revenue": 110000, "expenses": 15000, "profit": 95000, "employees": 18},
        {"companyId": 14, "companyName": "GreenBrownSpace Properties", "industrySector": "Real Estate", "revenue": 120000, "expenses": 16000, "profit": 104000, "employees": 10},
        {"companyId": 15, "companyName": "ModernFutureHomes Ltd.", "industrySector": "Real Estate", "revenue": 130000, "expenses": 17000, "profit": 113000, "employees": 10},
        {"companyId": 16, "companyName": "CityCountycape Estates", "industrySector": "Real Estate", "revenue": 140000, "expenses": 18000, "profit": 122000, "employees": 10},
        {"companyId": 17, "companyName": "CoastalFocalRealty Group", "industrySector": "Real Estate", "revenue": 150000, "expenses": 19000, "profit": 131000, "employees": 10},
        {"companyId": 18, "companyName": "InnovativeModernLiving Spaces", "industrySector": "Real Estate", "revenue": 160000, "expenses": 20000, "profit": 140000, "employees": 10},
        {"companyId": 19, "companyName": "GlobalRegional Properties Alliance", "industrySector": "Real Estate", "revenue": 170000, "expenses": 21000, "profit": 149000, "employees": 11},
        {"companyId": 20, "companyName": "NextGenPast Residences", "industrySector": "Real Estate", "revenue": 180000, "expenses": 22000, "profit": 158000, "employees": 260}
    ]
    
  
    def get_named_parameter(event, name):
        return next(item for item in event['parameters'] if item['name'] == name)['value']
    
 
    def companyResearch(event):
        companyName = get_named_parameter(event, 'name').lower()
        print("NAME PRINTED: ", companyName)
        
        for company_info in company_data:
            if company_info["companyName"].lower() == companyName:
                return company_info
        return None
    
    def createPortfolio(event, company_data):
        numCompanies = int(get_named_parameter(event, 'numCompanies'))
        industry = get_named_parameter(event, 'industry').lower()

        industry_filtered_companies = [company for company in company_data
                                       if company['industrySector'].lower() == industry]

        sorted_companies = sorted(industry_filtered_companies, key=lambda x: x['profit'], reverse=True)

        top_companies = sorted_companies[:numCompanies]
        return top_companies

 
    def sendEmail(event, company_data):
        emailAddress = get_named_parameter(event, 'emailAddress')
        fomcSummary = get_named_parameter(event, 'fomcSummary')
    
        # Retrieve the portfolio data as a string
        portfolioDataString = get_named_parameter(event, 'portfolio')
    

        # Prepare the email content
        email_subject = "Portfolio Creation Summary and FOMC Search Results"
        #email_body = f"FOMC Search Summary:\n{fomcSummary}\n\nPortfolio Details:\n{json.dumps(portfolioData, indent=4)}"
    
        # Email sending code here (commented out for now)
    
        return "Email sent successfully to {}".format(emailAddress)   
      
      
    result = ''
    response_code = 200
    action_group = event['actionGroup']
    api_path = event['apiPath']
    
    print("api_path: ", api_path )
    
    if api_path == '/companyResearch':
        result = companyResearch(event)
    elif api_path == '/createPortfolio':
        result = createPortfolio(event, company_data)
    elif api_path == '/sendEmail':
        result = sendEmail(event, company_data)
    else:
        response_code = 404
        result = f"Unrecognized api path: {action_group}::{api_path}"
        
    response_body = {
        'application/json': {
            'body': result
        }
    }
        
    action_response = {
        'actionGroup': event['actionGroup'],
        'apiPath': event['apiPath'],
        'httpMethod': event['httpMethod'],
        'httpStatusCode': response_code,
        'responseBody': response_body
    }

    api_response = {'messageVersion': '1.0', 'response': action_response}
    return api_response

```

- Then, select **Deploy** in the tab section of the Lambda console. Review the code provided before moving to the next step. You will see that we are using mock data to represent various companies in the technology and real estate insdustry, along with functions that we will call later in this workshop. 

![Lambda deploy](Streamlit_App/images/lambda_deploy.png)

- Next, apply a resource policy to the Lambda to grant Bedrock agent access. To do this, we will switch the top tab from **code** to **configuration** and the side tab to **Permissions**. Then, scroll to the **Resource-based policy statements** section and click the **Add permissions** button.

![Permissions config](Streamlit_App/images/permissions_config.png)

![Lambda resource policy create](Streamlit_App/images/lambda_resource_policy_create.png)

- Here is an example of the resource policy. (At this part of the setup, we will not have a Bedrock agent Source ARN. So, enter in `arn:aws:bedrock:us-west-2:{accoundID}:agent/BedrockAgentID` for now. We will include the ARN once it’s generated in step 6 after creating the Bedrock Agent alias):

![Lambda resource policy](Streamlit_App/images/lambda_resource_policy.png)


### Step 4: Setup Bedrock Agent and Action Group 
- Navigate to the Bedrock console, go to the toggle on the left, and under **Orchestration** select Agents, then select **Create Agent**.

![Orchestration2](Streamlit_App/images/orchestration2.png)

- On the next screen, provide an agent name, like “PortfolioCreator”. Leave the other options as default, then select **Next**.

![Agent details](Streamlit_App/images/agent_details.png)

![Agent details 2](Streamlit_App/images/agent_details_2.png)

- Select the **Anthropic: Claude V1.2 model**. Now, we need to add instructions by creating a prompt that defines the rules of operation for the agent. In the prompt below, we provide specific direction on how the model should use tools to answer questions. Copy, then paste the details below into the agent instructions. 

```text
You are an investment banker who creates portfolios of companies based on the number of companies, and industry in the <question>. An example of a portfolio looks like <portfolio_example>. You also research companies, and summarize documents. When requested, you format emails like <email_format>, then send these emails that include company portfolios and a summary of searched results. 
```

![Model select2](Streamlit_App/images/select_model.png)

- When creating the agent, select Lambda function `PortfolioCreator-actions`. Next, select the schema file `ActionSchema.json` from the s3 bucket `artifacts-bedrock-agent-creator-alias`. Then, select **Next**. 

![Add action group](Streamlit_App/images/action_group_add.png)


- Now, we need to provide the Bedrock agent an example of a formatted company portfolio, and a formatted email. On the Agent Overview screen, scroll down and select **Working draft**.

![Working draft](Streamlit_App/images/working_draft.png)

- Go down to **Advanced prompts** and select **Edit**.

![advance_prompt_btn](Streamlit_App/images/advance_prompt_btn.png)



- Select the **Orchestration** tab. Toggle on the radio button  **Override orchestration template defaults**. Make sure  **Activate orchestration template** is enabled as well.

- In the *Prompt template editor*, scroll down to line seven right below the closing tag `</auxiliary_instructions>`. Make two line spaces, then copy/paste in the following portfolio example and email format:

```sql
Here is an example of a company portfolio.  

<portfolio_example>

Here is a portfolio of the top 3 real estate companies:

  1. NextGenPast Residences with revenue of $180,000, expenses of $22,000 and profit of $158,000 employing 260 people. 
  
  2. GlobalRegional Properties Alliance with revenue of $170,000, expenses of $21,000 and profit of $149,000 employing 11 people.
  
  3. InnovativeModernLiving Spaces with revenue of $160,000, expenses of $20,000 and profit of $140,000 employing 10 people.  
  
</portfolio_example>


Here is an example of a formatted email.

<email_format>

Company Portfolio:

  1. NextGenPast Residences with revenue of $180,000, expenses of $22,000 and profit of $158,000 employing 260 people. 
  
  2. GlobalRegional Properties Alliance with revenue of $170,000, expenses of $21,000 and profit of $149,000 employing 11 people.
  
  3. InnovativeModernLiving Spaces with revenue of $160,000, expenses of $20,000 and profit of $140,000 employing 10 people.  


Searched Results Report:

  Participants noted that recent indicators pointed to modest growth in spending and production. Nonetheless, job gains had been robust in recent months, and the unemployment rate remained low. Inflation had eased somewhat but remained elevated.
   
  Participants recognized that Russia’s war against Ukraine was causing tremendous human and economic hardship and was contributing to elevated global uncertainty. Against this background, participants continued to be highly attentive to inflation risks.
</email_format>
```

- The results should look similar to the following:

![advance_prompt_setup](Streamlit_App/images/advance_prompt_setup.gif)

- When your done, scroll to the bottom and select **Save and exit**.


- Now, within your *working draft*, check to confirm that the *Orchestration* in the **Advance prompt** section is Overridden

![advance_prompt_overridden](Streamlit_App/images/adv_prompt_overridden.png)




### Step 5: Setup Knowledge Base with Bedrock Agent

- When integrating the KB with the agent, you will need to provide basic instructions on how to handle the knowledge base. For example, use the following:
  ```text
  Use this knowledge base when a user asks about data, such as economic trends, company financial statements, or the outcomes of the Federal Open Market Committee meetings.
  ```
 
![Knowledge base add2](Streamlit_App/images/add_knowledge_base2.png)

Review, then select the **Create Agent** button.

![create_agent_button](Streamlit_App/images/create_agent_button.png)


### Step 6: Create an alias
-Create an alias (new version), and choose a name of your liking. Make sure to copy and save your Agent ID and Agent Alias ID. You will need these in step 9.
 
![Create alias](Streamlit_App/images/create_alias.png)

- Next, navigate to the **Agent Overview** settings for the agent created by selecting **Agents** under the Orchestration dropdown menu on the left of the screen, then select the agent. Copy the Agent ARN, then add this ARN to the resource policy of Lambda function `PortfolioCreator-actions` previously created in step 3. 

![Agent ARN2](Streamlit_App/images/agent_arn2.png)


## Step 7: Testing the Setup
### Testing the Knowledge Base
- While in the Bedrock console, select **Knowledge base** under the Orchestration tab, then the KB you created. Scroll down to the Data source section, and make sure to select the **Sync** button.

![KB sync](Streamlit_App/images/kb_sync.png)

- You will see a user interface on the right where you will need to select a model. Choose the **Anthropic Claude V1.2 model**, then select **Apply**.

![Select model test](Streamlit_App/images/select_model_test.png)

- You should now have the ability to enter prompts in the user interface provided.

![KB prompt](Streamlit_App/images/kb_prompt.png)

- Test Prompts:
  ```text
  Give me a summary of financial market developments and open market operations in January 2023.
  ```
  ```text
  Can you provide information about inflation or rising prices?
  ```
  ```text
  What can you tell me about the Staff Review of the Economic & Financial Situation?
  ```

### Testing the Bedrock Agent
- While in the Bedrock console, select **Agents** under the Orchestration tab, then the agent you created. You should be able to enter prompts in the user interface provided to test your knowledge base and action groups from the agent.

![Agent test](Streamlit_App/images/agent_test.png)

- Example prompts for **Knowledge base**:
  ```text
  Give me a summary of financial market developments and open market operations in January 2023
  ```
  ```text
  Tell me the participants view on economic conditions and economic outlook
  ```
  ```text
  Provide any important information I should know about inflation, or rising prices
  ```
  ```text
  Tell me about the Staff Review of the Economic & financial Situation
  ```

- Example prompts for **Action groups**:
```text
  Create a portfolio with 3 companies in the real estate industry
```
```text
  Create portfolio of 3 companies that are in the technology industry
```
```text
  Create a new investment portfolio of companies
```
```text
  Do company research on TechStashNova Inc.
```

- Example prompt for KB & AG
  ```text
  Send an email to test@example.com that includes the company portfolio and FOMC summary
  ```
  `(The logic for this method is not implemented to send emails)`  



## Step 8: Setting Up Cloud9 Environment (IDE)

1.	Navigate in the Cloud9 management console. Then, select **Create Environment**

![create_environment](Streamlit_App/images/create_environment.png)

2. Here, you will enter the following values in each field
   - **Name**: Bedrock-Environment (Enter any name)
   - **Instance type**: t3.small
   - **Platform**: Ubuntu Server 22.04 LTS
   - **Timeout**: 1 hour  

![ce2](Streamlit_App/images/ce2.png)

   - Once complete, select the **Create** button at the bottom of the screen. The environment will take a couple of minutes to spin up. If you get an error spinning up Cloud9 due to lack of resources, you can also choose t2.micro for the instance type and try again. (The Cloud9 environment has Python 3.10.12 version at the time of this publication)


![ce3](Streamlit_App/images/ce3.png)

3. Navigate back to the Cloud9 Environment, then select **open** next to the Cloud9 you just created. Now, you are ready to setup the Streamlit app!

![environment](Streamlit_App/images/environment.png)


## Step 9: Setting Up and Running the Streamlit App
1. **Obtain the Streamlit App ZIP File**: Download the zip file of the project [here](https://github.com/build-on-aws/bedrock-agents-streamlit/archive/refs/heads/main.zip).

2. **Upload to Cloud9**:
   - In your Cloud9 environment, upload the ZIP file.

![Upload file to Cloud9](Streamlit_App/images/upload_file_cloud9.png)

3. **Unzip the File**:
   - Use the command `unzip bedrock-agents-streamlit-main.zip` to extract the contents.
4. **Navigate to Streamlit_App Folder**:
   - Change to the directory containing the Streamlit app. Use the command `cd ~/environment/bedrock-agents-streamlit-main/Streamlit_App`
5. **Update Configuration**:
   - Open the `InvokeAgent.py` file.
   - Update the `agentId` and `agentAliasId` variables with the appropriate values, then save it.

![Update Agent ID and alias](Streamlit_App/images/update_agentId_and_alias.png)

6. **Install Streamlit** (if not already installed):
   - Run `pip install streamlit`. Additionally, make sure boto3, and pandas dependencies are installed by running `pip install boto3` and `pip install pandas`.

7. **Run the Streamlit App**:
   - Execute the command `streamlit run app.py --server.address=0.0.0.0 --server.port=8080`.
   - Streamlit will start the app, and you can view it by selecting **Preview** within the Cloud9 IDE at the top, then **Preview Running Application**.
  
     ![Preview button](Streamlit_App/images/preview_btn.png)
     
     
   - Once the app is running, please test some of the sample prompts provided. (On 1st try, if you receive an error, try again.)

![Running App ](Streamlit_App/images/running_app.png)


Optionally, you can review the trace events in the left toggle of the screen. This data will include the rational tracing, invocation input tracing, and observation tracing.

![Trace events ](Streamlit_App/images/trace_events.png)


## Cleanup

After completing the setup and testing of the Bedrock Agent and Streamlit app, follow these steps to clean up your AWS environment and avoid unnecessary charges:
1. Delete S3 Buckets:
- Navigate to the S3 console.
- Select the buckets "knowledgebase-bedrock-agent-alias" and "artifacts-bedrock-agent-creator-alias". Make sure that both of these buckets are empty by deleting the files. 
- Choose 'Delete' and confirm by entering the bucket name.

2.	Remove Lambda Function:
- Go to the Lambda console.
- Select the "PortfolioCreator-actions" function.
- Click 'Delete' and confirm the action.

3.	Delete Bedrock Agent:
- In the Bedrock console, navigate to 'Agents'.
- Select the created agent, then choose 'Delete'.

4.	Deregister Knowledge Base in Bedrock:
- Access the Bedrock console, then navigate to “Knowledge base” under the Orchestration tab.
- Select, then delete the created knowledge base.

5.	Clean Up Cloud9 Environment:
- Navigate to the Cloud9 management console.
- Select the Cloud9 environment you created, then delete.




## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

