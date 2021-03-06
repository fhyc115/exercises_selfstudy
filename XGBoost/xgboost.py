# -*- coding: utf-8 -*-
"""XGBoost.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1VmP8zAkgrVPS7MgUXbhPQcepARg6euQZ

Statquest with Josh Starmer
- XGBoost

Exceptionally useful ML method when you don't want to sacrifice ability to correctly classify observations but still want a model that is fairly easy to understand and interpret
"""

pip install xgboost

import pandas as pd # load and manipulate dat and for one-hot encoding
import numpy as np # calc mean and std dev
import xgboost as xgb # xgb
from sklearn.model_selection import train_test_split #split data into train and test set
from sklearn.metrics import balanced_accuracy_score, roc_auc_score, make_scorer #for scoring during
from sklearn.model_selection import GridSearchCV # cross validation
from sklearn.metrics import confusion_matrix #creates confusion matrix
from sklearn.metrics import plot_confusion_matrix #draws confusion matrix

"""Load dataset from IBM Base Samples (Telco Churn Dataset)."""

from google.colab import files
uploaded = files.upload()

df = pd.read_csv('Telco_customer_churn.csv')

df.head()

"""Last few columns regarding churn are from people that left Telco, don't want to use this data in our prediction.
- no one's going to do the exit interview before leaving the company
- these columns will give us perfect predictive ability, so drop them
"""

df.drop(['Churn Label', 'Churn Score', 'CLTV', 'Churn Reason'], axis = 1, inplace = True) #axis = 0 to remove rows, 1 to remove columns
df.head()

"""Some columns only contain a single value, and will not be useful for classification"""

df['Count'].unique()

df['Country'].unique()

df['State'].unique()

"""City contains abunch of city names, so will leave it in"""

df['City'].unique()

"""Will also remove `CustomerID` b/c diff value for every single person. 
- Also remove Lat Long b/c already ahve latitude and longitude
"""

df.drop(['CustomerID', 'Count', 'Country', 'State', 'Lat Long'], axis = 1, inplace = True)
df.head()

"""Although Ok to have whitespace in city names for XGBoost and classification, we can't have whitespace if we want to draw a tree. So take care of it by replacing whitespace with underscore.
- can easily remove whitespaces from all values, not just city names, but will wait until we have identified missing values
"""

df['City'].replace(' ', '_', regex = True, inplace = True)
df.head()

df['City'].unique()[0:10]

"""Eliminate whitespace in the column names, so replace it with underscores"""

df.columns = df.columns.str.replace(' ', '_')
df.head()

"""Removed all model that won't help us create an effective XGB model and reformatted the column name and city names so we can draw a tree. Now ready to identify and deal with Missing Data

# Missing Data Part 1: Identifying Missing data
unfortunately, biggest part of any data analysis project is making sure that the data are correctly formatted and fixing it when it's not. First part of process is identifying Missing data.

Missing data is simply blank space, or a surrogate value like NA, that indicates we failed to collect data for one of the features. 

One thing that is relatively unique about XGBoost is that it has default behavior for missing data. SO all we have to do is identify missing values and make sure they are set to 0.
- author of XGBoost has said even when you code something with 0 and use 0 to mean missing data, XGBoost still does a great job. It doesn't interfere with how it performs

First see what type of data is in each column
"""

df.dtypes

"""A lot of object columns, is ok, b/c saw a lot of text responses. Verify we are getting what we expect"""

df['Phone_Service'].unique()

"""So `Phone_Service` only contains `Yes` and `No`. In practice, check every other column. Here we focus on 1 column that could be a problem: `Total_Charges`"""

df['City'].unique()

df['Zip_Code'].unique()

df['Latitude'].unique()

df['Longitude'].unique()

df['Gender'].unique()

df['Senior_Citizen'].unique()

df['Partner'].unique()

df['Dependents'].unique()

df['Tenure_Months'].unique()

df['Multiple_Lines'].unique()

df['Internet_Service'].unique()

df['Online_Security'].unique()

df['Online_Backup'].unique()

df['Device_Protection'].unique()

df['Tech_Support'].unique()

df['Streaming_TV'].unique()

df['Streaming_Movies'].unique()

df['Contract'].unique()

df['Paperless_Billing'].unique()

df['Payment_Method'].unique()

df['Monthly_Charges'].unique()

df['Churn_Value'].unique()

""" Here we focus on 1 column that could be a problem: Total_Charges"""

df['Total_Charges'].unique()

"""Too many values to print "...". Try to convert to numeric, we get error.
- unable to parse string " " at position 2234
- tells us there are blank spaces in this column

# Missing Data Part 2: Dealing with Missing Data, XGBoost Style
One thing that is relatively unique about XGBoost is that it determines default behavior for missing data. So all we have to do is identify missing values and make sure they are set to 0.

However before we do that, let's see how many rows are missing data. If it's a lot, then we might have a problem on our hands that is bigger than XGBoost can deal with on its own. If it's not many then we can just set them to 0
"""

