from decimal import Decimal
from datetime import datetime

class Expense:
    def __init__(self, name: str, price: str, date: str, category: str = "misc"):
        # validate/normalize here
        self.name = name.strip()
        self.price = Decimal(price)  # precise for money
        self.date = self._parse_date(date)
        self.category = category.strip().lower()

    def _parse_date(self, date_str: str):
        """Validate & store date in YYYY-MM-DD format."""
        try:
            return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("❌ Date must be in YYYY-MM-DD format.")

    def to_dict(self) -> dict:
        """Convert Expense to a dict (for saving in JSON)."""
        return {
            "name": self.name,
            "price": str(self.price),       # JSON doesn’t support Decimal directly
            "date": self.date.isoformat(),  # "YYYY-MM-DD"
            "category": self.category,
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Rebuild Expense object from a dict (when loading JSON)."""
        return cls(
            name=data["name"],
            price=data["price"],
            date=data["date"],
            category=data.get("category", "misc")
        )

    def __str__(self):
        # expense printing in command line
        return f"{self.name} | ${self.price} | {self.date} | {self.category}"



Expenses = []




from collections import defaultdict
from decimal import Decimal

 # we want:
    # to sort the expenses by month and then aggregate the costs adn then sort of give a per category percentage spent and the actual value as well

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


def save_expense(Expenses, filename="expenses.json"):
    import json
    with open(filename, "w") as f:
        json.dump([e.to_dict() for e in Expenses], f, indent=2)

# Load from JSON
def load_expense(filename="expenses.json"):
    import json
    try:
        with open(filename) as f:
            data = json.load(f)
            return [Expense.from_dict(d) for d in data]
    except FileNotFoundError:
        return []


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
        print("\n 4. Summarise")
        print("\n 5. Exit")


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
            price_ = input("\n price($): ")
            date_ = input("\n date (YYYY-MM-DD): ")
            
            categories = category_show()
            category_choice = input( "Enter category_choice[1-5]: ")
            

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
                Expenses.append(expense)

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
            summary_choice = input("Summary by month ='1'Summary by category and month ='2': ")
            if summary_choice == "1":
                print("\n Your expenses sorted by month are as follows: ")
                monthly_summary(Expenses)
            if summary_choice =="2":
                print("\n Your expenses sorted by month & category are as follows: ")
                monthly_summaryByCat(Expenses)
            
            
        
        
        
        elif user_category_choice=="5":
            # save the expenses before exit:
            save_expense(Expenses)
            
            
            print("bye :(")
            break
    



main()


# Things to Do:
#add summarise by month and category --> DONE
# summarise just by cateogry --> .......
# summarise by week -->.......
# Add an option 
#.--> a feature to give the most spending category wise --> DONE
#..
#...
#....
#.....
#GUI --> Front End







# version control here before i use git next time
# @test
