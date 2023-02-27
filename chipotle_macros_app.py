# -*- coding: utf-8 -*-
"""
Created on Fri Feb 24 17:35:08 2023

@author: jwbol
"""

import pandas as pd
import numpy as np
from pulp import *
import matplotlib.pyplot as plt
import streamlit as st
import circlify
import random

url = "https://raw.githubusercontent.com/JohnBolger/chipotlemacros/main/chipotle_usa_nutritions_no_drinks_or_kids.csv"
nut_facts = pd.read_csv(url)

st.title('Chipotle Macros Tool')
st.text('''          Enter the macronutrient requirements for your chipotle order along with an item 
        that you must have and an item that you don't want in your order. This app 
        will optimize your order for the least amount of calories and provide you with
        the nutrition facts for your order.''')

# Convert the item names to a list
MenuItems = nut_facts.Item.tolist()
# Convert all of the macro nutrients fields to be dictionaries of the item names
Calories = nut_facts.set_index('Item')['Total Calories (cal)'].to_dict()
TotalFat = nut_facts.set_index('Item')['Total Fats (g)'].to_dict()
SaturatedFat = nut_facts.set_index('Item')['Saturated Fats (g)'].to_dict()
Carbohydrates = nut_facts.set_index('Item')['Carbohydrates (g)'].to_dict()
Sugars = nut_facts.set_index('Item')['Sugar (g)'].to_dict()
Protein = nut_facts.set_index('Item')['Protein (g)'].to_dict()
Sodium = nut_facts.set_index('Item')['Sodium (g)'].to_dict()


prob = LpProblem("Macro Optimization Problem", LpMinimize)

MenuItems_vars = LpVariable.dicts("MenuItems",MenuItems,lowBound=0,
   upBound=2,cat='Integer')


st.sidebar.write('Constraints')

must_have = st.sidebar.selectbox('"Must-have" item', nut_facts['Item'])

dont_want = st.sidebar.selectbox('"Don\'t want" item', nut_facts['Item'])

TotalFat_min = st.sidebar.number_input('Total Fat Min', value=10)
TotalFat_max = st.sidebar.number_input('Total Fat Max', value=70)

CarbsMin = st.sidebar.number_input('Carbohydrates Min', value=50)
CarbsMax = st.sidebar.number_input('Carbohydrates Max', value=260)

ProtienMin = st.sidebar.number_input('Protien Min', value=15)
ProtienMax = st.sidebar.number_input('Protien Max', value=85)





# First entry is the calorie calculation (this is our objective)
prob += lpSum([Calories[i]*MenuItems_vars[i] for i in MenuItems]), "Calories"
# Must-have
prob += MenuItems_vars[must_have] >= 1, "MustHave"
# Dont want
prob += MenuItems_vars[dont_want] <= 0, "DontWant"
# Total Fat between x-y g
prob += lpSum([TotalFat[i]*MenuItems_vars[i] for i in MenuItems]) >= TotalFat_min, "TotalFat_lower"
prob += lpSum([TotalFat[i]*MenuItems_vars[i] for i in MenuItems]) <= TotalFat_max, "TotalFat_upper"
# Carbohydrates between x-y g
prob += lpSum([Carbohydrates[i]*MenuItems_vars[i] for i in MenuItems]) >= CarbsMin, "Carbohydrates_lower"
prob += lpSum([Carbohydrates[i]*MenuItems_vars[i] for i in MenuItems]) <= CarbsMax, "Carbohydrates_upper"
# Protein between x-y g
prob += lpSum([Protein[i]*MenuItems_vars[i] for i in MenuItems]) >= ProtienMin, "Protein_lower"
prob += lpSum([Protein[i]*MenuItems_vars[i] for i in MenuItems]) <= ProtienMax, "Protein_upper"


prob.solve()


# Loop over the constraint set and get the final solution
results = {}

