# Solely to be used for the CSV export. text summary export and Charts.....
# working on csv feature:

#imports

from models import Expense
import csv
import os

def csv_to_export(Expenses,filename ="data/expenses_export.csv"):
    if not Expenses:
        print("No expenses to export.")
        return
    
    #ensuring folder exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    #converting the first expense to dict to extract headers

    headers = list(Expenses[0].to_dict().keys())

    with open (filename,"w",newline="",encoding="utf-8") as f:
        writer = csv.DictWriter(f,fieldnames=headers)
        writer.writeheader()

    
        for e in Expenses:
            writer.writerow(e.to_dict())

    print(f"✅ Expenses exported successfully to '{filename}'")




    