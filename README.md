# 💪🥗 AI Workout & Diet Planner

An AI-powered personalized **Indian diet planner** and **workout scheduler** that generates **7-day meal plans** with full recipes and **7-day exercise plans** based on your body metrics, fitness goals, experience level, and dietary preferences.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Web_Framework-black?logo=flask)
![scikit-learn](https://img.shields.io/badge/scikit--learn-ML_Model-orange?logo=scikit-learn)
![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3_70B-green)

---

## ✨ Features

- **ML-Powered Nutrition Prediction** — Random Forest Regressor predicts daily calorie, protein, carbs, and fat requirements.
- **AI-Generated Meal Plans** — Groq API (LLaMA 3.3 70B) creates personalized 7-day Indian meal plans with full recipes.
- **7-Day Workout Plan** — Structured exercise schedules based on experience level (Beginner/Intermediate/Advanced), goal, and location (Home/Gym).
- **Diet Type Support** — Vegetarian, Eggetarian, and Non-Vegetarian options.
- **Health Condition Awareness** — Adapts both diet and workout plans for Diabetes, PCOS, Thyroid, Hypertension.
- **BMI, BMR & TDEE Calculation** — Scientific formulas with transparent display of all metrics.
- **📄 PDF Export** — Download your complete 7-day diet + workout plan as a professional PDF.
- **🛒 Shopping List** — Auto-generated weekly shopping list with deduplicated ingredients.
- **Modern Glassmorphism UI** — Dark theme with neon accents, animated backgrounds, and responsive design.

---

## 🛠️ Tech Stack

| Layer        | Technology                                      |
| ------------ | ----------------------------------------------- |
| **Backend**  | Python, Flask                                   |
| **ML Model** | scikit-learn (Random Forest Regressor)           |
| **AI/LLM**   | Groq API — LLaMA 3.3 70B Versatile              |
| **Frontend** | HTML5, CSS3, JavaScript, Bootstrap 5             |
| **PDF**      | jsPDF (client-side PDF generation)               |
| **Design**   | Google Fonts (Outfit), Glassmorphism, Neon Glow  |

---

## 📂 Project Structure

```
AI-Workout-Diet-Plan/
├── app.py                  # Flask backend — routes, prediction, Groq API, workout integration
├── model_training.py       # Synthetic data generation + Random Forest model training
├── workout_generator.py    # Workout plan generation from workout_data.json
├── workout_data.json       # Exercise database — categorized by goal, location, muscle group
├── nutrition_model.pkl     # Trained ML model (auto-generated if missing)
├── requirements.txt        # Python dependencies
├── .gitignore              # Hides API keys, venv, cache from version control
├── Api-2.txt               # Groq API key (not committed to version control)
├── templates/
│   ├── index.html          # Input form — body metrics, diet & workout preferences
│   └── result.html         # Result page — 7-day diet + workout plan
└── static/
    ├── css/
    │   └── style.css       # Custom styles — dark theme, glassmorphism, exercise cards
    └── js/
        └── script.js       # Form handling, API calls, workout rendering, PDF export, shopping list
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+** installed
- A **Groq API key** (get one at [console.groq.com](https://console.groq.com))

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/DhavalMCA/AI-Workout-Diet-Plan.git
   cd AI-Workout-Diet-Plan
   ```

2. **Create a virtual environment (recommended):**

   ```bash
   python -m venv venv
   venv\Scripts\activate        # Windows
   # source venv/bin/activate   # macOS/Linux
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Add your Groq API key:**

   Create a file named `Api-2.txt` in the project root and paste your Groq API key:

   ```
   gsk_your_api_key_here
   ```

5. **Run the application:**

   ```bash
   python app.py
   ```

6. **Open in browser:**

   ```
   http://localhost:5000
   ```

---

## ⚙️ How It Works

### 1. User Input (Frontend)

The user fills out a form with:

| Field                | Description                                     |
| -------------------- | ----------------------------------------------- |
| Age                  | 15–100 years                                    |
| Gender               | Male / Female                                   |
| Height               | In centimeters                                  |
| Weight               | In kilograms                                    |
| Activity Level       | Sedentary → Very Active (5 levels)              |
| Fitness Goal         | Weight Loss / Maintenance / Weight Gain         |
| Diet Preference      | Vegetarian / Eggetarian / Non-Vegetarian        |
| Health Condition     | None / Diabetes / PCOS / Thyroid / Hypertension |
| Workout Experience   | Beginner / Intermediate / Advanced              |
| Workout Location     | Home / Gym                                      |

### 2. ML Prediction Engine (Backend)

```
User Input → BMI → BMR (Mifflin-St Jeor) → TDEE → Goal Calories → Macros → Meal Plan
```

#### BMR — Mifflin-St Jeor Equation

| Gender | Formula |
|--------|---------|
| **Male** | `BMR = (10 × W) + (6.25 × H) − (5 × A) + 5` |
| **Female** | `BMR = (10 × W) + (6.25 × H) − (5 × A) − 161` |

#### TDEE — Activity Multipliers

| Activity Level | Multiplier |
|----------------|------------|
| Sedentary      | 1.2        |
| Light          | 1.375      |
| Moderate       | 1.55       |
| Very Active    | 1.725      |
| Athlete        | 1.9        |

#### Goal-Based Calorie & Macro Targets

| Goal | Calories | Protein | Fat | Carbs |
|------|----------|---------|-----|-------|
| 🔴 **Weight Loss** | TDEE − 500 | 2.0–2.2 g/kg | 20–25% of cal | Remaining |
| 🟢 **Maintenance** | TDEE | 1.2–1.6 g/kg | 25–30% of cal | Remaining |
| 🔵 **Weight Gain** | TDEE + 300–500 | 1.6–2.0 g/kg | 30–35% of cal | Remaining |

### 3. Workout Plan Generation

The workout plan is generated from `workout_data.json` based on:

- **Experience Level** → Determines weekly schedule (beginner: 4 days, intermediate: 5, advanced: 6)
- **Goal** → Selects exercise pool (weight loss: HIIT/cardio focus, muscle gain: strength focus)
- **Location** → Home (bodyweight) or Gym (equipment-based) exercises
- **Health Condition** → Reduces intensity (fewer sets, longer rest) for medical conditions
- **BMI** → Additional adjustments for underweight/obese users

Each exercise includes: name, sets, reps/duration, rest time, and target muscle group.

### 4. AI Meal Plan Generation (Groq API)

The predicted nutritional values are sent to **Groq's LLaMA 3.3 70B** model to generate a 7-day meal plan with full Indian recipes.

### 5. Result Display

The result page renders:
- **⚠️ Medical Disclaimer**
- **BMI, BMR, TDEE & daily macro targets** (calories, protein, carbs, fat)
- **7-day tabbed meal plan** with recipe cards (ingredients + cooking steps)
- **7-day tabbed workout plan** with exercise cards (sets, reps, rest, target muscle)
- **📄 Download PDF** — Combined diet + workout plan export
- **🛒 Shopping List** — Weekly ingredients with deduplication

---

## 🤖 Model Details

| Parameter            | Value                          |
| -------------------- | ------------------------------ |
| Algorithm            | Random Forest Regressor        |
| Estimators           | 200 trees                      |
| Max Depth            | 10                             |
| Training Samples     | 6,000 (synthetic)              |
| Features             | Age, Gender, Height, Weight, BMI, Activity Level, Goal |
| Targets              | Calories, Protein, Carbs, Fat  |
| BMR Formula          | Mifflin-St Jeor Equation       |

---

## 📡 API Endpoints

| Method | Endpoint    | Description                                  |
| ------ | ----------- | -------------------------------------------- |
| GET    | `/`         | Serves the input form page                   |
| GET    | `/result`   | Serves the result page                       |
| POST   | `/predict`  | Accepts user data (JSON), returns combined plan |

### POST `/predict` — Request Body

```json
{
  "age": 25,
  "gender": 1,
  "height": 170,
  "weight": 70,
  "activity_level": 2,
  "fitness_goal": 1,
  "diet_type": "Vegetarian",
  "health_condition": "None",
  "workout_experience": "intermediate",
  "workout_location": "gym"
}
```

### POST `/predict` — Response

```json
{
  "success": true,
  "metrics": {
    "bmi": 24.2,
    "bmr": 1680,
    "tdee": 2604,
    "calories": 2200,
    "protein": 98,
    "carbs": 275,
    "fat": 70
  },
  "diet_plan": { "Day1": { "..." }, "..." },
  "workout_plan": {
    "Day1": {
      "label": "Push Day",
      "is_rest_day": false,
      "exercises": [
        {
          "name": "Bench Press",
          "sets": 3,
          "reps": "10",
          "duration": "",
          "rest": "90s",
          "target_muscle": "Chest"
        }
      ],
      "notes": ""
    },
    "Day4": {
      "label": "Rest Day",
      "is_rest_day": true,
      "exercises": [],
      "notes": "Focus on recovery, stretching, and hydration."
    }
  },
  "diet_type": "Vegetarian",
  "disease": "None",
  "workout_experience": "intermediate",
  "workout_location": "gym"
}
```

---

## 🎨 UI Design

- **Theme:** Dark mode (`#0f172a` base) with animated gradient background
- **Style:** Glassmorphism with `backdrop-filter: blur(16px)`
- **Font:** [Outfit](https://fonts.google.com/specimen/Outfit) from Google Fonts
- **Effects:** Neon text glow, hover animations, smooth transitions
- **Responsive:** Full Bootstrap 5 grid with mobile-optimized layouts

---

## 📋 Dependencies

```
Flask
scikit-learn
pandas
numpy
groq
```

Install all with:

```bash
pip install -r requirements.txt
```

---

## ⚠️ Disclaimer

This application generates diet and workout plans using AI and machine learning. It is developed as part of an **academic (MTech) project** and is intended for **educational use only**. The plans are AI-generated and should **not** be considered medical, nutritional, or fitness advice. Please consult a qualified healthcare professional before making dietary or exercise changes.

---

## ⚠️ Important Notes

- The `Api-2.txt` file containing your Groq API key should **never** be committed to version control — it's in `.gitignore`.
- The ML model (`nutrition_model.pkl`) is auto-trained on first run if not found.
- Workout plans are generated offline from `workout_data.json` — no extra API calls needed.
- AI-generated meal plans are for **informational purposes only**.

---

## 👤 Author

**Sarswati**

---

## 📄 License

This project is for educational and personal use.
