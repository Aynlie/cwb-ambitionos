// amby.js — AmbitionOS Onboarding Step Machine
// Controls the Amby dialogue flow, branching, and API submission.

'use strict';

// ─────────────────────────────────────────
// STATE
// ─────────────────────────────────────────
const state = {
    name: '',
    user_type: '',
    field: '',
    focus: '',
    needs: []
};

let currentStep = 0;

// ─────────────────────────────────────────
// BRANCH DATA
// ─────────────────────────────────────────
const BRANCH = {
    student: {
        step2: {
            msg: 'Amazing! What field are you in?',
            sub: '',
            choices: ['Technology', 'Business', 'Healthcare', 'Creative Arts', 'Science', 'Law', 'Other'],
            cols: 'two-col'
        },
        step3: {
            msg: 'What are you currently focused on?',
            sub: '',
            choices: [
                'Finishing my degree',
                'Building my portfolio',
                'Applying for opportunities',
                'Preparing for certifications'
            ],
            cols: ''
        },
        step4: {
            choices: [
                'Academic deadlines',
                'Internships and scholarships',
                'Personal projects',
                'Study goals',
                'All of the above'
            ]
        }
    },
    professional: {
        step2: {
            msg: 'What is your current role?',
            sub: '',
            choices: ['Project Manager', 'Developer', 'Designer', 'Analyst', 'Team Lead', 'Other'],
            cols: 'two-col'
        },
        step3: {
            msg: 'What do you need help with?',
            sub: '',
            choices: [
                'Managing project deadlines',
                'Tracking team tasks',
                'Planning career growth',
                'All of the above'
            ],
            cols: ''
        },
        step4: {
            choices: [
                'Project milestones',
                'Change approvals',
                'Team blockers',
                'Gantt timeline',
                'All of the above'
            ]
        }
    },
    career_shifter: {
        step2: {
            msg: 'Where are you shifting to?',
            sub: '',
            choices: ['Tech', 'Business', 'Creative', 'Healthcare', 'Other'],
            cols: 'two-col'
        },
        step3: {
            msg: 'What stage are you at?',
            sub: '',
            choices: [
                'Just exploring',
                'Actively upskilling',
                'Job hunting now',
                'Already transitioning'
            ],
            cols: ''
        },
        step4: {
            choices: [
                'Upskilling goals',
                'Job applications',
                'Certification paths',
                'Networking tasks',
                'All of the above'
            ]
        }
    }
};

// ─────────────────────────────────────────
// STEP NAVIGATION
// ─────────────────────────────────────────
function showStep(n) {
    document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
    const el = document.getElementById(`step-${n}`);
    if (el) el.classList.add('active');
    updateDots(n);
    currentStep = n;
}

function updateDots(n) {
    for (let i = 0; i < 5; i++) {
        const dot = document.getElementById(`dot-${i}`);
        if (!dot) continue;
        dot.classList.toggle('active', i === n);
    }
}

// ─────────────────────────────────────────
// STEP 0 → 1: Name capture
// ─────────────────────────────────────────
function goStep1() {
    const input = document.getElementById('inputName');
    const name = input.value.trim();
    if (!name) {
        input.focus();
        input.style.borderColor = '#ff4757';
        return;
    }
    state.name = name;
    input.style.borderColor = '';
    document.getElementById('greetMsg').textContent = `Nice to meet you, ${name}!`;
    showStep(1);
}

// Enter key support on name input
document.addEventListener('DOMContentLoaded', () => {
    const nameInput = document.getElementById('inputName');
    if (nameInput) {
        nameInput.addEventListener('keydown', e => {
            if (e.key === 'Enter') goStep1();
        });
    }
});

// ─────────────────────────────────────────
// STEP 1: User type selection → build steps 2-4
// ─────────────────────────────────────────
function selectUserType(type, btn) {
    state.user_type = type;

    // Highlight selected
    document.querySelectorAll('#choicesUserType .choice-btn').forEach(b => b.classList.remove('selected'));
    btn.classList.add('selected');

    // Build step 2
    const branch = BRANCH[type];
    buildStep2(branch.step2);
    buildStep3(branch.step3);
    buildStep4(branch.step4);

    // Brief delay for visual feedback, then advance
    setTimeout(() => showStep(2), 320);
}

