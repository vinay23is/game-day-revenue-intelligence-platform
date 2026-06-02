# Model Metrics Report

## Attendance Prediction Models

| Model | MAE | RMSE | R² | MAPE |
|-------|-----|------|----|------|
| LinearRegression | 566 | 714 | 0.7810 | 3.29% |
| RandomForest | 597 | 745 | 0.7619 | 3.47% |
| GradientBoosting | 563 | 717 | 0.7797 | 3.28% |

**Best Model:** LinearRegression  
**Test Season:** 2023  
**Train/Test Split:** Time-based (earlier seasons for training)  


## Revenue Prediction Models

| Model | MAE | RMSE | R² | MAPE |
|-------|-----|------|----|------|
| LinearRegression | $23,294 | $29,296 | 0.9933 | 0.61% |
| RandomForest | $29,937 | $37,641 | 0.9889 | 0.78% |
| GradientBoosting | $25,771 | $32,430 | 0.9918 | 0.68% |

**Best Model:** LinearRegression  
**Revenue Target:** total_game_day_revenue (ticket + concessions + merchandise)  

