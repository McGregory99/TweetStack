// Utilities
const API_BASE = "/api";

// Helper functions
function showMessage(message, type = "info") {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message message-${type}`;
    messageDiv.textContent = message;

    // Simple notification system
    document.body.appendChild(messageDiv);
    setTimeout(() => {
        document.body.removeChild(messageDiv);
    }, 3000);
}

function formatDate(dateString) {
    if (!dateString) return "Sin fecha";
    const date = new Date(dateString);
    return date.toLocaleDateString("es-ES", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
}

// API functions
async function apiRequest(url, options = {}) {
    const response = await fetch(API_BASE + url, {
        headers: {
            "Content-Type": "application/json",
            ...options.headers,
        },
        ...options,
    });

    if (!response.ok) {
        const error = await response
            .json()
            .catch(() => ({ detail: "Error desconocido" }));
        throw new Error(error.detail || "Error en la solicitud");
    }

    return response.json();
}

// Tweet functions
async function createTweet(tweetData) {
    return apiRequest("/tweets", {
        method: "POST",
        body: JSON.stringify(tweetData),
    });
}

async function updateTweet(tweetId, tweetData) {
    return apiRequest(`/tweets/${tweetId}`, {
        method: "PUT",
        body: JSON.stringify(tweetData),
    });
}

async function deleteTweet(tweetId) {
    return apiRequest(`/tweets/${tweetId}`, {
        method: "DELETE",
    });
}

// Collection functions
async function createCollection(collectionData) {
    return apiRequest("/collections", {
        method: "POST",
        body: JSON.stringify(collectionData),
    });
}

async function deleteCollection(collectionId) {
    return apiRequest(`/collections/${collectionId}`, {
        method: "DELETE",
    });
}

// Modal functions
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove("hidden");
        document.body.style.overflow = "hidden";
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add("hidden");
        document.body.style.overflow = "";
    }
}

// Tweet Editor functionality
class TweetEditor {
    constructor() {
        this.isThread = false;
        this.threadTweets = [{ content: "", media_path: "", media_type: "" }];
        this.selectedCollections = [];
        this.scheduledDate = "";

        // Initialize with existing content if any
        const singleTweetContent = document.getElementById("content");
        if (singleTweetContent && singleTweetContent.value.trim()) {
            this.threadTweets[0].content = singleTweetContent.value;
        }

        this.initEventListeners();
    }

    initEventListeners() {
        // Thread toggle
        const threadToggle = document.getElementById("threadToggle");
        if (threadToggle) {
            threadToggle.addEventListener("change", (e) => {
                this.toggleThread(e.target.checked);
            });
        }

        // Single tweet content textarea
        const singleTweetContent = document.getElementById("content");
        if (singleTweetContent) {
            singleTweetContent.addEventListener("input", (e) => {
                // Update threadTweets[0].content when typing in single tweet mode
                if (!this.isThread && this.threadTweets[0]) {
                    this.threadTweets[0].content = e.target.value;
                }
            });
        }

        // Add thread tweet button
        const addThreadBtn = document.getElementById("addThreadTweet");
        if (addThreadBtn) {
            addThreadBtn.addEventListener("click", () => {
                this.addThreadTweet();
            });
        }

        // Save tweet button
        const saveTweetBtn = document.getElementById("saveTweet");
        if (saveTweetBtn) {
            saveTweetBtn.addEventListener("click", () => {
                this.saveTweet();
            });
        }
    }

    toggleThread(isThread) {
        const singleTweetContainer = document.getElementById(
            "singleTweetContainer"
        );
        const singleTweetContent = document.getElementById("content");

        // Synchronize content when switching modes
        if (!isThread && singleTweetContent) {
            // Switching to single tweet mode - sync from threadTweets[0] to textarea
            if (this.threadTweets[0]) {
                singleTweetContent.value = this.threadTweets[0].content || "";
            }
        } else if (isThread && singleTweetContent) {
            // Switching to thread mode - sync from textarea to threadTweets[0]
            if (this.threadTweets[0]) {
                this.threadTweets[0].content = singleTweetContent.value || "";
            }
        }

        if (singleTweetContainer) {
            singleTweetContainer.style.display = isThread ? "none" : "block";
        }

        this.isThread = isThread;
        const threadContainer = document.getElementById("threadContainer");
        const addThreadBtn = document.getElementById("addThreadTweet");

        if (threadContainer) {
            threadContainer.style.display = isThread ? "block" : "none";
        }
        if (addThreadBtn) {
            addThreadBtn.style.display = isThread ? "block" : "none";
        }

        if (!isThread && this.threadTweets.length > 1) {
            this.threadTweets = [this.threadTweets[0]];
        }

        if (isThread) {
            this.renderThreadTweets();
        }
    }

    addThreadTweet() {
        this.threadTweets.push({ content: "", media_path: "", media_type: "" });
        this.renderThreadTweets();
    }

    removeThreadTweet(index) {
        if (this.threadTweets.length > 1) {
            this.threadTweets.splice(index, 1);
            this.renderThreadTweets();
        }
    }

    renderThreadTweets() {
        const container = document.getElementById("threadTweetsContainer");
        if (!container) return;

        container.innerHTML = "";

        this.threadTweets.forEach((tweet, index) => {
            const tweetDiv = document.createElement("div");
            tweetDiv.className = "card mb-4";
            tweetDiv.innerHTML = `
                <div class="card-content">
                    <div class="flex justify-between items-center mb-2">
                        <label class="label">Tweet ${index + 1}</label>
                        ${
                            this.threadTweets.length > 1
                                ? `
                            <button type="button" class="btn btn-danger btn-sm" onclick="tweetEditor.removeThreadTweet(${index})">
                                Eliminar
                            </button>
                        `
                                : ""
                        }
                    </div>
                    <textarea 
                        class="textarea" 
                        placeholder="¿Qué está pasando?"
                        maxlength="280"
                        onchange="tweetEditor.updateThreadTweet(${index}, 'content', this.value)"
                    >${tweet.content}</textarea>
                    <div class="text-xs text-gray-500 text-right mt-1">
                        ${tweet.content.length}/280
                    </div>
                </div>
            `;
            container.appendChild(tweetDiv);
        });
    }

    updateThreadTweet(index, field, value) {
        if (this.threadTweets[index]) {
            this.threadTweets[index][field] = value;
        }
    }

    collectFormData() {
        const form = document.getElementById("tweetForm");
        if (!form) return null;

        const formData = new FormData(form);
        const collections = Array.from(
            form.querySelectorAll('input[name="collections"]:checked')
        ).map((cb) => parseInt(cb.value));

        return {
            user_id: "demo-user-123",
            content: this.isThread ? "" : this.threadTweets[0].content,
            media_path: this.isThread
                ? ""
                : this.threadTweets[0].media_path || "",
            media_type: this.isThread
                ? ""
                : this.threadTweets[0].media_type || "",
            is_thread: this.isThread,
            thread_tweets: this.isThread ? this.threadTweets : [],
            collection_ids: collections,
            scheduled_date: formData.get("scheduled_date") || null,
        };
    }

    async saveTweet() {
        try {
            const tweetData = this.collectFormData();
            if (!tweetData) return;

            // Validate content
            if (this.isThread) {
                const hasContent = this.threadTweets.some(
                    (t) => t.content.trim().length > 0
                );
                if (!hasContent) {
                    showMessage(
                        "Debes escribir al menos un tweet en el hilo",
                        "error"
                    );
                    return;
                }
            } else {
                if (!this.threadTweets[0].content.trim()) {
                    showMessage("Debes escribir algo en el tweet", "error");
                    return;
                }
            }

            await createTweet(tweetData);
            showMessage("Tweet guardado exitosamente", "success");

            // Redirect to home
            setTimeout(() => {
                window.location.href = "/";
            }, 1000);
        } catch (error) {
            showMessage("Error al guardar el tweet: " + error.message, "error");
        }
    }
}

// Collection Manager
class CollectionManager {
    async createCollection() {
        const name = document.getElementById("collectionName")?.value;
        const description =
            document.getElementById("collectionDescription")?.value || "";

        if (!name || !name.trim()) {
            showMessage("El nombre de la colección es obligatorio", "error");
            return;
        }

        try {
            await createCollection({
                name: name.trim(),
                description: description.trim(),
                user_id: "demo-user-123",
            });

            showMessage("Colección creada exitosamente", "success");
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } catch (error) {
            showMessage(
                "Error al crear la colección: " + error.message,
                "error"
            );
        }
    }

    async deleteCollection(collectionId, collectionName) {
        if (
            !confirm(
                `¿Estás seguro de que quieres eliminar la colección "${collectionName}"?`
            )
        ) {
            return;
        }

        try {
            await deleteCollection(collectionId);
            showMessage("Colección eliminada exitosamente", "success");
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } catch (error) {
            showMessage(
                "Error al eliminar la colección: " + error.message,
                "error"
            );
        }
    }
}

// Tweet Actions
async function deleteTweetAction(tweetId) {
    if (!confirm("¿Estás seguro de que quieres eliminar este tweet?")) {
        return;
    }

    try {
        await deleteTweet(tweetId);
        showMessage("Tweet eliminado exitosamente", "success");
        setTimeout(() => {
            window.location.reload();
        }, 1000);
    } catch (error) {
        showMessage("Error al eliminar el tweet: " + error.message, "error");
    }
}

// Initialize components when DOM is loaded
document.addEventListener("DOMContentLoaded", function () {
    // Initialize tweet editor if we're on the editor page
    if (document.getElementById("tweetForm")) {
        window.tweetEditor = new TweetEditor();
    }

    // Initialize collection manager if we're on the collections page
    if (document.querySelector(".collections-page")) {
        window.collectionManager = new CollectionManager();
    }

    // Close modal when clicking outside
    document.addEventListener("click", function (e) {
        if (e.target.classList.contains("modal")) {
            const modalId = e.target.id;
            closeModal(modalId);
        }
    });

    // Close modal with Escape key
    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") {
            const openModal = document.querySelector(".modal:not(.hidden)");
            if (openModal) {
                closeModal(openModal.id);
            }
        }
    });
});

// Export functions for global use
window.openModal = openModal;
window.closeModal = closeModal;
window.deleteTweetAction = deleteTweetAction;
