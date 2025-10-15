# solely to be used for the code to create the search and filter functions/feature
# creating the fucntion for the search and filter feature:
#imports
from decimal import Decimal
from datetime import datetime
from datetime import date,timedelta

from collections import defaultdict
from decimal import Decimal






def search_Filter(Expenses, name_query, Category_Choice, date_query):
    results_SearchFilter = []
    
    # name matches for name query.. auto completeion:

    name_matches = lambda e,q: True if not q else (q.lower() in e.name.lower())

    # normalize inputs
    name_query = name_query.strip().lower() if name_query else ""


    date_query = date_query.strip() if date_query else ""

    # try parsing date input (error handling, proactinvely handlign potential errors)
    try:
        parsed_date = datetime.strptime(date_query, "%Y-%m-%d").date() if date_query else None
    except ValueError:
        print(" Invalid date format, ignoring date filter.")
        parsed_date = None
    
    for e in Expenses:
        # check each condition independently
        match_name = name_matches(e,name_query)

        if not Category_Choice:
            match_category = True
        else:
            match_category = e.category.lower() in Category_Choice  # any one match


        #match_date = True if not parsed_date else (e.date == parsed_date)

        if not parsed_date:
            match_date = True
        else:
            parts = date_query.split("-")

            if len(parts) ==1:
                try:
                    match_date = (e.date.year==int(parts[0]))
                except ValueError:
                    print("Invalid date format.(will be ignored in filter)")
                    match_date = True

            
            elif len(parts)==2:
                try:
                    match_date = (e.date.year == int(parts[0]) and e.date.month == int(parts[1]))
                
                except ValueError:
                    
                    print("Invalid date format.(will be ignored in filter)")
                    match_date = True
            
            elif len(parts)==3:
                try:
                
                    match_date = e.date ==parsed_date
                
                except ValueError:

                    print("Invalid date format.(will be ignored in filter)")
                    match_date = True

            else:
                print("Invalid date format.(will be ignored in filter)")
                match_date = True

        # normal way: 
        #(
      #  if not name_query:
      #      match_name = True
       # else:
       #     match_name = name_query in e.name.lower()
        
      #  if not Category_Choice:
       #     match_category = True
      #  else:
       #     match_category = e.category.lower() ==Category_Choice
       # if not parsed_date:
       #     match_date = True
        #else:
        #    match_date=e.date ==parsed_date
        #
        #)


        # include expense only if all match
        if match_name and match_category and match_date:
            results_SearchFilter.append(e)

    return results_SearchFilter