len(df.loc[df['Total_Charges'] == ' '])

"""Only 11 rows having missing data, let's look at them"""

df.loc[df['Total_Charges'] == ' ']

"""See all 11 with " " have just signed up, b/c Tenure_Months is 0. THese people also all have Churn_Value = 0 b/c they just signed up. 
- have few choices, can set Total_Charges = 0 for these 11 people or can remove them.
- in this example, we set to 0
"""

# rows = ' ' and column = Total_charges set values = 0
df.loc[(df['Total_Charges'] == ' '), 'Total_Charges'] = 0

df.loc[df['Tenure_Months'] == 0]

"""Verified df contains 0s instead of ' ' for missing values. **NOTE: Total_Charges** still has the `object` data type. No good because XGBoost only allows `int`, `float`, or `boolean` data types. Can fix this by converting it with `to_numeric()`"""

df['Total_Charges'] = pd.to_numeric(df['Total_Charges'])
df.dtypes

"""Now that we've dealt with missing data, can replace all other whitespaces in all of the columns with underscores. **NOTE**: only doing this so we can draw picture of one of the XGBoost Trees"""

# doing it data frame wide
df.replace(' ', '_', regex = True, inplace = True)
df.head()

"""# Format Data Part 1: Split Data into dependent and independent variables
two parts:
1. columns of data that we will use to make classifications
2. column of data we want to predict (Churn value)

use conventional notation of X to represent columns of data that we will use to make classifications and y to represent thing we want to predict. 

reason we deal with missing data before splitting into X and y is that if we remove rows splitting after ensures that each row in X correctly corresponds with the appropriate value in y.

**NOTE:** using `copy()` to copy the data by value. By default, pandas uses copy by reference. Using `copy()` ensures that the original data `df_no_missing` is not modified when we modify X or y. In other words, if we make a mistake when we are formatting the columns for classification trees, we can just re-copy `df_no_missing`, rather than having to reload the original data and remove the missing values etc.
"""

X = df.drop('Churn_Value', axis = 1).copy()
X.head()

y = df['Churn_Value'].copy()
y.head()

"""Now to format X so it's suitable for XGBoost

#Format the Data Part 2: One-Hot Encoding
Now split into X and y, take closer look at variables in X.
"""

X.dtypes

"""All object type columns need to be inspected to make sure they only contain reasonable values, and most, if not all of them, will need to change. B/c, while XGBoost natively supports continuous data, like Monthly_Charges and Total_Charges, it doesn't natively support categorical data like Phone_Service, which contains 2 different categories. Thus in order to use categorical data with XGBoost, have to use trick that converts column of categorical data into multiple columns of binary values. **One-Hot Encoding**

Treating like continuous data: 1, 2, 3, 4
- would assume 4 is more similar to 3 than it is to 1 or 2. XGBoost Tree more likely to cluster people with 4s and 3s than with 1s.

Treat like categorical data: each one as separate category

Many different ways to do One-Hot Encoding. Two more popular ways: `ColumnTransformer()` (from scikit-learn) and `get_dummies()` (from pandas) and both have pros and cons.
- `ColumnTransformer()` has a very cool feature where it creates persistent function that can validate data that you can get in the future. 
- Downside is that it turns yoru data into an array and loses all of the column names, making it harder to verify that your usage of `ColumnTransformer()`
- In contrast `get_dummies()` leaves your data in a dataframe and retains column names, making it much easier to verify that it worked as intended.
- however doesnt have the persistent behavior that `ColumnTransformer()` has. 
- We use `get_dummies()` for the sake of learning, but once comfortable with OHE, encourage you to use `ColumnTransformer()`
"""

pd.get_dummies(X, columns = ['Payment_Method']).head()

"""**NOTE**: in a real situation, should verify all of these columns contain accepted categories. """

X_encoded = pd.get_dummies(X, columns = ['City', 
                                         'Gender', 
                                         'Senior_Citizen', 
                                         'Partner', 
                                         'Dependents', 
                                         'Phone_Service',
                                         'Multiple_Lines',
                                         'Internet_Service',
                                         'Online_Security',
                                         'Online_Backup',
                                         'Device_Protection',
                                         'Tech_Support',
                                         'Streaming_TV',
                                         'Streaming_Movies',
                                         'Contract',
                                         'Paperless_Billing',
                                         'Payment_Method'])
X_encoded.head()

"""Verify y only contains 1s and 0s with unique()"""

y.unique()

