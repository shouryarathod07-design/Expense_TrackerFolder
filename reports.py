# Solely to be used for all the summaries annual, weekly, monthly ....etc.

#imports
from decimal import Decimal
from datetime import datetime
from datetime import date,timedelta

from collections import defaultdict
from decimal import Decimal

import datetime




# main




def monthly_summary(Expenses):
    #"""Print total expenses grouped by (year, month)."""
    monthly_totals = defaultdict(Decimal)


    

    # Group and aggregate
    for e in Expenses:
        key = (e.date.year, e.date.month)
        monthly_totals[key] += e.price

    # Print results sorted by date
    if not monthly_totals:
        print("No expenses to summarize.")
        return

    print("\nMonthly Summary:")
    for (y, m), total in sorted(monthly_totals.items()):
        print(f"{y}-{m:02d}: ${total}")
   
# Save to JSON


# monthly summary by category more meaningful and useful
def monthly_summaryByCat(Expenses):
    
    
     # Nested dict: { (year, month): {category: total} }
    monthly_cat_totals = defaultdict(lambda: defaultdict(Decimal))
    
    for e in Expenses:
        key = (e.date.year,e.date.month)
        monthly_cat_totals[key][e.category]+=e.price
    if not monthly_cat_totals:
        print("No expenses to summarise.")
        return

    
    print("\n monthly summary by category:")
    for (y,m), categories  in sorted(monthly_cat_totals.items()):
        print(f"\n{y}-{m:02d}:")
        for cat, total in sorted(categories.items()):
            print(f"\n{cat:<12}:${total}")

        month_total = sum(categories.values(), Decimal("0"))
        print(f"{'TOTAL':<12}:${month_total}")
    #the category u spend the most on on a monthly basis
    for (y,m),categories in sorted(monthly_cat_totals.items()):
        Max_cat,Max_total = max(categories.items(),key=lambda item:item[1])
        print(f"\n {y}-{m}: ")
        print(f"\n Max Category--> {Max_cat}:${Max_total}")



# creating annual summary:

def annual_summary(Expenses):
    annual_total = defaultdict(Decimal)
     # group and aggregate:
    for e in Expenses:
         key = (e.date.year)
         annual_total[key] +=e.price

    if not annual_total:
        print("No expenses to summarise")

    else:
        print(f"\n Annual Summary: ")
        
        for y,total in annual_total.items():
            print(f"\n {y}:${total}")


        
        
def weekly_summary(Expenses):
    weekly_total = defaultdict(Decimal)
    weekly_ranges = {}
    # group & aggregate ....
    
    
    for e in Expenses:
        year,week,weekday = e.date.isocalendar()
        key = (year,week)
        
        
        weekly_total[key]+=e.price
         # this works fine except it returns a week number that is simply ununderstandabel 
        # therefore to convert the week number to the range that the week lasts get the start and end date as follows:
        if key not in weekly_ranges:
            start_week_date = e.date-timedelta(days=weekday-1)
            end_week_date = start_week_date+timedelta(days=6)
            weekly_ranges[key]= (start_week_date,end_week_date)


    if not weekly_total:
        print("No expenses to summarise.")
    
    else:
        print(f"\n Weekly Summary: ")
        
        for key,total in sorted(weekly_total.items()): 
            start, end = weekly_ranges[key]
            print(f"\n Week {key[1]}|{start}->{end}: ${total}")



# creating the average: --> daily spend:        
       

    
def average_daily_spending_by_month(Expenses):
    if not Expenses:
        print("No expenses to summarize.")
        return

    # Group expenses by (year, month)
    monthly_expenses = defaultdict(list)
    for e in Expenses:
        key = (e.date.year, e.date.month)
        monthly_expenses[key].append(e)

    print("\nAverage Daily Spending by Month:")

    for (y, m), exps in sorted(monthly_expenses.items()):
        total = sum((e.price for e in exps), Decimal("0"))
        min_date = min(e.date for e in exps)
        max_date = max(e.date for e in exps)
        days = (max_date - min_date).days + 1  # include both start & end
        avg = total / days if days > 0 else Decimal("0")

        print(f"{y}-{m:02d}: ${avg:.2f}/day over {days} days, total ${total}")




# creating the fucntion for the search and filter feature:



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


        match_date = True if not parsed_date else (e.date == parsed_date)

        
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


        
 


        
        

  
# match name creating for word completion:
# Example: "co" returns "coffee"

#def name_queryv2(Expenses,name_query):
    if not name_query:
        match_name = True
    else:
        for e in Expenses:
            if name_query in e.name:
                
                match_name = name_query in e.name.lower()

                

# creating the monthly summary including comapring against budget:

def monthly_summary_Compare_Budget(Expenses,monthly_budget):
    #"""Print total expenses grouped by (year, month)."""
    monthly_totals = defaultdict(Decimal)
    
    # Group and aggregate
    for e in Expenses:
        key = (e.date.year, e.date.month)
        monthly_totals[key] += e.price

    # Print results sorted by date
    if not monthly_totals:
        print("No expenses to summarize.")
        return

    print("\nMonthly Summary:")
    for (y, m), total in sorted(monthly_totals.items()):
        X_of_monthly_budget = ((total-monthly_budget)/(monthly_budget))*100
        reducing_expenditure_amount =(total-monthly_budget)
        print(f"\n{y}-{m:02d}: ${total}")
        print(f"\nMonthly Budget was set to:${monthly_budget}")
        if X_of_monthly_budget>0:
            print(f"\n Your current expenditure (${total}) exceeds your budget by {X_of_monthly_budget:.2f}%.\n Reducing your expenditure by ${reducing_expenditure_amount} will keep you within your budget.")
        else:
            print(f"\n Your expenditure (${total}) is under your budget by {X_of_monthly_budget:.2f}%, keep it up !!")
        




