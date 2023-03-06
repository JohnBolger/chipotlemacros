# -*- coding: utf-8 -*-
"""
Created on Fri Feb 24 17:35:08 2023

@author: jwbol
"""

import pandas as pd
import numpy as np
from pulp import *
import matplotlib.pyplot as plt
import plotly.express as px
import streamlit as st
import random
from PIL import Image


url = "https://raw.githubusercontent.com/JohnBolger/chipotlemacros/main/chipotle_usa_nutritions_no_drinks_or_kids.csv"
nut_facts = pd.read_csv(url)

st.title('Chipotle Macros Tool')
st.text('''          Enter the macronutrient requirements for your chipotle order along with items 
        that you must have and items that you don't want in your order. This app 
        will optimize your order for the least amount of calories and provide you with
        the full nutrition facts.''')

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

want = st.sidebar.multiselect('Select up to 3 items that you want in your order:', nut_facts['Item'], max_selections=3)

no_want = st.sidebar.multiselect('Select up to 3 items that you don\'t want in your order:', nut_facts['Item'], max_selections=3)

TotalFat_min = st.sidebar.number_input('Total Fat', value=50)

CarbsMin = st.sidebar.number_input('Carbohydrates', value=100)

ProtienMin = st.sidebar.number_input('Protien', value=40)





# First entry is the calorie calculation (this is our objective)
prob += lpSum([Calories[i]*MenuItems_vars[i] for i in MenuItems]), "Calories"
# Yes
if len(want) == 1:
    prob += MenuItems_vars[want[0]]  >= 1, "MustHave1"
if len(want) == 2:
    prob += MenuItems_vars[want[0]]  >= 1, "MustHave1"
    prob += MenuItems_vars[want[1]]  >= 1, "MustHave2"
if len(want) == 3:
    prob += MenuItems_vars[want[0]]  >= 1, "MustHave1"
    prob += MenuItems_vars[want[1]]  >= 1, "MustHave2"
    prob += MenuItems_vars[want[2]]  >= 1, "MustHave3"
    
# No
if len(no_want) == 1:
    prob += MenuItems_vars[no_want[0]] <= 0, "DontWant1"
if len(no_want) == 2:
    prob += MenuItems_vars[no_want[0]] <= 0, "DontWant1"
    prob += MenuItems_vars[no_want[1]] <= 0, "DontWant2"
if len(no_want) == 3:
    prob += MenuItems_vars[no_want[0]] <= 0, "DontWant1"
    prob += MenuItems_vars[no_want[1]] <= 0, "DontWant2"
    prob += MenuItems_vars[no_want[2]] <= 0, "DontWant3"

# Total Fat between x-y g
prob += lpSum([TotalFat[i]*MenuItems_vars[i] for i in MenuItems]) >= TotalFat_min, "TotalFat_lower"
# Carbohydrates between x-y g
prob += lpSum([Carbohydrates[i]*MenuItems_vars[i] for i in MenuItems]) >= CarbsMin, "Carbohydrates_lower"
# Protein between x-y g
prob += lpSum([Protein[i]*MenuItems_vars[i] for i in MenuItems]) >= ProtienMin, "Protein_lower"


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


# list of labels
labels = [i[10:] for i in varsdict.keys()]

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

cals = int(nut_matrix[0,0])
protein = int(nut_matrix[0,11])
fat = int(nut_matrix[0,2])
carbs = int(nut_matrix[0,8])
que = [protein, carbs, fat]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Calories", str(cals))
col2.metric("Protein", str(protein) + "g")
col3.metric("Fat", str(fat) + "g")
col4.metric("Carbs", str(carbs) + "g")

st.header("Order:")

# Pie Chart
fig = px.pie(values = [ProtienMin, CarbsMin, TotalFat_min], names=['Protein', 'Carbs', 'TotalFat_min'], color_discrete_sequence=['#451400', "#A81612", "White"])



col1, col2, col3 = st.columns(3)
col1.write(order)
#col2.metric("Calories", str(cals))
#col2.metric("Protein", str(protein) + "g")
#col2.metric("Fat", str(fat) + "g")
#col2.metric("Carbs", str(carbs) + "g")
col3.image('https://www.google.com/search?q=chipotle&rlz=1C1CHBF_enUS919US919&sxsrf=AJOqlzWjx59SgEja3aXktDVWeqPcRTM95A:1678076032686&source=lnms&tbm=isch&sa=X&ved=2ahUKEwjT_tWuuMb9AhXsFVkFHVSLAQMQ0pQJegQIBhAG&biw=1920&bih=937&dpr=1#imgrc=ZJkz-iWDEddiNM') 

st.sidebar.plotly_chart(fig, use_container_width=True)


st.header("Full Nutrition Facts:")


st.table(df_order)

