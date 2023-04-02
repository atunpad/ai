import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import matplotlib.pyplot as plt

# Load data from Excel file
data = pd.read_excel("C:\Abi\data.xlsx")

# Separate features and target
X = data.iloc[:, :-1].values
y = data.iloc[:, -1].values

# Create scatter plot of data
plt.scatter(X, y)
plt.xlabel('X')
plt.ylabel('y')
plt.show()
# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)

# Train regression model
regressor = LinearRegression()
regressor.fit(X_train, y_train)

# Predict target values using testing data
y_pred = regressor.predict(X_test)

# Evaluate performance of model
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print('Mean squared error:', mse)
print('R-squared:', r2)

# Plot actual versus predicted values
plt.scatter(y_test, y_pred)
plt.xlabel('Actual Values')
plt.ylabel('Predicted Values')
plt.show()

plt.scatter(X, y_pred)
plt.xlabel('Actual Values')
plt.ylabel('Predicted Values')
plt.show()