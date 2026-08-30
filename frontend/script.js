const API_BASE = "http://127.0.0.1:8000";

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


// Store the latest generated lesson
let currentLesson = null;



// Load Dashboard


async function loadDashboard() {

    try {

        hideError();

        const response = await fetch(
            `${API_BASE}/api/students/${STUDENT_ID}/dashboard`
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

        const card =
            document.createElement("div");

        card.className =
            "lesson-card";

        card.innerHTML = `
            <h3>
                ${escapeHTML(
                    lesson.title ||
                    "Untitled Lesson"
                )}
            </h3>

            <div class="lesson-info">

                <span>
                    Subject:
                    ${escapeHTML(
                        lesson.subject || "-"
                    )}
                </span>

                <span>
                    Topic:
                    ${escapeHTML(
                        lesson.topic || "-"
                    )}
                </span>

                <span>
                    Difficulty:
                    ${escapeHTML(
                        lesson.difficulty || "-"
                    )}
                </span>

                <span>
                    Duration:
                    ${escapeHTML(
                        String(
                            lesson.total_duration_minutes ?? "-"
                        )
                    )} min
                </span>

            </div>
        `;

        lessonsContainer.appendChild(card);
    });

    lessonsSection.classList.remove("hidden");
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
                    student.preferred_language,

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


function displayGeneratedLesson(lesson) {

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
                "Creating personalized lesson video...";

            const videoResponse =
                await fetch(
                    `${API_BASE}/api/video/generate`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body:
                            JSON.stringify({

                                visual_file:
                                    visualFile,

                                audio_file:
                                    audioFile,

                                duration_seconds:
                                    300
                            })
                    }
                );

            if (!videoResponse.ok) {

                const errorData =
                    await videoResponse.json();

                throw new Error(
                    errorData.detail ||
                    "Video generation failed."
                );
            }

            const videoData =
                await videoResponse.json();

            const videoFile =
                videoData.output_file;

            if (!videoFile) {
                throw new Error(
                    "Video generation returned no file."
                );
            }

            const videoFilename =
                getFilename(videoFile);

            generatedVideo.src =
                `${API_BASE}/media/${videoFilename}`;

            generatedVideo.load();

            videoContainer.classList.remove(
                "hidden"
            );

            mediaStatus.textContent =
                "AI learning media generated successfully!";

            mediaSection.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });

        } catch (error) {

            console.error(
                "Media generation error:",
                error
            );

            mediaStatus.textContent =
                "Media generation failed.";

            showError(
                error.message
            );

        } finally {

            generateMediaButton.disabled =
                false;

            generateMediaButton.textContent =
                "🎬 Generate Learning Video";
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



// Start Application


loadDashboard();