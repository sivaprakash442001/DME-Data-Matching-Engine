"""
Sample data generator for testing matching scenarios.
Generates realistic datasets matching the examples specified in the requirements.
"""
import os
import pandas as pd


SAMPLE_ADDRESS_DATA = [
    {"Address_A": "12, MG Road, Chennai", "Address_B": "12 MG Rd Chennai", "Expected_Category": "Strong Match"},
    {"Address_A": "45 Anna Nagar West", "Address_B": "45 Anna Nagar W", "Expected_Category": "Strong Match"},
    {"Address_A": "100 Main Street", "Address_B": "200 Main Street", "Expected_Category": "Possible Match"},
    {"Address_A": "Chennai, Tamil Nadu", "Address_B": "Mumbai, Maharashtra", "Expected_Category": "No Match"},
    {"Address_A": "12, MG Road, Anna Nagar, Chennai, Tamil Nadu 600040", "Address_B": "12 MG Rd Anna Nagar Chennai TN 600040", "Expected_Category": "Strong Match"},
    {"Address_A": "Flat 302, Green Valley Apts, Sector 14, Gurgaon", "Address_B": "Unit 302, Green Valley Apartments, Sec 14, Gurugram", "Expected_Category": "Strong Match"},
    {"Address_A": "742 Evergreen Terrace, Springfield, OR 97477", "Address_B": "742 Evergreen Terr, Springfield, Oregon 97477", "Expected_Category": "Strong Match"},
    {"Address_A": "No. 25, 1st Floor, 5th Cross, Indiranagar, Bangalore", "Address_B": "#25, Floor 1, 5th Cross Rd, Indira Nagar, Bengaluru", "Expected_Category": "Strong Match"},
    {"Address_A": "1600 Amphitheatre Pkwy, Mountain View, CA 94043", "Address_B": "1600 Amphitheatre Parkway, Mountain View, California", "Expected_Category": "Strong Match"},
    {"Address_A": "Suite 500, 350 5th Ave, New York, NY 10118", "Address_B": "Ste 500, 350 Fifth Avenue, NY, New York", "Expected_Category": "Strong Match"},
]

SAMPLE_COMPANY_DATA = [
    {"Company_A": "ABC Pvt. Ltd.", "Company_B": "abc private limited", "Expected_Category": "Strong Match"},
    {"Company_A": "ABC PVT LTD", "Company_B": "ABC Private Limited", "Expected_Category": "Strong Match"},
    {"Company_A": "A.B.C. PVT. LTD.", "Company_B": "ABC PRIVATE LTD", "Expected_Category": "Strong Match"},
    {"Company_A": "Acme Solutions Inc.", "Company_B": "Acme Solutions Incorporated", "Expected_Category": "Strong Match"},
    {"Company_A": "Reliance Industries Limited", "Company_B": "Reliance Ind Ltd", "Expected_Category": "Strong Match"},
    {"Company_A": "Global Tech Services Corp", "Company_B": "Global Tech Services Corporation", "Expected_Category": "Strong Match"},
    {"Company_A": "Tata Consultancy Services Ltd", "Company_B": "Tata Consultancy Services", "Expected_Category": "Strong Match"},
    {"Company_A": "Microsoft Corporation", "Company_B": "Microsoft Corp", "Expected_Category": "Strong Match"},
    {"Company_A": "XYZ Pharmaceuticals Ltd", "Company_B": "ABC Logistics Pvt Ltd", "Expected_Category": "No Match"},
    {"Company_A": "Apex Digital Media LLC", "Company_B": "Apex Digital Solutions LLP", "Expected_Category": "Likely Match"},
]