"""Done formatting

XGBoost uses sparse matrices, only keeps track of the 1s, doesn't allocate memory for the 0s (memory efficient)

#Build a Preliminary XGBoost Model

split into train and test. observe data is imbalanced by dividing the number of people who left the company, where y =1 by total number of people in the dataset
"""

sum(y) / len(y)

"""Only 26.5% of people in dataset left company. B/C of this when we split the data into training and testing, will split using stratification in order to maintain same % of people who left the company in both the training & testing set."""

X_train, X_test, y_train, y_test = train_test_split(X_encoded, y, random_state = 42, stratify = y)

# see if stratify worked as expected
sum(y_train)/len(y_train)

sum(y_test)/len(y_test)

"""same % of people in both y_train and y_test

**Note:** instead of determining the optimal number of trees with CV, we will use **early stopping** to stop building trees when they no longer improve the situation

Specify binary:logistic -> for classification (logistic regression approach to evaluate how good the XGBoost is at classifying the observations)
- missing = none, default is none. -> telling XGBoost what character we're using to represent missing values.
-  seed = 42, in order to hopefully replicate same result
- XGBClassifier creates the shell in which we're going to create a forest of extreme gradient boosted trees, stored in clf_xgb
- create those trees by using fit
- early_stopping_rounds = 10, build 10 more trees, if none improve predictions, then it'll stop
- using aucpr to evaluate how well predictions are being made
"""

clf_xgb = xgb.XGBClassifier(objective = 'binary:logistic', missing = None, seed = 42)
clf_xgb.fit(X_train, y_train, verbose = True, early_stopping_rounds = 10, eval_metric = 'aucpr', eval_set = [(X_test, y_test)])

"""Only created 45 trees. Now let's see how it performs on testing dataset by running the testing dataset down the model and drawing a confusion matrix"""

plot_confusion_matrix(clf_xgb, X_test, y_test, 
                      values_format = 'd', display_labels = ["Did not leave", "Left"])

"""- 1294 didn't leave, 1178 (91%) correctly classified.
- 467 left, 239 (51%) were correctly classified.
- XGBoost model was not awesome. 
- part of the problem is that our data is imbalanced, which we saw earlier and we see this in the confusion matrix with the top row showing 1262 people didn't default 
- bottom row showing 467 people who did.
- because people leaving costs the money a lot of money, we would like to capture more ofthe people that left. 
- the good news is that XGBoost has a parameter, `scale_pos_weight`, that helps with imbalanced data. 
- let's try to improve predictions using **Cross Validation** to optimize the parameters

# Optimize Parameters using Cross Validation and GridSearch()
XGBoost has a lot of *hyperparameters*, parameters that we have to manually configure and are not determned by XGBoost itself, including `max_depth`, the maximum tree depth, `learning_rate`, the learning rate, or "eta", `gamma`, the parameter that encourages pruning, and `reg_lambda`, the regularization parameter lambda. So let's try to find the optimal values for these hyperparameters in hopes that we can improve the accuracy with the Testing dataset.

**NOTE:** since we have many hyperparameters to optimize, use `GridSearchCV()`. Specify a bunch of potential values for the hyperparameters and `GridSearchCV()` tests all possible combos of the parameters for us.

when data are imbalanced, XGBoost manual says if you care only about overall performance metric (AUC) of your prediction
-  Balance the positive and negative weights via `scale_pos_weight`
- Use AUC for evaluation
**NOTE:** ran GridSearchCV sequentially on subsets of parameter options, rather than all at once in order to optimize parameters in a short period of time.
"""

# ## Round 1
param_grid = {
    'max_depth': [3, 4, 5],
    'learning_rate': [0.1, 0.01, 0.05],
    'gamma': [0, 0.25, 1.0],
    'reg_lambda': [0, 1.0, 10.0],
    'scale_pos_weight': [1, 3, 5] # XG Boost recommends sum(negative instances) / sum(positive instances)
}
# # output: max_depth: 4, learning: 0.1, gamma: 0.25, reg_lambda: 10, scale_pos_weight: 3
# # b/c learning_rate and reg_lambda at the ends of their range, we will continue to explore
# ## Round 2
# # got middle for max_depth so chose it.
# # learning rate got edge, so went in that direction
# # gamma got mid value
# # reg_lambda got right side edge, so explore
# # weight got mid
# param_grid = {
#     'max_depth': [4],
#     'learning_rate': [0.1, 0.5, 1],
#     'gamma': [0.25],
#     'reg_lambda': [10.0, 20, 100],
#     'scale_pos_weight': [3]
# }
# # output: max_depth: 4, learning_rate: 0.1, reg_lambda: 10

