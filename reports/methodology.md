# Methodology

## 1. Target definition

The target is customer churn. A value of 1 means the customer churned; 0 means the customer stayed.

## 2. Split strategy

The dataset is split into train and test sets using stratification so that the churn share remains approximately comparable between the two samples.

The test set is kept untouched until final evaluation.

## 3. Preprocessing

Numeric variables are imputed and scaled for Logistic Regression.

Categorical variables are imputed and one-hot encoded.

Preprocessing is inside sklearn Pipelines and ColumnTransformers. This means transformations are fitted only on the training sample.

## 4. Models

### Logistic Regression

Used as the interpretable baseline. It gives a useful reference point and makes it possible to inspect the direction and magnitude of encoded-feature coefficients.

### Tree-based model

A Random Forest model is used as a nonlinear benchmark. It can capture interactions and nonlinear relationships that a linear model may miss.

The purpose is not to pick the most complex model available. The purpose is to determine whether additional model complexity improves useful ranking of churn risk.

## 5. Metrics

The project reports:

- ROC-AUC
- PR-AUC
- precision
- recall
- F1
- confusion matrix

Accuracy is not treated as the primary metric because the churn class is smaller than the non-churn class.

## 6. Threshold selection

The default 0.5 threshold is not assumed to be optimal.

A threshold table is evaluated to show the trade-off between:
- precision;
- recall;
- number of customers contacted;
- number of churners captured.

This makes the model output interpretable as a retention prioritization tool.

## 7. Feature interpretation

Permutation importance is calculated on the untouched test set using PR-AUC as the scoring metric. This keeps interpretation at the original customer-feature level and avoids presenting one-hot encoded categories as if they were independent business variables.

Feature importance is treated as an association with model performance, not as a causal explanation of churn.

## 8. Risk ranking

Customers are also ranked by predicted churn probability.

For a retention campaign, a top-risk segment can be more useful than a binary prediction. The analysis therefore measures how much of the actual churn population is found inside the highest-risk customers.

## 9. Limitations

This dataset is observational and historical. A churn prediction model identifies customers associated with higher churn risk; it does not prove that contacting a customer will prevent churn.

The next step in a real product setting would be a retention experiment comparing an intervention group with a control group.
