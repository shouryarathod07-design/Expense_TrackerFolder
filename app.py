# The main file to run serving as an controller and for the now the entry point for my CLI Loop:

#imports
from decimal import Decimal
from datetime import datetime, date
import json 
from collections import defaultdict
from decimal import Decimal
from charts import monthly_spending_chart, Monthly_spending_Category_pie
from models import Expense
from storage import load_expense,save_expense,save_budget
from reports import monthly_summary,monthly_summaryByCat, annual_summary, weekly_summary , average_daily_spending_by_month, monthly_summary_Compare_Budget, Quick_indicator, Quick_Top_Category, Quick_month_over_month_change,Quick_DailyBurn_rate
from filters import search_Filter
from export import  csv_to_export

# main....
def category_show():
    #print("\n Select a category from the following:")
    #print("\n 1.Food")
    #print("\n 2.Travel")
    #print("\n 3.Entertainment")
    #print("\n 4.Misc")
    #print("\n 5.Clothing")
    #print("\n 6.Others")
    categories = ["Food", "Travel", "Ent", "Misc", "Clothing", "Others"]
    print("\nSelect a category from the following:")
    for i, cat in enumerate(categories, start=1):
        print(f"{i}. {cat}")
    return categories





# integrating with loop:
def main():
    # loading expenses at start:
       ## Load from JSON
    Expenses = load_expense()
    
    while True:
        
        #menu 
        print("\n Expense Tracker")
        print("\n 1. View Expense")
        print("\n 2. Add Expense")
        print("\n 3. Delete Expense")
        print("\n 4. Monthly Summarise")
        print("\n 5. Weekly Summaries")
        print("\n 6. Annual Summaries")
        print("\n 7. Daily Average Spending per month")
        print("\n 8. Search & Filter")
        print("\n 9. Edit Existing Expense")
        print("\n 10. Export To CSV")
        print("\n 11. Set/Edit Monthly Budget")
        print("\n 12. Charts & Graphs")
        print("\n 13. Text Report insights (Quick Glance) ")
        print("\n 14. Exit")


        # user selection
        user_category_choice = input("Select a choice: ")
    
   


        if user_category_choice == "1":
            if not Expenses:
                print("No expenses to view")
                continue

    
            else:
                print("\n Expenses List: ")
                for i, expense in enumerate(Expenses,start=1):
                    print(f"{i}.{expense}")

        
        elif user_category_choice== "2":
    # Name # Price # Date
            
            name_ = input("To add an expense.....\n name: ")
            
            
        
            
            
            # helper function for validation
            def validate_price(value):
                try:
                    price = Decimal(value)
                    if price <= 0:
                        raise ValueError
                    return price
                except:
                     raise ValueError("Price must be a positive number.")
                
            try:
                price_ = validate_price(input("Price: "))
            except ValueError as e:
                print(f"❌ {e}")
                return

            



            current_date_now = date.today()


            date_ = input("\n date (YYYY-MM-DD): ")

            year_for_compare,month_for_compare,day_for_compare = date_.split("-")

            if not(int(year_for_compare)<=current_date_now.year and int(month_for_compare)<=current_date_now.month and int(day_for_compare)<=current_date_now.day):

                raise ValueError("Date cannot be in the future")
            

            
            categories = category_show()
            category_choice = input( "Enter category choice[1-5]: ")
            

            # mapping the numbers to the cateogry and correctly labelling
            if category_choice.isdigit() and 1 <= int(category_choice) <= len(categories):
                category = categories[int(category_choice) - 1]   # map number → category string
            
            else:
                print(" X Invalid category_choice, defaulting to 'Misc'")
                category = "Misc"

            #new_expense = input("Add expense with name: , price: ,date : ,category ")
            #parts = [x.strip() for x in new_expense.split(",")]
            #if len(parts) != 4:
                #print(" Please enter: name, price, date (YYYY-MM-DD), category")
                #continue
            
            #name_, price_, date_, category_ = parts

            try:

                expense = Expense(name_, price_, date_,category)
                Expenses.append(expense)  # Expenses is the empty dict created originally while Expense is the class and expense is a singular expense

                print("Expense has been added!")
            except Exception as e:
                print(f"Error:{e}")


    
        elif user_category_choice== "3":
            
            
            
            if not Expenses:
                print("No expenses to remove.")
            else:
                try:
                    expense_remove = int(input("Select an expense to remove: ").strip())

                    
                    if 1<=expense_remove<=len(Expenses):
                        expense_position = expense_remove-1
                        removed = Expenses.pop(expense_position)
                        print(f"Removed= {removed}")
                    else:
                        print("Invalid task number")
        
                except ValueError: 
                    print("Please enter valid number")
    
        elif user_category_choice=="4":
            
            with open('data/budget.json', 'r') as f:
                value= json.load(f)
                monthly_budget = value["monthly_budget"]
            
            summary_choice = input("Summary by month ='1'Summary by category & month ='2': ")
            if summary_choice == "1":
                print("\n Your expenses sorted by month are as follows: ")
                monthly_summary_Compare_Budget(Expenses,monthly_budget)
            if summary_choice =="2":
                print("\n Your expenses sorted by month & category are as follows: ")
                monthly_summaryByCat(Expenses)

        
            
        elif user_category_choice =="5":
            print("\n Your expenses on a weekly basis are as follows:")
            weekly_summary(Expenses)

        elif user_category_choice =="6":
            print("\n Your expenses per annum are as follows:")
            annual_summary(Expenses)
        
        
        elif user_category_choice =="7":
            print("\n Your average expenses per month are as follows:")
            average_daily_spending_by_month(Expenses)

        
        elif user_category_choice=="8":
            print("\n Search & Filter Options")

            name_query = input("\nEnter name to search (or leave blank): ").strip().lower()

            category_show()
            Category_Choice = input("Enter category number(s), comma separated (or leave blank): ")

            selected_categories = [c.strip() for c in Category_Choice.split(",") if c.strip()] if Category_Choice else []

            categories = ["Food", "Travel", "Ent", "Misc", "Clothing", "Others"]
            if selected_categories:
                selected_category_names = [
                    categories[int(i)-1].lower()
                    for i in selected_categories
                    if i.isdigit() and 1 <= int(i) <= len(categories)
                ]
            else:
                selected_category_names = []


            date_query = input("\n Enter date (YYYY-MM-DD) to filter (or leave blank): ").strip()  #improvement: if not correct date format ask to submit again

            # call function from reports.py to get filtered results

            results_SearchFilter = search_Filter(Expenses,name_query,selected_category_names,date_query)


            if not results_SearchFilter:
                print("No matching expenses found.")
            else:
                print("\n Search Results....")
                for i, each_expense in enumerate(results_SearchFilter,start=1):
                    print(f"\n {i}. {each_expense}")


        elif user_category_choice =="9":
            # Editing an Expense 
            if not Expenses:
                print("No expenses to remove.")
            else:
                try:
                    
                    print("\n Expenses List: ")
                    for i, expense in enumerate(Expenses,start=1):
                        print(f"{i}.{expense}")
                    
                    expense_to_edit =int(input("Type the number of the expense to edit: ").strip()) 


                    
                    if 1<=expense_to_edit<=len(Expenses):
                        expense_position = expense_to_edit-1
                        Editable_expense = Expenses[expense_position]
                        print(f"Editing | {Editable_expense} ")
                        new_name = input(f"\n new name (old name|{Editable_expense.name}): ") or Editable_expense.name
                        new_price = input(f"\n new price($)(old price|{Editable_expense.price}) : ") or Editable_expense.price
                        new_date = input(f"\n Enter new date (YYYY-MM-DD)(old date|{Editable_expense.date}): ") 
                        
                        categories = category_show()
                        new_category_choice = input( "Enter category choice[1-5]: ") 
            

                        # mapping the numbers to the cateogry and correctly labelling
                        if new_category_choice.isdigit() and 1 <= int(new_category_choice) <= len(categories):
                            new_category = categories[int(new_category_choice) - 1]   # map number → category string
            
                        else:
                            print(" X Invalid category_choice, defaulting to 'Misc'")
                            new_category = "Misc"

                        #new_name,new_price,new_date,new_category == 

                        Edited_expense = Expense(new_name,new_price,new_date,new_category)
                        Expenses[expense_position] = Edited_expense

                        # to save on exit
                        save_expense(Expenses)

                    else:
                        print("Invalid task number")
        
                except ValueError: 
                    print("Please enter valid number")
        
        
        elif user_category_choice=="10":
            user_wish = input("Do you wish to proceed by exporting your epxense to csv [(Y/N)] : ").lower()
            if user_wish =="y":
                csv_to_export(Expenses)
            elif user_wish =="n":
                exit



        elif user_category_choice=="11":
            
            print("\n Monthly Budget......")
            
            try:
                monthly_Budget = int(input("\nEnter your monthly budget($): "))
                save_budget(monthly_Budget)
                
            
            except ValueError:
                print("Enter a a whole number budget you wish to stick to for the month.")
                
        
        elif user_category_choice == "12":
            print("\n Charts:")
            print("\n 1. Monthly Spending Overview")
            print("\n 2. Spending By Category Monthly")

            chart_type_user_choice = input("Choose chart number (int): ").strip()

            # CHART 1
            if chart_type_user_choice == "1":
                try:
                    year_to_be_plotted = int(input("Enter the year (e.g. 2025): ").strip())
                    monthly_spending_chart(Expenses, year_to_be_plotted)
                except ValueError:
                    print("⚠️ Invalid year — please enter a 4-digit number.")
                    return

            # CHART(PIE CHART) 2
            elif chart_type_user_choice == "2":
                try:
                    year_selected_input = int(input("Enter the year (e.g. 2025): ").strip())
                    month_selected_input = int(input("Enter the month number (1-12): ").strip())

                    if not (1 <= month_selected_input <= 12):
                        print("Invalid month number. Please enter between 1-12.")
                        return

                    Monthly_spending_Category_pie(Expenses, year_selected_input, month_selected_input)

                except ValueError:
                    print("Invalid input — year and month must be numbers.")
                    return

            else:
                print("Invalid chart choice. Please enter 1 or 2.")

            
            
        elif user_category_choice=="13":
           
            with open("data/budget.json") as f:
                value = json.load(f)
                monthly_budget = value["monthly_budget"]


            print("\n Quick Glance Reports: ")
            print("\n 1. Month overview ")
            print("\n 2. Top Spending Category for a month")
            print("\n 3. Month Over Month Change")
            print("\n 4. Average Daily Spend (Burn Rate)")

            
            user_quickGlance_choice = int(input("Choose a report you wish to view (1-4): ").strip())
            
            if user_quickGlance_choice ==1:
                
                
                year_forReport = int(input("Type the year for the report (ex: 2025): "))
                month_forReport = int(input("Type the month for the report (ex: 2 [for feb]): "))
                
                Quick_indicator(Expenses,year_forReport,month_forReport,monthly_budget)
            

            elif user_quickGlance_choice ==2:
                year_forReport2 = int(input("Type the year for the report (ex: 2025): "))
                month_forReport2 = int(input("Type the month for the report (ex: 2 [for feb]): "))

                Quick_Top_Category(Expenses,year_forReport2,month_forReport2)
            
            
            elif user_quickGlance_choice ==3:
                year_forReport3 = int(input("Type the year for the report (ex: 2025): "))
                month_forReport3 = int(input("Type the month for the report (ex: 2 [for feb]): "))

                Quick_month_over_month_change(Expenses,year_forReport3,month_forReport3)
            

            elif user_quickGlance_choice ==4:
                year_forReport4 = int(input("Type the year for the report (ex: 2025): "))
                month_forReport4 = int(input("Type the month for the report (ex: 2 [for feb]): "))

                Quick_DailyBurn_rate(Expenses,year_forReport4,month_forReport4)




            else:
                print("Invalid choice")
                return




        
        
        
        elif user_category_choice=="14":
                
                # save the expenses before exit:
            save_expense(Expenses)
                
                
            print("bye :(")
            break
        


if __name__ =="__main__":
    main()

























# things to do :
# 1) daily expense/average daily burn rate --> DONE
# 2) search and filter feature --> DONE
# 3 3) Improve the Search and filter feature --> DONE
#4) possible edit an expense --> DONE (Simply refine it so that if no input default to previous input for the updates....) --> DONE
# 5) cjarts/graphs -->  IN Progress -->DONE
# 6) Text report summary --> {I will do this so that: 1)(most spent category for the year,month.)()} --> Integrated in the monthly summary (DONE)
# 7_ Backup/polish --> IN PROGRESS
# 8) **** CSV EXPORT**** --> DONE
# 8) Whole Frontend GUI 
#9) AI OCR reciept scanner (DIGITAL)
# adding a budget per month --> DONE



# Move on to refactoring--> IN PROGRESS









