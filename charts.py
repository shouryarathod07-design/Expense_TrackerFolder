# imports
import matplotlib.pyplot as plt
import numpy as np

#from reports import monthly_summary,monthly_summary_Compare_Budget,monthly_summaryByCat,average_daily_spending_by_month

from collections import defaultdict
from datetime import datetime
from decimal import Decimal
import os
import json


#from models import Expense
# creating a function to grpah my shit out




#create a list containing the months:




def monthly_spending_chart(expenses,year:int):
   

# X axis: month
# Y axis: spending ($)

   # aggregate totals by month for the sepcified year

   monthly_totals = defaultdict(Decimal)
   for e in expenses:
      if e.date.year ==year:
         monthly_totals[e.date.month]+=e.price

   months = sorted(monthly_totals.keys()) #[1,2,3,4....]
   totals = [monthly_totals[m] for m in months] # corressponding totals
   
   #converting the months to nice labels:
   month_labels = [datetime(year,m,1).strftime("%b") for m in months] # list comprehension

     
         # 3. Load budget value
   with open("data/budget.json") as f:
      value = json.load(f)
      monthly_budget = value["monthly_budget"]
     
     
     # 4. Plot
   plt.figure(figsize=(10, 6))
   plt.bar(month_labels, totals, label="Actual Spending")

   # 5. Budget line
   plt.axhline(y=monthly_budget, color="red", linestyle="--", linewidth=2, label="Budget")

   # labelling the graph
   plt.title(f"Monthly Spending vs Budget - {year}")
   plt.xlabel("Month")
   plt.ylabel("Amount ($)")
   plt.legend()
   plt.tight_layout()

   # Optional visual polish
   plt.grid(axis="y",linestyle = "--",alpha=0.6)
   plt.tight_layout()

   # saving the chart
   os.makedirs("data/plots",exist_ok=True)
   output_path = f"data/plots/monthly_spending{year}.png"
   
   try:
        plt.savefig(output_path)
    
        print(f"✅ Chart successfully saved to: {output_path}")
  
         
    
   except Exception as e:
       print(f"❌ Error saving chart: {e}")
      
   




      
   
def Monthly_spending_Category_pie(Expenses, year: int, month: int, threshold_percentage: float = 6.0):
   
   
   
    """
    Create a pie chart showing spending distribution by category for a given month and year.
    Small categories under 'threshold_percentage' are merged into 'Minor Categories'.
    """

    from collections import defaultdict
    from decimal import Decimal
    import matplotlib.pyplot as plt
    from datetime import datetime

    #  Nested dict: { (year, month): {category: total} }
    monthly_cat_totals = defaultdict(lambda: defaultdict(lambda: Decimal("0")))

    # Group data
    for e in Expenses:
        if e.date.year == year and e.date.month == month:
            key = (year, month)
            monthly_cat_totals[key][e.category] += e.price

    # Prepare lists for plotting
    pie_labels, pie_sizes = [], []

    # To show absolute values alongside %
    def autopct_with_values(pct, all_values):
        total = sum(all_values)
        absolute = int(round(pct * total / 100.0))
        return f"${absolute}\n({pct:.1f}%)"

    # Extract categories and totals
    for (y, m), categories in sorted(monthly_cat_totals.items()):
        for cat, total in sorted(categories.items()):
            pie_labels.append(cat)
            pie_sizes.append(float(total))

    # Handle case: no expenses for that month
    if not pie_sizes:
        print(f"⚠️ No expenses recorded for {month}/{year}. Nothing to show.")
        return

    #  Merge small categories (< threshold %) 
    total_spent = sum(pie_sizes)
    minor_total = 0
    merged_labels, merged_sizes = [], []

    for label, size in zip(pie_labels, pie_sizes):
        pct = (size / total_spent) * 100
        if pct < threshold_percentage:
            minor_total += size
        else:
            merged_labels.append(label)
            merged_sizes.append(size)

    if minor_total > 0:
        merged_labels.append(f"Minor Categories (<{threshold_percentage:.0f}%)")
        merged_sizes.append(minor_total)

    # Plot pie chart
    plt.figure(figsize=(8, 8))

    # Assign colors — same palette but last one always grey if present
    colors = plt.cm.tab20.colors  # base palette (20 nice distinct colors)
    if "Minor Categories" in merged_labels[-1]:
        # make a copy so we don’t mutate the global color cycle
        colors = list(colors[:len(merged_labels) - 1]) + ['#d3d3d3']

    plt.pie(
        merged_sizes,
        labels=merged_labels,
        colors=colors[:len(merged_labels)],  # use truncated palette
        autopct=lambda pct: autopct_with_values(pct, merged_sizes),
        startangle=90
    )

    plt.title(f"Category Distribution — {datetime(year, month, 1).strftime('%B %Y')}", y=1.10)
    plt.axis("equal")
    plt.legend(merged_labels, title="Categories", loc="center left", bbox_to_anchor=(-0.1, 0))


    #  Save to file
    file_path = f"data/plots/category_breakdown_{year}_{month:02d}.png"
    plt.savefig(file_path)
    plt.close()  # good practice when generating multiple plots

    print(f"✅Pie chart saved for {month}/{year}! (Threshold: {threshold_percentage}%) → {file_path}")









###
### 
   # sizes: Total expenses in a year per category/total expenses in a year
      
      
      


   # plot





#def Test_(Expenses):
      
   