SAMPLE_PERSON_DATA = [
    {"Name_A": "John Michael Smith", "Name_B": "Smith, John M.", "Expected_Category": "Strong Match"},
    {"Name_A": "John Smith", "Name_B": "Smith John", "Expected_Category": "Strong Match"},
    {"Name_A": "John A Smith", "Name_B": "John Albert Smith", "Expected_Category": "Strong Match"},
    {"Name_A": "Dr. Robert Downey Jr.", "Name_B": "Downey, Robert", "Expected_Category": "Likely Match"},
    {"Name_A": "Priya Ramesh Sharma", "Name_B": "Sharma, Priya R.", "Expected_Category": "Strong Match"},
    {"Name_A": "Alexander Hamilton", "Name_B": "Hamilton, Alex", "Expected_Category": "Likely Match"},
    {"Name_A": "Alice Wonder", "Name_B": "Bob Builder", "Expected_Category": "No Match"},
    {"Name_A": "David K. Johnson", "Name_B": "D. K. Johnson", "Expected_Category": "Strong Match"},
    {"Name_A": "Sundar Pichai", "Name_B": "Pichai Sundararajan", "Expected_Category": "Likely Match"},
    {"Name_A": "Karthik Subramanian", "Name_B": "Karthik S", "Expected_Category": "Likely Match"},
]

SAMPLE_CUSTOMER_DATA = [
    {
        "Customer_ID_1": "CUST-1001",
        "Full_Name_1": "John M. Smith",
        "Company_1": "Apex Technologies Pvt Ltd",
        "Address_1": "12, MG Road, Chennai",
        "Phone_1": "+91 98765 43210",
        "Email_1": "john.smith@gmail.com",
        "Customer_ID_2": "CUST1001",
        "Full_Name_2": "Smith, John Michael",
        "Company_2": "Apex Tech Private Limited",
        "Address_2": "12 MG Rd, Chennai, TN",
        "Phone_2": "09876543210",
        "Email_2": "john.smith@gmail.com",
    },
    {
        "Customer_ID_1": "CUST-1002",
        "Full_Name_1": "Priya Sharma",
        "Company_1": "Global Logistics Inc",
        "Address_1": "45 Anna Nagar West, Chennai",
        "Phone_1": "+91 98111 22334",
        "Email_1": "priya.sharma@outlook.com",
        "Customer_ID_2": "CUST-1002",
        "Full_Name_2": "Sharma, Priya",
        "Company_2": "Global Logistics Incorporated",
        "Address_2": "45 Anna Nagar W, Chennai",
        "Phone_2": "9811122334",
        "Email_2": "priya.sharma@outlook.com",
    },
    {
        "Customer_ID_1": "CUST-1003",
        "Full_Name_1": "Robert E. Lee",
        "Company_1": "Acme Corp",
        "Address_1": "100 Main Street, Springfield",
        "Phone_1": "(555) 019-2834",
        "Email_1": "rlee@acme.com",
        "Customer_ID_2": "CUST-1003",
        "Full_Name_2": "Robert Lee",
        "Company_2": "Acme Corporation",
        "Address_2": "200 Main Street, Springfield",
        "Phone_2": "5550192834",
        "Email_2": "rlee@acme.com",
    },
    {
        "Customer_ID_1": "CUST-1004",
        "Full_Name_1": "Alice Walker",
        "Company_1": "Starlight Media LLC",
        "Address_1": "120 Broadway, New York, NY",
        "Phone_1": "+1 212 555 0144",
        "Email_1": "alice@starlight.com",
        "Customer_ID_2": "CUST-9999",
        "Full_Name_2": "Bob Harris",
        "Company_2": "Moonlight Enterprises",
        "Address_2": "742 Ocean Ave, Miami, FL",
        "Phone_2": "+1 305 555 0199",
        "Email_2": "bob@moonlight.com",
    },
]


def generate_sample_files(target_dir: str = "data/samples"):
    """Write sample CSV and Excel datasets to disk for instant user demonstration."""
    os.makedirs(target_dir, exist_ok=True)

    pd.DataFrame(SAMPLE_ADDRESS_DATA).to_csv(os.path.join(target_dir, "sample_addresses.csv"), index=False)
    pd.DataFrame(SAMPLE_COMPANY_DATA).to_csv(os.path.join(target_dir, "sample_companies.csv"), index=False)
    pd.DataFrame(SAMPLE_PERSON_DATA).to_csv(os.path.join(target_dir, "sample_persons.csv"), index=False)
    pd.DataFrame(SAMPLE_CUSTOMER_DATA).to_excel(os.path.join(target_dir, "sample_customers.xlsx"), index=False)


# Initialize samples on import
generate_sample_files()