# Quick_glance_report(Expenses,year,month):


    # What all do we want:
    """
    
    1) Quick indicator : Example :  ->October 2025 — Total Spent: $487.32 of $600 budget (81%)
                                    ->✅ On track to stay under budget this month
    
    2) Top spending category: Example: - 💸 Top Category: Food — $192.45 (39% of total)

    3) Month Over Month Change: Example: -> Spending up 23% from September (given that its oct now)

    4) Average Daily Spend (Burn Rate): Example: -> 🔥 Average Daily Spending: $16.24/day (vs $20/day budget target)
     
    
    These 4 should be good starters for now, which later be integrated as widgets for my GUI: LESGOOOOOOOOOOo

    """


    print("\n Quick Glance Reports: ")


def Quick_indicator(Expenses,year,month,monthly_budget):

    
    monthly_totals = defaultdict(Decimal)
    
    # Group and aggregate
    for e in Expenses:
        
        if e.date.year==year and e.date.month ==month:
        
            key = (year,month)
            monthly_totals[key] += e.price

    # Print results sorted by date
    if not monthly_totals:
        print("No expenses in this month for this year to show.")
        

    print("\n This Month:")
    for (y, m), total in sorted(monthly_totals.items()):
        X_of_monthly_budget = ((total)/(monthly_budget))*100  # how much of the budget has been spent alredy
        reducing_expenditure_amount =(total-monthly_budget)

        # m --> month number --> the month name (couple of ways to do this : manually map each month number to month name OR use datetime)
        # for the datetime method create a full datetime object:
        
        month_name = datetime.datetime(y,m,1).strftime("%B") #for full month name!

        print(f"{month_name} {y}-Total Spent: {total:.2f} of ${monthly_budget} budget ({X_of_monthly_budget:.2f}% of the budget has been spent) ")

        if X_of_monthly_budget>100:
            print(f"\n ⚠️ You are outside your budget by ${reducing_expenditure_amount:.2f} ")
            
        else:
            print("\n ✅ On track to stay under budget this month ")
    

def Quick_Top_Category(Expenses,year:int,month:int):
    monthly_cat_totals = defaultdict(lambda: defaultdict(Decimal))
    
    for e in Expenses:
        if (e.date.year ==year and e.date.month ==month):
            key = (e.date.year,e.date.month)
            monthly_cat_totals[key][e.category]+=e.price
    
    if not monthly_cat_totals:
        print("No expenses to report.")
        return

    
    print("\n monthly summary by category:")
    for (y,m), categories  in sorted(monthly_cat_totals.items()):
        
        

        month_total = sum(categories.values(), Decimal("0"))
        
    #the category u spend the most on on a monthly basis
    for (y,m),categories in sorted(monthly_cat_totals.items()):
        Max_cat,Max_total = max(categories.items(),key=lambda item:item[1])
        X_of_total = (Max_total/month_total)*100
        print(f"\n 💸 Top Category: {Max_cat.upper()} --> ${Max_total:.2f} ({X_of_total:.2f}%)")





def Quick_month_over_month_change(Expenses,year,month):

    
    # we need to get the current months total expenses value so for :... $x -->DONE
    # next we need to get the PREVIOUS months total expenses: so $y --> DONE
    # simply calculate %change --> (x-y)/y*100% and then print the appropriate result -->DONE

    monthly_totals = defaultdict(Decimal)
    
    
    for e in Expenses:
        if (e.date.year ==year and e.date.month ==month):
            key = (year,month)
            monthly_totals[key]+=e.price # for each expense then grouping and aggregating by same month so getting monthly total expenses

    
    if not monthly_totals:
        print("No expenses to report.")

    for (y,m),total in sorted(monthly_totals.items()):
            current_month_x = total
        
    monthly_totals_Previous_Month = defaultdict(Decimal)
    
    for e in Expenses:
        if (e.date.year ==year and e.date.month ==month-1):
            key = (year,e.date.month)
            monthly_totals_Previous_Month[key]+=e.price

    for (y,m), total_prev in sorted(monthly_totals_Previous_Month.items()):
        prev_month_y = total_prev

    # calculate the % change

    percentage_change_x_y = ((current_month_x-prev_month_y)/prev_month_y)*100
    # debugging
    for key,value in monthly_totals_Previous_Month.items():
        print(f"{key}:{value}")
    for key,value in monthly_totals.items():
        print(f"{key}:{value}")

    if percentage_change_x_y<0:
        print(f"Spending is down this month by {abs(percentage_change_x_y):.2f}%")

    else:
        print(f"Spending is up this month by {(percentage_change_x_y):.2f}%")





def Quick_DailyBurn_rate(Expenses,year,month):


    monthly_expenses = defaultdict(list)
    

    
    for e in Expenses:
        if (e.date.year ==year and e.date.month ==month):
            key = (e.date.year, e.date.month)
            monthly_expenses[key].append(e)

    print("\nAverage Daily Spending/Daily burn rate by Month:")

    for (y, m), exps in sorted(monthly_expenses.items()):
        total__ = sum((e.price for e in exps), Decimal("0"))
        min_date = min(e.date for e in exps)
        max_date = max(e.date for e in exps)
        days = (max_date - min_date).days + 1  # include both start & end
        avg = total__ / days if days > 0 else Decimal("0")

        print(f"{y}-{m:02d}: ${avg:.2f}/day over {days} days, total ${total__:.2f}")



