document.addEventListener("DOMContentLoaded", () => {

    const openBtn = document.getElementById("aiChatOpen");
    const closeBtn = document.getElementById("aiChatClose");
    const box = document.getElementById("aiChatbot");
    const messages = document.getElementById("aiChatMessages");
    const input = document.getElementById("aiChatInput");
    const send = document.getElementById("aiChatSend");


    // ================================
    // OPEN CHATBOT
    // ================================

    openBtn?.addEventListener("click", () => {
        box?.classList.add("open");
        input?.focus();
    });


    // ================================
    // CLOSE CHATBOT
    // ================================

    closeBtn?.addEventListener("click", () => {
        box?.classList.remove("open");
    });


    // ================================
    // ADD MESSAGE
    // ================================

    function addMessage(text, user = false) {

        const row = document.createElement("div");

        row.className = `ai-message ${
            user ? "user-message" : "bot-message"
        }`;

        if (!user) {

            const avatar = document.createElement("div");

            avatar.className = "message-avatar";
            avatar.textContent = "🤖";

            row.appendChild(avatar);
        }

        const messageText = document.createElement("div");

        messageText.className = "message-text";

        messageText.textContent = text;

        row.appendChild(messageText);

        messages.appendChild(row);

        messages.scrollTop = messages.scrollHeight;
    }


    // ================================
    // GET FITNESS PLAN CONTEXT
    // ================================

    function getContext() {

        try {

            const data =
                sessionStorage.getItem("dietResult");

            if (!data) {
                return {};
            }

            const result = JSON.parse(data);

            return {
                metrics: result.metrics || {},
                diet_type: result.diet_type || "",
                disease: result.disease || "",
                workout_experience:
                    result.workout_experience || "",
                workout_location:
                    result.workout_location || "",

                diet_plan:
                    result.diet_plan || {},

                workout_plan:
                    result.workout_plan || {}
            };

        } catch (error) {

            console.error(
                "Context error:",
                error
            );

            return {};
        }
    }


    // ================================
    // SEND MESSAGE
    // ================================

    async function sendMessage(text = null) {
    const message = text || input.value.trim();

    if (!message) return;

    // Show user message
    addMessage(message, "user");

    input.value = "";
    send.disabled = true;

    // Show thinking message
    addMessage("Thinking...", "bot");

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            credentials: "same-origin",
            body: JSON.stringify({
                message: message,
                context: getContext()
            })
        });

        console.log("Chat status:", response.status);

        // Read response as TEXT first
        const rawResponse = await response.text();

        console.log("Raw chatbot response:", rawResponse);

        // Remove Thinking...
        const thinkingMessages =
            messages.querySelectorAll(".bot-message");

        if (thinkingMessages.length > 0) {
            const lastThinking =
                thinkingMessages[thinkingMessages.length - 1];

            if (lastThinking.textContent.includes("Thinking...")) {
                lastThinking.remove();
            }
        }

        if (!rawResponse.trim()) {
            throw new Error("Server returned a blank response.");
        }

        // Convert text to JSON
        const data = JSON.parse(rawResponse);

        console.log("Chat JSON:", data);

        if (!response.ok) {
            throw new Error(data.error || "Server error");
        }

        if (!data.success) {
            throw new Error(data.error || "AI response failed");
        }

        if (!data.reply || !data.reply.trim()) {
            throw new Error("AI returned an empty reply.");
        }

        // SHOW AI RESPONSE
        addMessage(data.reply, "bot");

    } catch (error) {

        console.error("CHATBOT ERROR:", error);

        addMessage(
            "⚠️ " + error.message,
            "bot"
        );

    } finally {
        send.disabled = false;
        input.focus();
    }
}


    // ================================
    // QUICK QUESTIONS
    // ================================

    document
        .querySelectorAll(".quick-question")
        .forEach(button => {

            button.addEventListener(
                "click",
                () => {

                    sendMessage(
                        button.textContent.trim()
                    );

                }
            );

        });
        
    // ================================
    // QUICK QUESTIONS
    // ================================

    document
        .querySelectorAll(".quick-question")
        .forEach(button => {

            button.addEventListener(
                "click",
                () => {

                    sendMessage(
                        button.textContent.trim()
                    );

                }
            );

        });


    // ================================
    // SEND BUTTON
    // ================================

    send?.addEventListener("click", () => {

        sendMessage();

    });


    // ================================
    // ENTER KEY
    // ================================

    input?.addEventListener("keydown", (e) => {

        if (e.key === "Enter" && !e.shiftKey) {

            e.preventDefault();

            sendMessage();

        }

    });

});
    