function buildStep2(data) {
    document.getElementById('step2Msg').textContent = data.msg;
    document.getElementById('step2Sub').textContent = data.sub;
    const container = document.getElementById('choicesField');
    container.className = `choices ${data.cols}`;
    container.innerHTML = data.choices.map(c => `
        <button class="choice-btn" onclick="selectField('${c}', this)">${c}</button>
    `).join('');
}

function buildStep3(data) {
    document.getElementById('step3Msg').textContent = data.msg;
    document.getElementById('step3Sub').textContent = data.sub;
    const container = document.getElementById('choicesFocus');
    container.className = `choices ${data.cols || ''}`;
    container.innerHTML = data.choices.map(c => `
        <button class="choice-btn" onclick="selectFocus('${c}', this)">${c}</button>
    `).join('');
}

function buildStep4(data) {
    const container = document.getElementById('choicesNeeds');
    container.innerHTML = data.choices.map(c => `
        <button class="choice-btn" onclick="toggleNeed('${c}', this)">${c}</button>
    `).join('');
}

// ─────────────────────────────────────────
// STEP 2: Field selection
// ─────────────────────────────────────────
function selectField(value, btn) {
    state.field = value;
    document.querySelectorAll('#choicesField .choice-btn').forEach(b => b.classList.remove('selected'));
    btn.classList.add('selected');
    setTimeout(() => showStep(3), 320);
}

// ─────────────────────────────────────────
// STEP 3: Focus selection
// ─────────────────────────────────────────
function selectFocus(value, btn) {
    state.focus = value;
    document.querySelectorAll('#choicesFocus .choice-btn').forEach(b => b.classList.remove('selected'));
    btn.classList.add('selected');
    setTimeout(() => showStep(4), 320);
}

// ─────────────────────────────────────────
// STEP 4: Needs (multi-select)
// ─────────────────────────────────────────
function toggleNeed(value, btn) {
    btn.classList.toggle('selected');

    if (value === 'All of the above') {
        // Select all siblings too
        const allBtns = document.querySelectorAll('#choicesNeeds .choice-btn');
        const isSelected = btn.classList.contains('selected');
        allBtns.forEach(b => {
            if (isSelected) b.classList.add('selected');
            else b.classList.remove('selected');
        });
        state.needs = isSelected ? ['All of the above'] : [];
    } else {
        // Toggle in array
        const idx = state.needs.indexOf(value);
        if (idx === -1) state.needs.push(value);
        else state.needs.splice(idx, 1);

        // Deselect "All" if individual item changed
        const allBtn = [...document.querySelectorAll('#choicesNeeds .choice-btn')]
            .find(b => b.textContent.includes('All of the above'));
        if (allBtn) allBtn.classList.remove('selected');
        state.needs = state.needs.filter(n => n !== 'All of the above');
    }

    document.getElementById('btnFinish').disabled = state.needs.length === 0;
}

// ─────────────────────────────────────────
// FINISH — submit to backend
// ─────────────────────────────────────────
async function finish() {
    showStep('loading');

    const messages = [
        'Configuring your dashboard...',
        'Setting up your task categories...',
        'Almost there!',
        `Welcome to AmbitionOS, ${state.name}!`
    ];

    let i = 0;
    const msgEl = document.getElementById('loadingMsg');
    const interval = setInterval(() => {
        if (i < messages.length) {
            msgEl.textContent = messages[i++];
        } else {
            clearInterval(interval);
        }
    }, 600);

    try {
        const res = await fetch('/api/onboarding/complete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(state)
        });

        const data = await res.json();

        if (data.status === 'success') {
            setTimeout(() => {
                window.location.href = '/';
            }, 2400);
        } else {
            msgEl.textContent = 'Something went wrong. Please try again.';
            msgEl.style.color = '#ff4757';
        }
    } catch (err) {
        msgEl.textContent = 'Connection error. Check the server.';
        msgEl.style.color = '#ff4757';
        console.error('Onboarding submit error:', err);
    }
}
