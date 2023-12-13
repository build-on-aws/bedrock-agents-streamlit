import json

    
def lambda_handler(event, context):
    print(event)
  
    # Mock data for demonstration purposes
    company_data = {
        #Technology Industry
        1: {"companyId": 1, "companyName": "TechNova Inc.", "industrySector": "Technology", "revenue": 10000, "expenses": 3000, "profit": 7000, "employees": 10},
        2: {"companyId": 2, "companyName": "QuantumLeap Technologies", "industrySector": "Technology", "revenue": 20000, "expenses": 4000, "profit": 16000, "employees": 10},
        3: {"companyId": 3, "companyName": "CyberSecure IT", "industrySector": "Technology", "revenue": 30000, "expenses": 5000, "profit": 25000, "employees": 10},
        4: {"companyId": 4, "companyName": "DigitalDreams Gaming", "industrySector": "Technology", "revenue": 40000, "expenses": 6000, "profit": 34000, "employees": 10},
        5: {"companyId": 5, "companyName": "NanoMed Pharmaceuticals", "industrySector": "Technology", "revenue": 50000, "expenses": 7000, "profit": 43000, "employees": 10},
        6: {"companyId": 6, "companyName": "RoboTech Industries", "industrySector": "Technology", "revenue": 60000, "expenses": 8000, "profit": 52000, "employees": 12},
        7: {"companyId": 7, "companyName": "FutureNet Solutions", "industrySector": "Technology",  "revenue": 60000, "expenses": 9000, "profit": 51000, "employees": 10},
        8: {"companyId": 8, "companyName": "InnovativeAI Corp", "industrySector": "Technology", "revenue": 65000, "expenses": 10000, "profit": 55000, "employees": 15},
        9: {"companyId": 9, "companyName": "EcoTech Energy", "industrySector": "Technology", "revenue": 70000, "expenses": 11000, "profit": 59000, "employees": 10},
        10: {"companyId": 10, "companyName": "TechHealth Systems", "industrySector": "Technology", "revenue": 80000, "expenses": 12000, "profit": 68000, "employees": 10},
    
        #Real Estate Industry
        11: {"companyId": 11, "companyName": "LuxuryLiving Real Estate", "industrySector": "Real Estate", "revenue": 90000, "expenses": 13000, "profit": 77000, "employees": 10},
        12: {"companyId": 12, "companyName": "UrbanDevelopers Inc.", "industrySector": "Real Estate", "revenue": 100000, "expenses": 14000, "profit": 86000, "employees": 10},
        13: {"companyId": 13, "companyName": "SkyHigh Towers", "industrySector": "Real Estate", "revenue": 110000, "expenses": 15000, "profit": 95000, "employees": 18},
        14: {"companyId": 14, "companyName": "GreenSpace Properties", "industrySector": "Real Estate", "revenue": 120000, "expenses": 16000, "profit": 104000, "employees": 10},
        15: {"companyId": 15, "companyName": "ModernHomes Ltd.", "industrySector": "Real Estate", "revenue": 130000, "expenses": 17000, "profit": 113000, "employees": 10},
        16: {"companyId": 16, "companyName": "Cityscape Estates", "industrySector": "Real Estate", "revenue": 140000, "expenses": 18000, "profit": 122000, "employees": 10},
        17: {"companyId": 17, "companyName": "CoastalRealty Group", "industrySector": "Real Estate", "revenue": 150000, "expenses": 19000, "profit": 131000, "employees": 10},
        18: {"companyId": 18, "companyName": "InnovativeLiving Spaces", "industrySector": "Real Estate", "revenue": 160000, "expenses": 20000, "profit": 140000, "employees": 10},
        19: {"companyId": 19, "companyName": "GlobalProperties Alliance", "industrySector": "Real Estate", "revenue": 170000, "expenses": 21000, "profit": 149000, "employees": 11},
        20: {"companyId": 20, "companyName": "NextGen Residences", "industrySector": "Real Estate", "revenue": 180000, "expenses": 22000, "profit": 158000, "employees": 260}
    }  
    
  
    def get_named_parameter(event, name):
        return next(item for item in event['parameters'] if item['name'] == name)['value']
    
    def get_named_property(event, name):
        return next(item for item in event['requestBody']['content']['application/json']['properties'] if item['name'] == name)['value']

 
    def companyResearch(event):
        # Retrieve the company name from the event
        companyName = get_named_parameter(event, 'name') 
        print("NAME PRINTED: ", companyName)
        
        # Normalize the input for case-insensitive comparison
        companyName = companyName.lower()
    
        # Search for the company in the dictionary
        for company_id, company_info in company_data.items():
            if company_info["companyName"].lower() == companyName.lower():
                return company_info
        
            
        # Return None if the company is not found
        return None
    
    
  
    def createPortfolio(event, company_data):
        numCompanies = int(get_named_parameter(event, 'numCompanies'))
        industry = get_named_parameter(event, 'industry')

        # Filter companies by the specified industry
        industry_filtered_companies = [company for company in company_data.values() 
                                       if company['industrySector'].lower() == industry.lower()]
    
        # Sort companies by revenue in descending order
        sorted_companies = sorted(industry_filtered_companies, key=lambda x: x['profit'], reverse=True)
    
        # Select the top 'numCompanies' companies
        top_companies = sorted_companies[:numCompanies]
    
        return top_companies
        
  
    result = ''
    response_code = 200
    action_group = event['actionGroup']
    api_path = event['apiPath']
    
    print("api_path: ", api_path )
    
    if api_path == '/companyResearch':
        result = companyResearch(event)
    elif api_path == '/createPortfolio':
        result = createPortfolio(event, company_data)
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