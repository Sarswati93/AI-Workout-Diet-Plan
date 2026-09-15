import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import pickle

# =========================================
# SYNTHETIC DATA GENERATION
# =========================================
def generate_data(num_samples=5000):
    np.random.seed(42)

    gender = np.random.choice([0, 1], size=num_samples)
    age = np.random.randint(18, 65, size=num_samples)
    height_cm = np.random.randint(150, 195, size=num_samples)

    weight_kg = (height_cm - 100) * np.random.uniform(0.8, 1.25, size=num_samples)
    weight_kg = np.clip(weight_kg, 45, 140)

    bmi = weight_kg / ((height_cm / 100) ** 2)

    activity_level = np.random.choice([0, 1, 2, 3, 4], size=num_samples)
    activity_multipliers = {0: 1.2, 1: 1.375, 2: 1.55, 3: 1.725, 4: 1.9}

    goal = np.random.choice([0, 1, 2], size=num_samples)

    calories = []
    protein = []
    carbs = []
    fat = []

    for i in range(num_samples):

        # Mifflin-St Jeor BMR
        if gender[i] == 1:
            bmr = (10 * weight_kg[i]) + (6.25 * height_cm[i]) - (5 * age[i]) + 5
        else:
            bmr = (10 * weight_kg[i]) + (6.25 * height_cm[i]) - (5 * age[i]) - 161

        tdee = bmr * activity_multipliers[activity_level[i]]

        # =============================================
        # GOAL-BASED CALORIE & MACRO CALCULATION
        # =============================================

        # 🔴 Weight Loss (goal == 0)
        if goal[i] == 0:
            target_cals = tdee - 500
            protein_mult = np.random.uniform(2.0, 2.2)  # 2.0–2.2 g/kg
            fat_pct = np.random.uniform(0.20, 0.25)      # 20–25% of calories

        # 🟢 Maintenance (goal == 1)
        elif goal[i] == 1:
            target_cals = tdee
            protein_mult = np.random.uniform(1.2, 1.6)  # 1.2–1.6 g/kg
            fat_pct = np.random.uniform(0.25, 0.30)      # 25–30% of calories

        # 🔵 Weight Gain (goal == 2)
        else:
            target_cals = tdee + np.random.uniform(300, 500)
            protein_mult = np.random.uniform(1.6, 2.0)  # 1.6–2.0 g/kg
            fat_pct = np.random.uniform(0.30, 0.35)      # 30–35% of calories

        # =============================================
        # BMI-BASED OVERRIDES
        # =============================================
        # Underweight + Gain → higher fat & protein
        if bmi[i] < 18.5 and goal[i] == 2:
            fat_pct = 0.35
            protein_mult = 2.0

        # Overweight + Loss → leaner split
        if bmi[i] > 25 and goal[i] == 0:
            protein_mult = 2.2
            fat_pct = 0.20

        # =============================================
        # AGE-BASED ADJUSTMENTS (Age > 40)
        # =============================================
        if age[i] > 40:
            protein_mult *= 1.05   # Increase protein by 5%
            # Carbs will be reduced by 10% below

        target_cals = max(1300, target_cals)

        # =============================================
        # MACRO CONVERSION (g)
        # =============================================
        protein_g = protein_mult * weight_kg[i]
        fat_g = (target_cals * fat_pct) / 9

        # Carbs = remaining calories
        remaining_cals = target_cals - ((protein_g * 4) + (fat_g * 9))
        carbs_g = remaining_cals / 4

        # Age > 40: reduce carbs by 10%
        if age[i] > 40:
            carbs_g *= 0.90

        calories.append(round(target_cals))
        protein.append(round(protein_g))
        carbs.append(round(carbs_g))
        fat.append(round(fat_g))

    df = pd.DataFrame({
        'Age': age,
        'Gender': gender,
        'Height': height_cm,
        'Weight': weight_kg,
        'BMI': bmi,
        'ActivityLevel': activity_level,
        'Goal': goal,
        'Calories': calories,
        'Protein': protein,
        'Carbs': carbs,
        'Fat': fat
    })

    return df

# =========================================
# TRAIN MODEL
# =========================================
def train_model():
    print("Generating scientific synthetic data...")

    df = generate_data(6000)

    X = df[['Age', 'Gender', 'Height', 'Weight', 'BMI', 'ActivityLevel', 'Goal']]
    y = df[['Calories', 'Protein', 'Carbs', 'Fat']]

    print("Training Random Forest Regressor...")

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=10,
        random_state=42
    )

    model.fit(X, y)

    print("Saving model...")

    with open('nutrition_model.pkl', 'wb') as f:
        pickle.dump(model, f)

    print("Model training complete!")

if __name__ == "__main__":
    train_model()