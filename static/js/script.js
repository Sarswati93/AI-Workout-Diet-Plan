document.addEventListener('DOMContentLoaded', () => {

    const dietForm = document.getElementById('dietForm');
    if (dietForm) {
        dietForm.addEventListener('submit', async function (e) {
            e.preventDefault();

            // UI State
            document.getElementById('errorMessage').classList.add('d-none');
            dietForm.classList.add('d-none');
            document.getElementById('loader').classList.remove('d-none');

            // Data
            const data = {
                age: document.getElementById('age').value,
                gender: document.getElementById('gender').value,
                height: document.getElementById('height').value,
                weight: document.getElementById('weight').value,
                activity_level: document.getElementById('activity_level').value,
                fitness_goal: document.getElementById('fitness_goal').value,
                diet_type: document.getElementById('diet_type').value,
                health_condition: document.getElementById('health_condition').value || 'None',
                workout_experience: document.getElementById('workout_experience').value,
                workout_location: document.getElementById('workout_location').value
            };

            try {
                const response = await fetch('/predict', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });

                const result = await response.json();

                if (result.success) {
                    sessionStorage.setItem('dietResult', JSON.stringify(result));
                    window.location.href = '/result';
                } else {
                    throw new Error(result.error || 'Failed to generate plan.');
                }

            } catch (err) {
                document.getElementById('loader').classList.add('d-none');
                dietForm.classList.remove('d-none');
                const errorEl = document.getElementById('errorMessage');
                errorEl.textContent = "Error: " + err.message;
                errorEl.classList.remove('d-none');
            }
        });
    }

    // =========================================
    // RESULT PAGE LOGIC
    // =========================================
    const resultContainer = document.getElementById('resultContainer');
    if (resultContainer) {
        const resultString = sessionStorage.getItem('dietResult');
        if (!resultString) {
            window.location.href = '/';
            return;
        }

        const resultData = JSON.parse(resultString);

        // Populate metrics
        document.getElementById('val-bmi').innerText = resultData.metrics.bmi;
        document.getElementById('val-bmr').innerText = resultData.metrics.bmr + ' kcal';
        document.getElementById('val-tdee').innerText = resultData.metrics.tdee + ' kcal';
        document.getElementById('val-cals').innerText = resultData.metrics.calories + ' kcal';
        document.getElementById('val-pro').innerText = resultData.metrics.protein + ' g';
        document.getElementById('val-car').innerText = resultData.metrics.carbs + ' g';
        document.getElementById('val-fat').innerText = resultData.metrics.fat + ' g';

        // User Info Badges
        const badgesEl = document.getElementById('userInfoBadges');
        if (badgesEl) {
            const dietType = resultData.diet_type || '';
            const disease = resultData.disease || 'None';
            const experience = resultData.workout_experience || 'beginner';
            const location = resultData.workout_location || 'home';

            const dietIcon = dietType === 'Veg' ? '🟢' : dietType === 'Egg' ? '🟡' : '🔴';
            const locIcon = location === 'gym' ? '🏋️' : '🏠';
            badgesEl.innerHTML = `
                <span class="info-badge">${dietIcon} ${dietType} Diet</span>
                ${disease && disease.toLowerCase() !== 'none'
                    ? `<span class="info-badge disease-badge">🏥 ${disease} Friendly Plan</span>`
                    : `<span class="info-badge safe-badge">✅ No Health Restrictions</span>`
                }
                <span class="info-badge" style="background:rgba(168,85,247,0.15);border-color:rgba(168,85,247,0.3);color:#a855f7;">🎯 ${capitalize(experience)}</span>
                <span class="info-badge" style="background:rgba(34,197,94,0.15);border-color:rgba(34,197,94,0.3);color:#22c55e;">${locIcon} ${capitalize(location)} Workout</span>
            `;
        }

        // =========================================
        // 7-DAY DIET PLAN RENDERING
        // =========================================
        const dietPlan = resultData.diet_plan;
        const dayTabs = document.getElementById('dayTabs');
        const dayContents = document.getElementById('dayContents');

        const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

        const mealMeta = {
            'Breakfast': { title: '🌅 Breakfast', icon: '☕' },
            'MidMorningSnack': { title: '🥤 Mid-Morning Snack', icon: '🍎' },
            'Lunch': { title: '🍛 Lunch', icon: '🍽️' },
            'EveningSnack': { title: '🫖 Evening Snack', icon: '🍪' },
            'Dinner': { title: '🌙 Dinner', icon: '🥘' }
        };

        const mealOrder = ['Breakfast', 'MidMorningSnack', 'Lunch', 'EveningSnack', 'Dinner'];

        let dayIndex = 0;
        for (const [dayKey, meals] of Object.entries(dietPlan)) {
            const tab = document.createElement('button');
            tab.className = 'day-tab' + (dayIndex === 0 ? ' active' : '');
            tab.setAttribute('data-day', dayKey);
            tab.innerHTML = `<span class="day-num">Day ${dayIndex + 1}</span><span class="day-name">${dayNames[dayIndex] || ''}</span>`;
            tab.addEventListener('click', () => switchDay(dayKey, 'diet'));
            dayTabs.appendChild(tab);

            const dayDiv = document.createElement('div');
            dayDiv.className = 'day-content' + (dayIndex === 0 ? ' active' : '');
            dayDiv.id = `content-${dayKey}`;

            for (const mealKey of mealOrder) {
                const meal = meals[mealKey];
                if (!meal) continue;
                const meta = mealMeta[mealKey] || { title: mealKey, icon: '🍽️' };
                dayDiv.innerHTML += buildMealCard(meal, meta);
            }

            dayContents.appendChild(dayDiv);
            dayIndex++;
        }

        // =========================================
        // 7-DAY WORKOUT PLAN RENDERING
        // =========================================
        const workoutPlan = resultData.workout_plan;
        if (workoutPlan) {
            const wTabs = document.getElementById('workoutDayTabs');
            const wContents = document.getElementById('workoutDayContents');

            let wIndex = 0;
            for (const [dayKey, dayData] of Object.entries(workoutPlan)) {
                const tab = document.createElement('button');
                tab.className = 'day-tab workout-tab' + (wIndex === 0 ? ' active' : '');
                tab.setAttribute('data-day', `w-${dayKey}`);
                tab.innerHTML = `<span class="day-num">Day ${wIndex + 1}</span><span class="day-name">${dayData.label || dayNames[wIndex] || ''}</span>`;
                tab.addEventListener('click', () => switchDay(`w-${dayKey}`, 'workout'));
                wTabs.appendChild(tab);

                const dayDiv = document.createElement('div');
                dayDiv.className = 'day-content' + (wIndex === 0 ? ' active' : '');
                dayDiv.id = `content-w-${dayKey}`;

                if (dayData.is_rest_day) {
                    dayDiv.innerHTML = `
                        <div class="exercise-card rest-card">
                            <div class="exercise-header">
                                <div class="exercise-name">😴 Rest Day</div>
                            </div>
                            <div class="exercise-body">
                                <p class="text-light opacity-75 mb-0">${dayData.notes || 'Focus on recovery, stretching, and hydration.'}</p>
                            </div>
                        </div>
                    `;
                } else {
                    if (dayData.notes) {
                        dayDiv.innerHTML += `<div class="workout-note mb-3"><small class="text-warning">⚠️ ${dayData.notes}</small></div>`;
                    }
                    (dayData.exercises || []).forEach(ex => {
                        dayDiv.innerHTML += buildExerciseCard(ex);
                    });
                }

                wContents.appendChild(dayDiv);
                wIndex++;
            }
        }

        // Show container
        resultContainer.classList.remove('d-none');

        // Shopping list
        buildShoppingList(dietPlan);

        // PDF
        const pdfBtn = document.getElementById('downloadPdfBtn');
        if (pdfBtn) {
            pdfBtn.addEventListener('click', () => generatePDF(resultData));
        }
    }

    // =========================================
    // HELPER: Build Exercise Card HTML
    // =========================================
    function buildExerciseCard(ex) {
        const detail = ex.reps ? `${ex.sets} × ${ex.reps}` : `${ex.sets} × ${ex.duration}`;
        return `
            <div class="exercise-card">
                <div class="exercise-header">
                    <div class="exercise-title-section">
                        <div class="exercise-name">${ex.name}</div>
                        <div class="exercise-detail">${detail}</div>
                    </div>
                    <div class="exercise-badges">
                        <span class="muscle-badge">${ex.target_muscle}</span>
                        ${ex.rest ? `<span class="rest-badge">⏱ ${ex.rest}</span>` : ''}
                    </div>
                </div>
            </div>
        `;
    }

    // =========================================
    // HELPER: Build Meal Card HTML
    // =========================================
    function buildMealCard(meal, meta) {
        const dietBadge = getDietBadge(meal.diet_type);
        const safeBadge = meal.disease_friendly
            ? '<span class="recipe-badge safe">✅ Safe</span>'
            : '<span class="recipe-badge caution">⚠️ Caution</span>';

        const ingredientsList = (meal.ingredients || [])
            .map(ing => `<li>${ing}</li>`)
            .join('');

        const stepsList = (meal.steps || [])
            .map((step, i) => `<li><span class="step-number">${i + 1}</span>${step}</li>`)
            .join('');

        return `
            <div class="recipe-card">
                <div class="recipe-header">
                    <div class="recipe-title-section">
                        <div class="recipe-meal-type">${meta.title}</div>
                        <div class="recipe-name">${meal.name || 'Unnamed Dish'}</div>
                    </div>
                    <div class="recipe-badges">
                        ${dietBadge}
                        ${safeBadge}
                    </div>
                </div>

                <div class="recipe-body">
                    <div class="recipe-section">
                        <div class="recipe-section-title">🧾 Ingredients</div>
                        <ul class="ingredient-list">${ingredientsList || '<li>No ingredients listed</li>'}</ul>
                    </div>
                    <div class="recipe-section">
                        <div class="recipe-section-title">👨‍🍳 How to Cook</div>
                        <ol class="step-list">${stepsList || '<li>No steps listed</li>'}</ol>
                    </div>
                </div>
            </div>
        `;
    }

    function getDietBadge(type) {
        if (type === 'Veg') return '<span class="recipe-badge veg">🟢 Veg</span>';
        if (type === 'Egg') return '<span class="recipe-badge egg">🟡 Egg</span>';
        if (type === 'Non-Veg') return '<span class="recipe-badge nonveg">🔴 Non-Veg</span>';
        return '<span class="recipe-badge">' + (type || 'Unknown') + '</span>';
    }

    function capitalize(str) {
        return str ? str.charAt(0).toUpperCase() + str.slice(1) : '';
    }

    // =========================================
    // DAY TAB SWITCHING
    // =========================================
    function switchDay(dayKey, section) {
        const tabContainer = section === 'workout' ? '#workoutDayTabs' : '#dayTabs';
        const contentContainer = section === 'workout' ? '#workoutDayContents' : '#dayContents';

        document.querySelectorAll(`${tabContainer} .day-tab`).forEach(t => t.classList.remove('active'));
        document.querySelector(`${tabContainer} .day-tab[data-day="${dayKey}"]`).classList.add('active');

        document.querySelectorAll(`${contentContainer} .day-content`).forEach(c => c.classList.remove('active'));
        document.getElementById(`content-${dayKey}`).classList.add('active');
    }

    // =========================================
    // SHOPPING LIST BUILDER
    // =========================================
    function buildShoppingList(dietPlan) {
        const section = document.getElementById('shoppingListSection');
        const content = document.getElementById('shoppingListContent');
        const toggleBtn = document.getElementById('toggleShoppingList');

        if (!section || !content) return;

        const allIngredients = [];
        for (const [dayKey, meals] of Object.entries(dietPlan)) {
            for (const [mealKey, meal] of Object.entries(meals)) {
                if (meal && meal.ingredients) {
                    meal.ingredients.forEach(ing => {
                        const cleaned = ing.trim().toLowerCase();
                        if (cleaned) allIngredients.push(cleaned);
                    });
                }
            }
        }

        const ingredientMap = {};
        allIngredients.forEach(ing => {
            const key = ing.replace(/^[\d\s\/½¼¾⅓⅔]+\s*(cup|cups|tbsp|tsp|g|gm|grams|kg|ml|litre|liter|piece|pieces|nos|no|bunch|pinch|small|medium|large|as needed|to taste)\s*/gi, '').trim();
            const groupKey = key || ing;
            if (!ingredientMap[groupKey]) ingredientMap[groupKey] = [];
            ingredientMap[groupKey].push(ing);
        });

        const sortedKeys = Object.keys(ingredientMap).sort();
        let html = '<div class="shopping-grid">';
        const perColumn = Math.ceil(sortedKeys.length / 3);
        for (let col = 0; col < 3; col++) {
            html += '<div class="shopping-card">';
            const start = col * perColumn;
            const end = Math.min(start + perColumn, sortedKeys.length);
            for (let i = start; i < end; i++) {
                const key = sortedKeys[i];
                const items = ingredientMap[key];
                const display = items[0].charAt(0).toUpperCase() + items[0].slice(1);
                const countNote = items.length > 1 ? ` <small style="color: rgba(56,189,248,0.6);">(×${items.length})</small>` : '';
                html += `<div class="shopping-item">${display}${countNote}</div>`;
            }
            html += '</div>';
        }
        html += '</div>';
        html += `<div class="shopping-count">${sortedKeys.length} unique ingredients across 7 days</div>`;

        content.innerHTML = html;
        section.style.display = 'block';

        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => {
                const isHidden = content.style.display === 'none';
                content.style.display = isHidden ? 'block' : 'none';
                toggleBtn.textContent = isHidden ? 'Hide List' : 'Show List';
            });
        }
    }

    // =========================================
    // PDF GENERATOR (jsPDF)
    // =========================================
    function generatePDF(resultData) {
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF('p', 'mm', 'a4');
        const pageWidth = doc.internal.pageSize.getWidth();
        const margin = 15;
        const maxWidth = pageWidth - margin * 2;
        let y = 20;

        const mealLabels = {
            'Breakfast': '☀ Breakfast',
            'MidMorningSnack': '🥤 Mid-Morning Snack',
            'Lunch': '🍛 Lunch',
            'EveningSnack': '🫖 Evening Snack',
            'Dinner': '🌙 Dinner'
        };
        const mealOrder = ['Breakfast', 'MidMorningSnack', 'Lunch', 'EveningSnack', 'Dinner'];

        function checkPage(needed) {
            if (y + needed > 275) {
                doc.addPage();
                y = 20;
            }
        }

        // Title
        doc.setFontSize(22);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(56, 189, 248);
        doc.text('AI Workout & Diet Planner — 7 Day Plan', pageWidth / 2, y, { align: 'center' });
        y += 10;

        // Disclaimer
        doc.setFontSize(8);
        doc.setFont('helvetica', 'italic');
        doc.setTextColor(180, 150, 50);
        const disclaimer = 'IMPORTANT: This plan was generated by AI. It is NOT a substitute for professional advice. Consult a healthcare provider before making changes to your diet or exercise routine.';
        const disclaimerLines = doc.splitTextToSize(disclaimer, maxWidth);
        doc.text(disclaimerLines, margin, y);
        y += disclaimerLines.length * 4 + 5;

        doc.setDrawColor(56, 189, 248);
        doc.setLineWidth(0.5);
        doc.line(margin, y, pageWidth - margin, y);
        y += 8;

        // Metrics
        doc.setFontSize(14);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(56, 189, 248);
        doc.text('Daily Nutritional Targets', margin, y);
        y += 8;

        doc.setFontSize(11);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(60, 60, 60);
        const m = resultData.metrics;
        doc.text(`BMI: ${m.bmi}  |  BMR: ${m.bmr} kcal  |  TDEE: ${m.tdee} kcal`, margin, y);
        y += 6;
        doc.text(`Calories: ${m.calories} kcal  |  Protein: ${m.protein}g  |  Carbs: ${m.carbs}g  |  Fat: ${m.fat}g`, margin, y);
        y += 10;

        doc.setDrawColor(200, 200, 200);
        doc.setLineWidth(0.3);
        doc.line(margin, y, pageWidth - margin, y);
        y += 8;

        // ====== DIET PLAN ======
        doc.setFontSize(16);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(56, 189, 248);
        doc.text('DIET PLAN', margin, y);
        y += 8;

        let dayIndex = 0;
        for (const [dayKey, meals] of Object.entries(resultData.diet_plan)) {
            checkPage(20);
            doc.setFontSize(14);
            doc.setFont('helvetica', 'bold');
            doc.setTextColor(168, 85, 247);
            doc.text(`Day ${dayIndex + 1}`, margin, y);
            y += 7;

            for (const mealKey of mealOrder) {
                const meal = meals[mealKey];
                if (!meal) continue;
                checkPage(25);

                doc.setFontSize(10);
                doc.setFont('helvetica', 'bold');
                doc.setTextColor(236, 72, 153);
                doc.text(mealLabels[mealKey] || mealKey, margin + 2, y);
                y += 5;

                doc.setFontSize(11);
                doc.setFont('helvetica', 'bold');
                doc.setTextColor(40, 40, 40);
                doc.text(meal.name || 'Unnamed', margin + 4, y);
                y += 5;

                doc.setFontSize(9);
                doc.setFont('helvetica', 'bold');
                doc.setTextColor(56, 189, 248);
                doc.text('Ingredients:', margin + 4, y);
                y += 4;

                doc.setFont('helvetica', 'normal');
                doc.setTextColor(80, 80, 80);
                (meal.ingredients || []).forEach(ing => {
                    checkPage(5);
                    const lines = doc.splitTextToSize(`* ${ing}`, maxWidth - 10);
                    doc.text(lines, margin + 8, y);
                    y += lines.length * 4;
                });
                y += 2;

                doc.setFontSize(9);
                doc.setFont('helvetica', 'bold');
                doc.setTextColor(56, 189, 248);
                doc.text('Steps:', margin + 4, y);
                y += 4;

                doc.setFont('helvetica', 'normal');
                doc.setTextColor(80, 80, 80);
                (meal.steps || []).forEach((step, idx) => {
                    checkPage(5);
                    const lines = doc.splitTextToSize(`${idx + 1}. ${step}`, maxWidth - 10);
                    doc.text(lines, margin + 8, y);
                    y += lines.length * 4;
                });
                y += 3;
            }

            checkPage(5);
            doc.setDrawColor(220, 220, 220);
            doc.setLineWidth(0.2);
            doc.line(margin, y, pageWidth - margin, y);
            y += 6;
            dayIndex++;
        }

        // ====== WORKOUT PLAN ======
        if (resultData.workout_plan) {
            doc.addPage();
            y = 20;
            doc.setFontSize(16);
            doc.setFont('helvetica', 'bold');
            doc.setTextColor(56, 189, 248);
            doc.text('WORKOUT PLAN', margin, y);
            y += 8;

            let wIdx = 0;
            for (const [dayKey, dayData] of Object.entries(resultData.workout_plan)) {
                checkPage(15);
                doc.setFontSize(13);
                doc.setFont('helvetica', 'bold');
                doc.setTextColor(168, 85, 247);
                doc.text(`Day ${wIdx + 1} — ${dayData.label}`, margin, y);
                y += 6;

                if (dayData.is_rest_day) {
                    doc.setFontSize(10);
                    doc.setFont('helvetica', 'italic');
                    doc.setTextColor(100, 100, 100);
                    doc.text(dayData.notes || 'Rest Day — Focus on recovery.', margin + 4, y);
                    y += 8;
                } else {
                    (dayData.exercises || []).forEach(ex => {
                        checkPage(8);
                        doc.setFontSize(10);
                        doc.setFont('helvetica', 'bold');
                        doc.setTextColor(40, 40, 40);
                        const detail = ex.reps ? `${ex.sets} x ${ex.reps}` : `${ex.sets} x ${ex.duration}`;
                        doc.text(`${ex.name}  —  ${detail}  [${ex.target_muscle}]${ex.rest ? '  Rest: ' + ex.rest : ''}`, margin + 4, y);
                        y += 5;
                    });
                    y += 3;
                }

                doc.setDrawColor(220, 220, 220);
                doc.setLineWidth(0.2);
                doc.line(margin, y, pageWidth - margin, y);
                y += 5;
                wIdx++;
            }
        }

        // Footer
        checkPage(10);
        doc.setFontSize(8);
        doc.setFont('helvetica', 'italic');
        doc.setTextColor(150, 150, 150);
        doc.text('Generated by AI Workout & Diet Planner | Educational Purpose Only', pageWidth / 2, 285, { align: 'center' });

        doc.save('AI_Workout_Diet_Plan_7Day.pdf');
    }
});