# NOTE: to speed up CV, and to further prevent overfitting, only using random subset
# of data (90%) and are only using a random subset of the features (columns) (50%) per tree.
optimal_params = GridSearchCV(
    estimator = xgb.XGBClassifier(objective = 'binary:logistic',
                                  seed = 42,
                                  subsample = 0.9,
                                  colsample_bytree = 0.5),
                              param_grid = param_grid,
                              scoring = 'roc_auc',
                              verbose = 0,
                              n_jobs = 10,
                              cv = 3)
optimal_params.fit(X_train, y_train)
# # only doing 3 fold cv, not a lot

optimal_params

"""after testing all possible combinations of the potential parameter values with CV, see that we should set `gamma` = 0.25, `learn_rate` = 0.1, `max_depth` = 4, `reg_lambda` = 10

# Building, Evaluating, Drawing, and interpreting the Optimized XGBoost Model
"""

clf_xgb = xgb.XGBClassifier(seed = 42,
                            objective = 'binary:logistic',
                            gamma = 0.25,
                            learn_rate = 0.1,
                            max_depth = 4,
                            reg_lambda = 10,
                            scale_pos_weight = 3,
                            subsample = 0.9,
                            colsample_bytree = 0.5)

clf_xgb.fit(X_train,
            y_train,
            verbose = True,
            early_stopping_rounds = 10,
            eval_metric = 'aucpr',
            eval_set = [(X_test, y_test)])

plot_confusion_matrix(clf_xgb,
                      X_test,
                      y_test,
                      values_format = 'd',
                      display_labels = ['Did not leave', 'Left'])

"""See optimized XGBoost model is al ot better at identifying people that left the company. Of 467, 388 (83%) were correctly identified. Before optimization only 239 (51%). However, this improvement was at expense of not beign able to correctly classify as many people that didn't leave. Before optimization, correctly identified 1178 (91%) people that didn't leave. Now we only correctly classify 923 (71.3%). That said this trade off may beb etter for the company because now it can focus resources on the people that leave if that will help them retain them.

Now draw the tree and discuss how to interpret.
"""

# if want to get info, like gain and cover etc, at each node in first tree,
# just build first tree, otherwise we'll get average over all the trees
clf_xgb = xgb.XGBClassifier(seed = 42,
                            objective = 'binary:logistic',
                            gamma = 0.25,
                            learn_rate = 0.1,
                            max_depth = 4,
                            reg_lambda = 10,
                            scale_pos_weight = 3,
                            subsample = 0.9,
                            colsample_bytree = 0.5,
                            n_estimators = 1) ## set to 1 so can get gain, cover etc)
clf_xgb.fit(X_train, y_train)

## now print out weight, gain, cover, etc. for tree
# weight = number of times a feature is used in a branch or root across all trees
# gain = avg gain across all splits that the feature is used in
# cover = avg coverage across all splits a feature is used in
# total_gain = total gain across all splits the feature is used in
# total_cover = total coverage across all splits the feature is used in
# NOTE: since only built 1 tree, gain = total gain and cover = total_cover
bst = clf_xgb.get_booster()
for importance_type in ('weight', 'gain', 'cover', 'total_gain', 'total_cover'):
  print('%s: ' % importance_type, bst.get_score(importance_type = importance_type))

node_params = {'shape': 'box', ## makes nodes fancy
               'style': 'filled, rounded',
               'fillcolor': '#78cbe'}
leaf_params = {'shape': 'box', 
               'style': 'filled',
               'fillcolor': '#e48038'}

# NOTE: num_trees is NOT the number of trees to plot, but specific tree you want to plot
# default value = 0, but getting it just to show it in action since it's counterintuitive
# xgb.to_graph(clf_xgb, num_trees = 0, size = "10,10")
xgb.to_graphviz(clf_xgb, num_trees = 0, size = "10,10",
                condition_node_params = node_params,
                leaf_node_params = leaf_params)

# if you want to save the figure
# graph_data = xgb.to_graphviz(clf_xgb, num_trees = 0, size = "10,10",
#                              condition_node_params = node_params,
#                              leaf_node_params = leaf_params)
# graph_data.view(filename = 'xgboost_tree_customer_churn') ## save as pdf

"""How to interpret the XGBoost Tree. In each node we have:
- variable (column name) and threshold for splitting the observations. E.g. in tree's root, use Contract_Month-to-month to split observations
  - Contract_Month-to-month < 1 go to left, everything else go to right
- each branch either says yes or no and some also say missing
  - yes and no refer to whether the threshold in the node above it is true or not. If not, then no.
  - missing is the default outpion if there is missing data
- leaf tells us the output value for each leaf.

# Conclusion
- loaded data from file
- identified and dealth with missing data
- formatted data for XGBoost using One Hot Encoding
- built XGBoost Model for Classification
- Optimize the XGBoost parameters with CV and GridSearch()
- Built, Drew, interpreted and Evaluated the Optimized XGBoost Model
"""

