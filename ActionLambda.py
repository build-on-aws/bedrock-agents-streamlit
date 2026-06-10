import json
import re
import boto3
from botocore.exceptions import ClientError

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
        {"companyId": 7, "companyName": "FuturePastNet Solutions", "industrySector": "Technology", "revenue": 60000, "expenses": 9000, "profit": 51000, "employees": 10},
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
        '''Function searches through the parameters list in the event dictionary and returns the value of the parameter whose name matches the provided name string'''
        return next(item for item in event['parameters'] if item['name'] == name)['value']

    def companyResearch(event):
        '''Searches for a company based on the 'name' parameter in the lambda event and returns its information if found.'''
        companyName = get_named_parameter(event, 'name').lower()
        print("NAME PRINTED: ", companyName)
        for company_info in company_data:
            if company_info["companyName"].lower() == companyName:
                return company_info
        return None

    def createPortfolio(event, company_data):
        '''Creates a portfolio of top companies based on the 'numCompanies' and 'industry' parameters in the lambda event.'''
        numCompanies = int(get_named_parameter(event, 'numCompanies'))
        industry = get_named_parameter(event, 'industry').lower()
        industry_filtered_companies = [company for company in company_data if company['industrySector'].lower() == industry]
        sorted_companies = sorted(industry_filtered_companies, key=lambda x: x['profit'], reverse=True)
        top_companies = sorted_companies[:numCompanies]
        return top_companies

    def sendEmail(event, company_data):
        '''Sends an email using Amazon SES with a summary report and portfolio details'''
        # Get parameters from event
        emailAddress = get_named_parameter(event, 'emailAddress')
        fomcSummary = next((item['value'] for item in event['parameters'] if item['name'] == 'fomcSummary'), "")
        portfolioDataString = get_named_parameter(event, 'portfolio')
        
        # Format portfolio data for display
        def _coerce_companies(raw):
            """Return a list of company dicts from either JSON or the Bedrock
            object-string format: {companies=[{revenue=80000, companyName=...}]}."""
            if isinstance(raw, dict):
                return raw.get('companies', [raw])
            if isinstance(raw, list):
                return raw
            if not isinstance(raw, str):
                return []
            # Try strict JSON first
            try:
                data = json.loads(raw)
                if isinstance(data, dict):
                    return data.get('companies', [data])
                if isinstance(data, list):
                    return data
            except (json.JSONDecodeError, ValueError):
                pass
            # Fall back to parsing the Bedrock key=value object-string format
            companies = []
            for block in re.findall(r'\{([^{}]*)\}', raw):
                fields = {}
                for m in re.finditer(r'(\w+)=(.+?)(?=,\s*\w+=|$)', block):
                    fields[m.group(1)] = m.group(2).strip()
                if fields:
                    companies.append(fields)
            return companies

        def _money(v):
            try:
                return f"${int(float(v)):,}"
            except (ValueError, TypeError):
                return str(v)

        companies = _coerce_companies(portfolioDataString)
        portfolio_html = ""
        portfolio_text = ""
        for i, company in enumerate(companies, 1):
            name = company.get('companyName', company.get('name', 'N/A'))
            revenue = _money(company.get('revenue', 'N/A'))
            expenses = _money(company.get('expenses', 'N/A'))
            profit = _money(company.get('profit', 'N/A'))
            employees = company.get('employees', 'N/A')

            portfolio_text += (f"  {i}. {name}\n"
                               f"     Revenue: {revenue}\n"
                               f"     Expenses: {expenses}\n"
                               f"     Profit: {profit}\n"
                               f"     Employees: {employees}\n\n")

            portfolio_html += f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">{i}</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{name}</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{revenue}</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{expenses}</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{profit}</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{employees}</td>
                </tr>"""

        if not companies:
            portfolio_text = str(portfolioDataString)
            portfolio_html = f"<p>{portfolioDataString}</p>"
        
        # Create the email content
        SENDER = emailAddress
        RECIPIENT = emailAddress
        SUBJECT = "Company Portfolio and Search Results Summary Report"
        
        # Plain text version
        BODY_TEXT = (f"Search Summary Report\n{'='*40}\n\n{fomcSummary}\n\n"
                     f"Portfolio Details\n{'='*40}\n\n{portfolio_text}")
        
        # HTML version with styled table
        BODY_HTML = f"""
        <html>
        <head></head>
        <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
            <h2 style="color: #232f3e;">Search Summary Report</h2>
            <p style="line-height: 1.6;">{fomcSummary}</p>
            <hr style="border: 1px solid #eee;">
            <h2 style="color: #232f3e;">Portfolio Details</h2>
            <table style="border-collapse: collapse; width: 100%;">
                <thead>
                    <tr style="background-color: #232f3e; color: white;">
                        <th style="padding: 10px; border: 1px solid #ddd;">#</th>
                        <th style="padding: 10px; border: 1px solid #ddd;">Company</th>
                        <th style="padding: 10px; border: 1px solid #ddd;">Revenue</th>
                        <th style="padding: 10px; border: 1px solid #ddd;">Expenses</th>
                        <th style="padding: 10px; border: 1px solid #ddd;">Profit</th>
                        <th style="padding: 10px; border: 1px solid #ddd;">Employees</th>
                    </tr>
                </thead>
                <tbody>
                    {portfolio_html}
                </tbody>
            </table>
        </body>
        </html>
        """
        
        CHARSET = "UTF-8"
        
        try:
            # Create a new SES client
            ses_client = boto3.client('ses')
            
            # Send the email
            response = ses_client.send_email(
                Destination={
                    'ToAddresses': [
                        RECIPIENT,
                    ],
                },
                Message={
                    'Body': {
                        'Html': {
                            'Charset': CHARSET,
                            'Data': BODY_HTML,
                        },
                        'Text': {
                            'Charset': CHARSET,
                            'Data': BODY_TEXT,
                        },
                    },
                    'Subject': {
                        'Charset': CHARSET,
                        'Data': SUBJECT,
                    },
                },
                Source=SENDER
            )
            
        except ClientError as e:
            print(e.response['Error']['Message'])
            return f"Error sending email: {str(e)}"
        else:
            return f"Email sent successfully to {emailAddress}! MessageId: {response['MessageId']}"

    result = ''
    response_code = 200
    action_group = event['actionGroup']
    api_path = event['apiPath']
    print("api_path: ", api_path)

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