for constraint in prob.constraints:
    s = 0
    for var, coefficient in prob.constraints[constraint].items():
        s += var.varValue * coefficient
    results[prob.constraints[constraint].name.replace('_lower','')
        .replace('_upper','')] = s


objective_function_value = value(prob.objective)

varsdict = {}
for v in prob.variables():
    if v.varValue > 0:
        varsdict[v.name] = v.varValue
df_results = pd.DataFrame([varsdict])


# Create just a figure and only one subplot
fig, ax = plt.subplots(figsize=(15,10))

# Title
ax.set_title('Menu Item')

# Remove axes
ax.axis('off')

circles = circlify.circlify(
    varsdict.values(), 
    show_enclosure=False, 
    target_enclosure=circlify.Circle(x=0, y=0, r=1)
)

# Find axis boundaries
lim = max(
    max(
        abs(circle.x) + circle.r,
        abs(circle.y) + circle.r,
    )
    for circle in circles
)
plt.xlim(-lim, lim)
plt.ylim(-lim, lim)

# list of labels
labels = [i[10:] for i in varsdict.keys()]



# print circles
for circle, label in zip(circles, labels):
    x, y, r = circle
    ax.add_patch(plt.Circle((x, y), r*0.7, alpha=0.9, linewidth=2, facecolor="#%06x" % random.randint(0, 0xFFFFFF), edgecolor="black"))
    plt.annotate(label, (x,y ) ,va='center', ha='center', bbox=dict(facecolor='white', edgecolor='black', boxstyle='round', pad=.5))
    value = circle.ex['datum']
    plt.annotate(value, (x,y-.1 ) ,va='center', ha='center', bbox=dict(facecolor='white', edgecolor='black', boxstyle='round', pad=.5))




# Make list at bottom
quant = [i for i in varsdict.values()]

order = ''
for i in range(0,len(quant)): order += '\n' + str(int(quant[i])) + ' ' + labels[i] + '\n'


# Calcualte nutrition facts
final = nut_facts[['Total Calories (cal)', 'Total Fat Calories (cal)', 'Total Fats (g)',
       'Saturated Fats (g)', 'Non-Saturated Fats (g)', 'Trans Fats (g)',
       'Cholesterol (mg)', 'Sodium (g)', 'Carbohydrates (g)',
       'Dietary Fiber (g)', 'Sugar (g)', 'Protein (g)']]

ind_labels = labels
for i in labels: ind_labels[labels.index(i)] = nut_facts["Item"].to_list().index(i)

# Create array of zeros
nut_matrix = np.zeros([1,12])

# Use matrix operations to fill the matrix with the nutrition facts
for i in range(len(ind_labels)): nut_matrix += np.asarray(final.iloc[ind_labels[i]].to_list()) * quant[i]

# Create dataframe for final nutrition facts

df_order = pd.DataFrame(np.int_(nut_matrix))
df_order.columns = ['Total Calories (cal)', 'Total Fat Calories (cal)', 'Total Fats (g)',
       'Saturated Fats (g)', 'Non-Saturated Fats (g)', 'Trans Fats (g)',
       'Cholesterol (mg)', 'Sodium (g)', 'Carbohydrates (g)',
       'Dietary Fiber (g)', 'Sugar (g)', 'Protein (g)']

# CSS to inject contained in a string
hide_table_row_index = """
            <style>
            thead tr th:first-child {display:none}
            tbody th {display:none}
            </style>
            """
# Inject CSS with Markdown
st.markdown(hide_table_row_index, unsafe_allow_html=True)


st.header("Order: " + order)

st.header("Nutrition Facts:")


col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Calories", str(int(nut_matrix[0,0])))
col2.metric("Protein", str(int(nut_matrix[0,11])) + "g")
col3.metric("Fat", str(int(nut_matrix[0,2])) + "g")
col4.metric("Carbs", str(int(nut_matrix[0,8])) + "g")
col5.metric("Sodium", str(int(nut_matrix[0,7])) + "mg")

st.write("Full:")

st.table(df_order)

