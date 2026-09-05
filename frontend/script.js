// Backend Configuration
const API_PORTS = [8000, 8001];
let API_BASE = "";

// Initialize API
async function initializeAPI() {
    for (const port of API_PORTS) {
        const url = `http://127.0.0.1:${port}`;
        try {
            const response = await fetch(`${url}/health`);
            if (response.ok) {
                API_BASE = url;
                console.log(`Connected to backend on ${API_BASE}`);
                return true;
            }
        } catch (e) {
            console.warn(`Backend not found on port ${port}`);
        }
    }
    showError("Could not connect to any backend API (tried ports 8000, 8001). Please ensure the backend is running.");
    loading.classList.add("hidden");
    return false;
}

// Your existing student UUID
const STUDENT_ID = "89c9c522-65c8-4743-99e2-60bc9d181a18";



// DOM Elements


const loading = document.getElementById("loading");
const errorBox = document.getElementById("error");

const studentSection = document.getElementById("student-section");
const progressSection = document.getElementById("progress-section");
const assessmentSection = document.getElementById("assessment-section");
const lessonsSection = document.getElementById("lessons-section");

const studentName = document.getElementById("student-name");
const studentGrade = document.getElementById("student-grade");
const studentLevel = document.getElementById("student-level");
const studentLanguage = document.getElementById("student-language");
const studentGoal = document.getElementById("student-goal");

const progressContainer = document.getElementById("progress-container");
const assessmentContainer = document.getElementById("assessment-container");
const lessonsContainer = document.getElementById("lessons-container");

const lessonForm = document.getElementById("lesson-form");
const generateButton = document.getElementById("generate-button");

const generatedLesson = document.getElementById("generated-lesson");
const lessonTitle = document.getElementById("lesson-title");
const lessonMeta = document.getElementById("lesson-meta");
const objectivesList = document.getElementById("objectives-list");
const segmentsContainer = document.getElementById("segments-container");

// AI Media
const mediaSection = document.getElementById("media-section");
const mediaStatus = document.getElementById("media-status");
const generateMediaButton =
    document.getElementById("generate-media-button");

const visualContainer =
    document.getElementById("visual-container");

const generatedVisual =
    document.getElementById("generated-visual");

const audioContainer =
    document.getElementById("audio-container");

const generatedAudio =
    document.getElementById("generated-audio");

const videoContainer =
    document.getElementById("video-container");

const generatedVideo =
    document.getElementById("generated-video");


// QA Flow Elements
const qaSection = document.getElementById("qa-section");
const questionText = document.getElementById("question-text");
const studentAnswerInput = document.getElementById("student-answer");
const submitAnswerButton = document.getElementById("submit-answer-button");
const evaluationContainer = document.getElementById("evaluation-container");
const evaluationResult = document.getElementById("evaluation-result");
const evaluationFeedback = document.getElementById("evaluation-feedback");
const misconceptionText = document.getElementById("misconception-text");
const nextStepButton = document.getElementById("next-step-button");

// Get Next Teacher Step
async function getTeacherNextStep(lessonId) {
    try {
        const response = await fetch(
            `${API_BASE}/api/lesson/${lessonId}/teacher`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    student_id: STUDENT_ID,
                    difficulty: "beginner" // Should probably be dynamic
                })
            }
        );

        if (!response.ok) {
            throw new Error("Failed to get next teacher step.");
        }

        return await response.json();
    } catch (error) {
        console.error("Error getting next teacher step:", error);
        return null;
    }
}

// Submit Answer
submitAnswerButton.addEventListener("click", async () => {
    const answer = studentAnswerInput.value.trim();
    if (!answer) return;

    const lessonId = currentLesson.lesson_id;
    const concept = currentLesson.segments[0].concept; // Simplified for now
    const question = questionText.textContent;

    try {
        const response = await fetch(`${API_BASE}/api/lesson/evaluate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                lesson_id: lessonId,
                student_id: STUDENT_ID,
                concept: concept,
                question: question,
                student_answer: answer,
                expected_answer: "...", // Need to get this from somewhere
                subject: currentLesson.subject,
                topic: currentLesson.topic
            })
        });

        const result = await response.json();
        displayEvaluation(result);
    } catch (error) {
        console.error("Evaluation error:", error);
        showError("Failed to evaluate answer.");
    }
});

// Display Evaluation
function displayEvaluation(result) {
    evaluationContainer.classList.remove("hidden");
    evaluationResult.textContent = result.correct ? "Correct!" : "Incorrect";
    evaluationFeedback.textContent = result.feedback;
    
    if (result.misconception_description) {
        misconceptionText.textContent = `Misconception: ${result.misconception_description}`;
        misconceptionText.classList.remove("hidden");
    } else {
        misconceptionText.classList.add("hidden");
    }
    
    nextStepButton.classList.remove("hidden");
}

// Next Step
nextStepButton.addEventListener("click", async () => {
    // Logic to move to next step
    evaluationContainer.classList.add("hidden");
    studentAnswerInput.value = "";
    // Fetch next step...
});



// Auth State
let isLoginMode = true;

// Auth UI Elements
const authSection = document.getElementById("auth-section");
const authForm = document.getElementById("auth-form");
const authTitle = document.getElementById("auth-title");
const authButton = document.getElementById("auth-button");
const authToggleText = document.getElementById("auth-toggle-text");
const authToggleButton = document.getElementById("auth-toggle-button");
const authEmailInput = document.getElementById("auth-email");
const authPasswordInput = document.getElementById("auth-password");

// Auth Toggle Listener
authToggleButton.addEventListener("click", () => {
    isLoginMode = !isLoginMode;
    authTitle.textContent = isLoginMode ? "Login" : "Sign Up";
    authButton.textContent = isLoginMode ? "Login" : "Sign Up";
    authToggleText.textContent = isLoginMode ? "Don't have an account?" : "Already have an account?";
    authToggleButton.textContent = isLoginMode ? "Sign Up" : "Login";
});

// Auth Form Listener
authForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    if (!API_BASE) {
        const success = await initializeAPI();
        if (!success) return;
    }

    const email = authEmailInput.value;
    const password = authPasswordInput.value;
    const endpoint = isLoginMode ? "/api/auth/login" : "/api/auth/signup";

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });

        if (!response.ok) {
            throw new Error(isLoginMode ? "Login failed" : "Sign up failed");
        }

        const data = await response.json();
        
        // Handle token storage
        // Assuming response structure: { session: { access_token: "..." } } or similar
        const token = data.session?.access_token || data.access_token;
        if (token) {
            setAuthToken(token);
            alert(isLoginMode ? "Login successful!" : "Sign up successful! Please login.");
            if (isLoginMode) {
                authSection.classList.add("hidden");
                loadDashboard();
            } else {
                isLoginMode = true;
                authToggleButton.click();
            }
        } else {
            throw new Error("No token received");
        }
    } catch (error) {
        console.error("Auth error:", error);
        alert(error.message);
    }
});

function getAuthToken() {
    return localStorage.getItem("auth_token");
}

function setAuthToken(token) {
    localStorage.setItem("auth_token", token);
}

function getAuthHeaders() {
    const token = getAuthToken();
    return {
        "Content-Type": "application/json",
        ...(token ? { "Authorization": `Bearer ${token}` } : {})
    };
}

// Load Dashboard
async function loadDashboard() {
    if (!API_BASE) {
        const success = await initializeAPI();
        if (!success) return;
    }

    try {

        hideError();

        const response = await fetch(
            `${API_BASE}/api/students/${STUDENT_ID}/dashboard`,
            {
                headers: getAuthHeaders()
            }
        );

        if (!response.ok) {
            throw new Error(
                `Dashboard request failed: ${response.status}`
            );
        }


        const data = await response.json();

        displayStudent(data.student);
        displayProgress(data.progress);
        displayAssessments(data.assessments);
        displayLessons(data.lessons);

        loading.classList.add("hidden");

    } catch (error) {

        console.error("Dashboard error:", error);

        loading.classList.add("hidden");

        showError(
            "Unable to load the dashboard. Make sure your FastAPI backend is running."
        );
    }
}



// Display Student


function displayStudent(student) {

    studentName.textContent =
        student.name || "-";

    studentGrade.textContent =
        student.grade || "-";

    studentLevel.textContent =
        student.current_level || "-";

    studentLanguage.textContent =
        student.preferred_language || "-";

    studentGoal.textContent =
        student.learning_goals ||
        "No learning goal specified.";

    studentSection.classList.remove("hidden");
}



// Display Progress


function displayProgress(progress) {

    progressContainer.innerHTML = "";

    if (!progress || progress.length === 0) {

        progressContainer.innerHTML =
            `<div class="empty">
                No learning progress recorded yet.
            </div>`;

        progressSection.classList.remove("hidden");

        return;
    }

    progress.forEach(item => {

        const mastery =
            Number(item.mastery_score ?? 0);

        const safeMastery =
            Math.max(0, Math.min(100, mastery));

        const topic =
            item.topic ||
            item.subject ||
            "Learning Progress";

        const status =
            item.status ||
            "Not specified";

        const strength =
            item.strength ||
            "Not recorded";

        const weakness =
            item.weakness ||
            "Not recorded";

        const card =
            document.createElement("div");

        card.className =
            "progress-card";

        card.innerHTML = `
            <div class="progress-header">
                <h3>${escapeHTML(topic)}</h3>

                <span class="mastery">
                    ${safeMastery}%
                </span>
            </div>

            <div class="progress-bar">
                <div
                    class="progress-fill"
                    style="width: ${safeMastery}%"
                ></div>
            </div>

            <div class="progress-details">
                <span>
                    Status: ${escapeHTML(status)}
                </span>

                <span>
                    Strength: ${escapeHTML(strength)}
                </span>
            </div>

            <div class="progress-details">
                <span>
                    Weakness: ${escapeHTML(weakness)}
                </span>
            </div>
        `;

        progressContainer.appendChild(card);
    });

    progressSection.classList.remove("hidden");
}



// Display Assessments


function displayAssessments(assessments) {

    assessmentContainer.innerHTML = "";

    if (!assessments || assessments.length === 0) {

        assessmentContainer.innerHTML =
            `<div class="empty">
                No assessments completed yet.
            </div>`;

        assessmentSection.classList.remove("hidden");

        return;
    }

    const table =
        document.createElement("table");

    table.className =
        "assessment-table";

    table.innerHTML = `
        <thead>
            <tr>
                <th>Topic</th>
                <th>Score</th>
                <th>Result</th>
                <th>Feedback</th>
            </tr>
        </thead>

        <tbody></tbody>
    `;

    const tbody =
        table.querySelector("tbody");

    assessments.forEach(item => {

        const row =
            document.createElement("tr");

        const score =
            item.score ??
            item.marks ??
            "-";

        const result =
            item.is_correct === true
                ? "Correct"
                : item.is_correct === false
                    ? "Incorrect"
                    : item.result || "-";

        const resultClass =
            result.toLowerCase() === "correct"
                ? "correct"
                : result.toLowerCase() === "incorrect"
                    ? "incorrect"
                    : "";

        row.innerHTML = `
            <td>
                ${escapeHTML(item.topic || "-")}
            </td>

            <td>
                ${escapeHTML(String(score))}
            </td>

            <td class="${resultClass}">
                ${escapeHTML(result)}
            </td>

            <td>
                ${escapeHTML(item.feedback || "-")}
            </td>
        `;

        tbody.appendChild(row);
    });

    assessmentContainer.appendChild(table);

    assessmentSection.classList.remove("hidden");
}



// Global Lesson State
let currentLesson = null;

// Display Previous Lessons
function displayLessons(lessons) {
    lessonsContainer.innerHTML = "";

    if (!lessons || lessons.length === 0) {
        lessonsContainer.innerHTML =
            `<div class="empty">
                No previous lessons yet.
            </div>`;
        lessonsSection.classList.remove("hidden");
        return;
    }

    lessons.forEach(lesson => {
        const card = document.createElement("div");
        card.className = "lesson-card";
        card.innerHTML = `
            <h3>${escapeHTML(lesson.title || "Untitled Lesson")}</h3>
            <div class="lesson-info">
                <span>Subject: ${escapeHTML(lesson.subject || "-")}</span>
                <span>Topic: ${escapeHTML(lesson.topic || "-")}</span>
            </div>
            <button class="start-lesson-button" data-lesson-id="${lesson.id}">Start Lesson</button>
        `;

        card.querySelector(".start-lesson-button").addEventListener("click", () => {
            startLesson(lesson);
        });

        lessonsContainer.appendChild(card);
    });

    lessonsSection.classList.remove("hidden");
}

// Start Lesson Demo
async function startLesson(lesson) {
    // Fetch full lesson state to get segments
    try {
        const response = await fetch(`${API_BASE}/api/lesson/${lesson.id}/state?student_id=${STUDENT_ID}`);
        if (!response.ok) throw new Error("Failed to load lesson state");
        const lessonState = await response.json();
        
        currentLesson = { ...lesson, lesson_id: lesson.id, ...lessonState };
    } catch (e) {
        console.error("Error loading lesson state:", e);
        currentLesson = { ...lesson, lesson_id: lesson.id, segments: [{concept: "Unknown"}] };
    }

    // Hide dashboard sections
    studentSection.classList.add("hidden");
    progressSection.classList.add("hidden");
    assessmentSection.classList.add("hidden");
    lessonsSection.classList.add("hidden");

    // Show QA section
    qaSection.classList.remove("hidden");

    // Get next step
    const step = await getTeacherNextStep(lesson.id);
    if (step && step.question) {
        questionText.textContent = step.question;
    } else {
        questionText.textContent = "Teacher is ready. Please ask a question or await input.";
    }
}




// Generate Personalized Lesson


lessonForm.addEventListener(
    "submit",
    async function(event) {

        event.preventDefault();

        const subject =
            document.getElementById("subject")
                .value
                .trim();

        const topic =
            document.getElementById("topic")
                .value
                .trim();

        const time =
            Number(
                document.getElementById("time").value
            );

        const language =
            document.getElementById("language").value;

        if (!subject || !topic || !time) {

            showError(
                "Please fill in all lesson fields."
            );

            return;
        }

        generateButton.disabled = true;

        generateButton.textContent =
            "Generating lesson...";

        hideError();

        generatedLesson.classList.add("hidden");

        // Hide old media
        mediaSection.classList.add("hidden");

        try {

            // Get actual student information
            const dashboardResponse =
                await fetch(
                    `${API_BASE}/api/students/${STUDENT_ID}/dashboard`
                );

            if (!dashboardResponse.ok) {
                throw new Error(
                    "Could not load student information."
                );
            }

            const dashboard =
                await dashboardResponse.json();

            const student =
                dashboard.student;

            const requestBody = {

                student_name:
                    student.name,

                grade:
                    student.grade,

                subject:
                    subject,

                topic:
                    topic,

                current_level:
                    student.current_level,

                language:
                    language || student.preferred_language,

                learning_goal:
                    student.learning_goals,

                available_time_minutes:
                    time
            };

            const response =
                await fetch(
                    `${API_BASE}/api/lesson/create`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body:
                            JSON.stringify(requestBody)
                    }
                );

            if (!response.ok) {

                let message =
                    `Lesson generation failed: ${response.status}`;

                try {

                    const errorData =
                        await response.json();

                    if (errorData.detail) {
                        message =
                            errorData.detail;
                    }

                } catch {
                    // Keep default message
                }

                throw new Error(message);
            }

            const lesson =
                await response.json();

            // Save current lesson
            currentLesson = {
                ...lesson,

                student: student
            };

            displayGeneratedLesson(
                currentLesson
            );

            // Refresh dashboard
            await loadDashboard();

        } catch (error) {

            console.error(
                "Lesson generation error:",
                error
            );

            showError(error.message);

        } finally {

            generateButton.disabled = false;

            generateButton.textContent =
                "✨ Generate Personalized Lesson";
        }
    }
);



// Display Generated Lesson


async function displayGeneratedLesson(lesson) {

    lessonTitle.textContent =
        lesson.title ||
        "Personalized Lesson";

    lessonMeta.textContent =
        `${lesson.subject || ""} • ` +
        `${lesson.topic || ""} • ` +
        `${lesson.difficulty || ""} • ` +
        `${lesson.total_duration_minutes || 0} minutes`;

    objectivesList.innerHTML = "";

    if (
        lesson.learning_objectives &&
        lesson.learning_objectives.length
    ) {

        lesson.learning_objectives.forEach(
            objective => {

                const li =
                    document.createElement("li");

                li.textContent =
                    objective;

                objectivesList.appendChild(li);
            }
        );

    } else {

        objectivesList.innerHTML =
            "<li>No objectives provided.</li>";
    }

    segmentsContainer.innerHTML = "";

    if (
        lesson.segments &&
        lesson.segments.length
    ) {

        lesson.segments.forEach(
            segment => {

                const card =
                    document.createElement("div");

                card.className =
                    "segment";

                card.innerHTML = `

                    <span class="segment-type">
                        ${escapeHTML(
                            segment.type ||
                            "Lesson"
                        )}
                    </span>

                    <h3>
                        ${escapeHTML(
                            segment.title ||
                            "Lesson Segment"
                        )}
                    </h3>

                    <p>
                        <strong>Concept:</strong>
                        ${escapeHTML(
                            segment.concept || "-"
                        )}
                    </p>

                    <p>
                        ${escapeHTML(
                            segment.explanation || ""
                        )}
                    </p>

                    <span class="duration">
                        ⏱
                        ${escapeHTML(
                            String(
                                segment.duration_minutes ?? 0
                            )
                        )}
                        minutes
                    </span>
                `;

                segmentsContainer.appendChild(card);
            }
        );

    } else {

        segmentsContainer.innerHTML =
            `<div class="empty">
                No lesson segments were returned.
            </div>`;
    }

    // Show generated lesson
    generatedLesson.classList.remove(
        "hidden"
    );

    // Trigger Teacher Agent
    const nextStep = await getTeacherNextStep(lesson.lesson_id);
    if (nextStep && nextStep.teacher_status === "WAITING_FOR_STUDENT") {
        qaSection.classList.remove("hidden");
        questionText.textContent = nextStep.content.explanation; // Assuming explanation is the question
    }

    // IMPORTANT:
    // Show media section after lesson generation
    mediaSection.classList.remove(
        "hidden"
    );

    mediaStatus.textContent =
        "Generate visual, speech and video for this lesson.";

    mediaSection.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}



// Generate AI Learning Media


generateMediaButton.addEventListener(
    "click",
    async function() {

        if (!currentLesson) {

            showError(
                "Please generate a lesson first."
            );

            return;
        }

        const student =
            currentLesson.student || {};

        const subject =
            currentLesson.subject ||
            document.getElementById("subject")
                .value
                .trim();

        const topic =
            currentLesson.topic ||
            document.getElementById("topic")
                .value
                .trim();

        const grade =
            student.grade ||
            "10";

        const language =
            student.preferred_language ||
            currentLesson.language ||
            "English";

        generateMediaButton.disabled =
            true;

        generateMediaButton.textContent =
            "Generating learning media...";

        hideError();

        visualContainer.classList.add(
            "hidden"
        );

        audioContainer.classList.add(
            "hidden"
        );

        videoContainer.classList.add(
            "hidden"
        );

        mediaStatus.textContent =
            "Generating educational visual...";

        try {

            
            // 1. Generate Visual
            

            const firstSegment =
                currentLesson.segments &&
                currentLesson.segments.length
                    ? currentLesson.segments[0]
                    : null;

            const concept =
                firstSegment?.concept ||
                `Main concept of ${topic}`;

            const visualResponse =
                await fetch(
                    `${API_BASE}/api/visuals/generate`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body:
                            JSON.stringify({

                                subject:
                                    subject,

                                topic:
                                    topic,

                                grade:
                                    grade,

                                concept:
                                    concept,

                                style:
                                    "educational diagram"
                            })
                    }
                );

            if (!visualResponse.ok) {

                const errorData =
                    await visualResponse.json();

                throw new Error(
                    errorData.detail ||
                    "Visual generation failed."
                );
            }

            const visualData =
                await visualResponse.json();

            const visualFile =
                visualData.output_file;

            if (!visualFile) {
                throw new Error(
                    "Visual generation returned no file."
                );
            }

            const visualFilename =
                getFilename(visualFile);

            generatedVisual.src =
                `${API_BASE}/media/${visualFilename}`;

            visualContainer.classList.remove(
                "hidden"
            );


            
            // 2. Generate Speech
            

            mediaStatus.textContent =
                `Generating AI teacher voice in ${language}...`;

            // Use actual lesson explanation
            const speechParts = [];

            speechParts.push(
                `Today we are learning about ${topic}.`
            );

            if (
                currentLesson.learning_objectives &&
                currentLesson.learning_objectives.length
            ) {

                speechParts.push(
                    `Our learning objectives are: ` +
                    currentLesson.learning_objectives.join(
                        ". "
                    )
                );
            }

            if (
                currentLesson.segments &&
                currentLesson.segments.length
            ) {

                currentLesson.segments.forEach(
                    segment => {

                        if (segment.title) {
                            speechParts.push(
                                segment.title
                            );
                        }

                        if (segment.explanation) {
                            speechParts.push(
                                segment.explanation
                            );
                        }
                    }
                );
            }

            const speechText =
                speechParts.join(" ");


            const speechResponse =
                await fetch(
                    `${API_BASE}/api/speech/tts`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body:
                            JSON.stringify({

                                text:
                                    speechText,

                                voice:
                                    "Kore"
                            })
                    }
                );

            if (!speechResponse.ok) {

                const errorData =
                    await speechResponse.json();

                throw new Error(
                    errorData.detail ||
                    "Speech generation failed."
                );
            }

            const speechData =
                await speechResponse.json();

            const audioFile =
                speechData.output_file;

            if (!audioFile) {
                throw new Error(
                    "Speech generation returned no file."
                );
            }

            const audioFilename =
                getFilename(audioFile);

            generatedAudio.src =
                `${API_BASE}/media/${audioFilename}`;

            generatedAudio.load();

            audioContainer.classList.remove(
                "hidden"
            );


            
            // 3. Generate Video
            

mediaStatus.textContent =
    "Creating AI animated lesson video...";

const animationResponse =
    await fetch(
        `${API_BASE}/api/video/generate-animation`,
        {
            method: "POST",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body:
                JSON.stringify({

                    subject:
                        subject,

                    topic:
                        topic,

                    grade:
                        grade,

                    concept:
                        concept
                })
        }
    );

if (!animationResponse.ok) {

    let errorMessage =
        "AI animation generation failed.";

    try {

        const errorData =
            await animationResponse.json();

        errorMessage =
            errorData.detail ||
            errorMessage;

    } catch (e) {

        console.error(
            "Could not read animation error:",
            e
        );
    }

    throw new Error(
        errorMessage
    );
}

const animationData =
    await animationResponse.json();

console.log(
    "AI animation response:",
    animationData
);

const videoUrl =
    animationData.video_url;

if (!videoUrl) {

    throw new Error(
        "AI animation returned no video URL."
    );
}

generatedVideo.src =
    videoUrl.startsWith("http")
        ? videoUrl
        : `${API_BASE}${videoUrl}`;

generatedVideo.load();

videoContainer.classList.remove(
    "hidden"
);

mediaStatus.textContent =
    "AI animated learning video generated successfully!";

mediaSection.scrollIntoView({
    behavior: "smooth",
    block: "start"
});

        } catch (error) {

            console.error(
                "Media generation error:",
                error
            );

            showError(
                error.message ||
                "AI learning media generation failed."
            );

            mediaStatus.textContent =
                "Media generation failed.";

        } finally {

            generateMediaButton.disabled =
                false;

            generateMediaButton.textContent =
                "✨ Generate Learning Media";
        }
    }
);


// Get Filename From Backend Path


function getFilename(filePath) {

    return String(filePath)
        .replace(/\\/g, "/")
        .split("/")
        .pop();
}



// Error Handling


function showError(message) {

    errorBox.textContent =
        message;

    errorBox.classList.remove(
        "hidden"
    );
}


function hideError() {

    errorBox.textContent =
        "";

    errorBox.classList.add(
        "hidden"
    );
}



// Security Helper


function escapeHTML(value) {

    const div =
        document.createElement("div");

    div.textContent =
        String(value ?? "");

    return div.innerHTML;
}

// Theme Toggle
const themeToggle = document.getElementById("theme-toggle");

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute("data-theme");
    const newTheme = currentTheme === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", newTheme);
    localStorage.setItem("theme", newTheme);
    themeToggle.textContent = newTheme === "dark" ? "☀️" : "🌙";
}

// Initialize Theme
const savedTheme = localStorage.getItem("theme") || "light";
document.documentElement.setAttribute("data-theme", savedTheme);
themeToggle.textContent = savedTheme === "dark" ? "☀️" : "🌙";

themeToggle.addEventListener("click", toggleTheme);

// Add Demo AI Teacher Button
function addDemoAITeacherButton() {
    const statusDiv = document.querySelector(".status");
    if (!statusDiv) return;

    const demoButton = document.createElement("button");
    demoButton.id = "ai-teacher-demo-button";
    demoButton.textContent = "Start Demo";
    demoButton.style.marginLeft = "10px";
    demoButton.onclick = () => {
        startLesson({
            id: "0d838683-d5e9-4603-9e0e-851b164af666",
            title: "Newton's Third Law of Motion",
            subject: "Physics",
            topic: "Newton's Third Law of Motion"
        });
    };
    statusDiv.insertBefore(demoButton, statusDiv.firstChild);
}

// Call button addition after page load
window.addEventListener('load', addDemoAITeacherButton);

// Start Application
async function startApp() {
    authSection.classList.add("hidden");
    await loadDashboard();
}
startApp();